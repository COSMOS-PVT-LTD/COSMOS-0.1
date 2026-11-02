"""Project-owned retention around existing fixed-fixture science and workers."""
from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from plugins.geometry.protocol import checked_file
from systems.contracts.geometry import (
    BuildState,
    DesignSnapshot,
    GeometryBuildEvent,
    GeometryBuildRequest,
    GeometryFeatureGraph,
)
from systems.geometry.qa import FixtureReference
from systems.geometry.service import GeometryBuildService, VerifiedCandidate
from systems.geometry.workbench import GeometryWorkbench, Revision
from systems.persistence.job_repository import (
    TERMINAL,
    BlobAttachment,
    DurableJob,
    JobRepository,
    JobState,
)
from systems.persistence.project_repository import ProjectRepository, RecordPayload
from systems.projects.authority import (
    Head,
    InvalidRecord,
    Principal,
    SavedSnapshot,
    SchemaMismatch,
    StoreUnavailable,
)

DOMAIN = "geometry-fixture"
SCHEMA = "cosmos.geometry-fixture-input.v1"


def source_payload(revision: Revision) -> RecordPayload:
    # Preserve each domain's exact canonical JSON text and frozen source namespace.
    return RecordPayload(json.dumps({"settings": revision.settings, "snapshot_json": revision.snapshot.to_json(),
        "graph_json": revision.graph.to_json(), "request_json": revision.request.to_json()},
        sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), SCHEMA, revision.snapshot.project_id)


def decode_source(saved: SavedSnapshot) -> Revision:
    if saved.domain != DOMAIN or saved.schema_id != SCHEMA or saved.source_namespace != "p07-software-fixtures":
        raise InvalidRecord("Exact supported software-fixture source is required.")
    value = json.loads(saved.payload)
    revision = Revision(value["settings"], DesignSnapshot.from_json(value["snapshot_json"]),
                        GeometryFeatureGraph.from_json(value["graph_json"]), GeometryBuildRequest.from_json(value["request_json"]))
    revision.graph.validate_snapshot(revision.snapshot)
    if revision.request.snapshot_id != revision.snapshot.snapshot_id or revision.request.feature_graph_sha256 != revision.graph.content_sha256:
        raise InvalidRecord("Retained geometry request/source binding is inconsistent.")
    return revision


@dataclass
class LiveAttempt:
    cancelled: threading.Event = field(default_factory=threading.Event)
    native_id: str | None = None
    service: GeometryBuildService | None = None


class ManagedGeometry:
    """Application coordinator only. Native worker processes never access IO authority."""

    def decode(self, source: SavedSnapshot) -> Revision:
        return decode_source(source)

    def select_service(self, revision: Revision) -> GeometryBuildService:
        return self.services()[revision.request.backend_id]

    def reference(self, revision: Revision):
        return FixtureReference(revision.settings["operation"])

    def selection_allowed(self, actor: Principal, job: DurableJob) -> bool:
        return True  # Existing durable SQL guards still enforce actual source/currentness/membership.

    def __init__(self, repository: ProjectRepository, jobs: JobRepository,
                 services: Callable[[], dict[str, GeometryBuildService]], resolve_actor: Callable[[str], Principal]) -> None:
        self.repository, self.jobs, self.services, self.resolve_actor = repository, jobs, services, resolve_actor
        self.lock = threading.RLock()
        self.closed = threading.Event()
        self.live: dict[str, LiveAttempt] = {}
        self.pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="managed-geometry-coordinator")

    def save(self, actor: Principal, project_id: str, object_id: str, *, settings: dict[str, Any],
             expected: Head, operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        revision = GeometryWorkbench.revision(settings)  # Existing whitelist/contracts; no new geometry algorithm.
        prior = None if expected == Head.absent() else self.repository.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id)
        return self.repository.save_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id,
            input_revision=0 if prior is None else prior.input_revision + 1, payload=source_payload(revision), expected=expected,
            operation_id=operation_id, command_hash=command_hash, purpose="create" if prior is None else "save")

    def start(self, actor: Principal, source: SavedSnapshot, *, operation_id: str, request_hash: str,
              retry_of: str | None = None) -> DurableJob:
        replay = self.jobs.resolve_command(actor, source.project_id, operation_id=operation_id, request_hash=request_hash)
        if replay is not None:
            return replay
        if not self.jobs.supports_stages:
            raise SchemaMismatch("New native attempts require schema4 incremental stages; existing stores were not upgraded.")
        revision = self.decode(source)
        service = self.select_service(revision)  # Explicit hash-qualified runtime policy before admission.
        with self.lock:
            if self.closed.is_set():
                raise StoreUnavailable("Managed geometry coordinator is closed.")
            receipt = self.jobs.admit(actor, source, operation_id=operation_id, request_hash=request_hash, retry_of=retry_of)
            current = self.jobs.get(actor, source.project_id, receipt.job_id)
            if current.state not in TERMINAL and current.job_id not in self.live:
                live = LiveAttempt()
                self.live[current.job_id] = live
                self.pool.submit(self._run, current, revision, service, live)
            return receipt

    @staticmethod
    def collect(candidate: VerifiedCandidate) -> tuple[BlobAttachment, ...]:
        items: dict[str, BlobAttachment] = {}

        def retain(name: str, digest: str, kind: str) -> None:
            path = checked_file(candidate.directory, name, digest)
            data = path.read_bytes()
            if sha256(data).hexdigest() != digest:
                raise InvalidRecord("Candidate changed during exact-byte retention.")
            items[name] = BlobAttachment(name, data, digest, kind)

        for artifact in candidate.record.artifacts:
            retain(artifact.storage_uri.split("/")[-1], artifact.sha256, "artifact")
            source_name = "source.brep" if artifact.backend_id == "occt" else "source.vdb"
            retain(source_name, artifact.source_artifact_sha256, "source")
        return tuple(items.values())

    def _run(self, job: DurableJob, revision: Revision, service: GeometryBuildService, live: LiveAttempt) -> None:
        try:
            if self.closed.is_set():
                self.jobs.advance(job.job_id, JobState.INTERRUPTED, RecordPayload.from_mapping({"code": "COORDINATOR_SHUTDOWN"}, "cosmos.geometry-attempt.v1"))
                return
            started = self.jobs.advance(job.job_id, JobState.RUNNING,
                RecordPayload.from_mapping({"code": "EXISTING_BUILDER_STARTING"}, "cosmos.geometry-attempt.v1"))
            if started.state is JobState.CANCELLED:
                return
            def retain_stage(event: GeometryBuildEvent) -> None:
                self.jobs.append_stage(job.job_id, RecordPayload(event.to_json().encode(),
                    "cosmos.geometry-stage.v1", revision.snapshot.project_id))
            native_id, future = service.submit(revision.request, revision.snapshot, revision.graph,
                self.reference(revision), conditioning_profile="exact_zero_faces_v1" if revision.request.backend_id == "picogk" else "raw",
                event_sink=retain_stage)
            with self.lock:
                live.native_id, live.service = native_id, service
                if live.cancelled.is_set() or self.closed.is_set():
                    service.cancel(native_id)
            candidate = future.result()
            if candidate.record.snapshot != revision.snapshot or candidate.record.feature_graph != revision.graph or candidate.record.request != revision.request:
                raise InvalidRecord("Builder returned a candidate for a different exact retained input.")
            actor = self.resolve_actor(job.creator_user_id)
            self.jobs.verify_stages(job.job_id, tuple(event.to_json().encode() for event in candidate.record.events))
            payload = RecordPayload(json.dumps({"record_json": candidate.record.to_json(), "evidence_json": candidate.evidence_json},
                sort_keys=True, separators=(",", ":"), allow_nan=False).encode(), "cosmos.geometry-attempt.v1", revision.snapshot.project_id)
            if self.closed.is_set():
                self.jobs.advance(job.job_id, JobState.INTERRUPTED, payload)
            else:
                accepted = candidate.record.state is BuildState.ACCEPTED
                blobs = self.collect(candidate) if accepted else ()
                self.jobs.advance(job.job_id, JobState.COMPLETED if accepted else JobState.FAILED, payload,
                                  attachments=blobs, actor=actor, selection_allowed=self.selection_allowed(actor, job))
        except Exception as error:
            logging.getLogger(__name__).exception("Managed geometry attempt failed; retaining failure when storage permits")
            # If retention itself is unavailable, leave nonterminal state for the
            # next lease owner's explicit INTERRUPTED recovery, never invent success.
            try:
                self.jobs.advance(job.job_id, JobState.FAILED, RecordPayload.from_mapping(
                    {"code": getattr(error, "code", type(error).__name__), "message": str(error)[:1024]}, "cosmos.geometry-attempt.v1"))
            except Exception:
                logging.getLogger(__name__).exception("Durable geometry terminal retention failed; restart recovery required")
        finally:
            with self.lock:
                self.live.pop(job.job_id, None)

    def cancel(self, actor: Principal, project_id: str, job_id: str, *, expected: Head,
               operation_id: str, request_hash: str) -> DurableJob:
        receipt = self.jobs.cancel(actor, project_id, job_id, expected=expected, operation_id=operation_id, request_hash=request_hash)
        with self.lock:
            live = self.live.get(job_id)
            if live is not None:
                live.cancelled.set()
                if live.service is not None and live.native_id is not None:
                    live.service.cancel(live.native_id)
        return receipt

    def close(self) -> None:
        self.closed.set()
        with self.lock:
            for live in self.live.values():
                if live.service is not None and live.native_id is not None:
                    live.service.cancel(live.native_id)
        self.pool.shutdown(wait=True)
