"""Project-owned adapters for the existing spherical software benchmark only."""
from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from numerics.finite_volume.radial_diffusion import DiffusionCancelled
from simulation.contracts import StudySettings, StudySnapshot
from simulation.workbench import SimulationWorkbench, mesh
from systems.contracts.geometry._wire import digest, dumps, require
from systems.geometry.retained_source import RetainedFixture, retained_fixture
from systems.geometry.source_contract import GeometrySource
from systems.persistence.job_repository import (
    TERMINAL,
    BlobAttachment,
    DurableJob,
    JobRepository,
    JobState,
)
from systems.persistence.project_repository import (
    Dependency,
    ProjectRepository,
    RecordPayload,
)
from systems.projects.authority import (
    Head,
    InvalidRecord,
    Principal,
    SavedSnapshot,
    SchemaMismatch,
    StoreUnavailable,
)

DOMAIN = "simulation-benchmark"
SCHEMA = "cosmos.simulation-study-input.v1"
SETTINGS = frozenset({"conductivity_w_m_k", "generation_w_m3", "surface_k", "cells", "relative_residual", "max_iterations"})


@dataclass(frozen=True)
class SavedStudy:
    study: StudySnapshot
    mesh_json: str
    geometry_commit_id: str
    geometry_job_id: str

    @property
    def dependency(self) -> Dependency:
        return Dependency("geometry", self.geometry_commit_id, self.geometry_job_id)


def decode_study(source: SavedSnapshot) -> SavedStudy:
    if source.domain != DOMAIN or source.schema_id != SCHEMA or source.source_namespace != "p07-software-fixtures":
        raise InvalidRecord("Exact supported spherical benchmark study source required.")
    value = json.loads(source.payload)
    if set(value) != {"study_json", "mesh_json", "geometry_commit_id", "geometry_job_id"}:
        raise InvalidRecord("Unexpected retained study fields.")
    study = StudySnapshot.from_json(value["study_json"])
    grid = json.loads(value["mesh_json"])
    content = {key: item for key, item in grid.items() if key != "mesh_sha256"}
    require(grid["mesh_sha256"] == digest(content) and grid["handoff_sha256"] == study.handoff.content_sha256
            and grid["geometry_sha256"] == study.handoff.artifact.sha256 and grid["cells"] == study.settings.cells,
            "MESH_PROVENANCE", "Retained mesh must match its immutable study/handoff and exact mesh checksum")
    return SavedStudy(study, value["mesh_json"], value["geometry_commit_id"], value["geometry_job_id"])


def study_payload(saved: SavedStudy) -> RecordPayload:
    return RecordPayload.from_mapping({"study_json": saved.study.to_json(), "mesh_json": saved.mesh_json,
        "geometry_commit_id": saved.geometry_commit_id, "geometry_job_id": saved.geometry_job_id}, SCHEMA,
        source_namespace="p07-software-fixtures")


def settings(value: dict[str, Any]) -> StudySettings:
    require(type(value) is dict and set(value) == SETTINGS, "INVALID_SETTINGS", "Provide every explicit SI material, boundary, mesh and solver setting")
    return StudySettings(**value)


@dataclass
class LiveStudy:
    cancelled: threading.Event = field(default_factory=threading.Event)
    worker: SimulationWorkbench | None = None
    native_id: str | None = None


class ManagedStudies:
    def __init__(self, repository: ProjectRepository, jobs: JobRepository,
                 materialize: Callable[[RetainedFixture], AbstractContextManager[GeometrySource]],
                 resolve_actor: Callable[[str], Principal]) -> None:
        self.repository, self.jobs, self.materialize, self.resolve_actor = repository, jobs, materialize, resolve_actor
        self.lock = threading.RLock()
        self.closed = threading.Event()
        self.live: dict[str, LiveStudy] = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="managed-study-coordinator")

    def _schema(self) -> None:
        if not self.repository.supports_dependencies or not self.jobs.supports_monitors:
            raise SchemaMismatch("Managed study/run lineage requires schema5; no existing storage was upgraded.")

    def save(self, actor: Principal, project_id: str, object_id: str, *, values: dict[str, Any], expected: Head,
             operation_id: str, command_hash: str, geometry_job_id: str | None = None) -> SavedSnapshot:
        self._schema()
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        parsed = settings(values)
        if expected == Head.absent():
            require(geometry_job_id is not None, "GEOMETRY_REQUIRED", "Choose an exact owned/current OCCT sphere build")
            assert geometry_job_id is not None
            fixture = retained_fixture(self.repository, self.jobs, actor, project_id, geometry_job_id)
            worker = SimulationWorkbench()
            try:
                with self.materialize(fixture) as geometry:
                    context = worker.attach(actor.user_id, geometry, fixture.job_id, fixture.revision.snapshot.snapshot_id)
                    base = StudySnapshot.from_json(dumps(context["study"]))
            finally:
                worker.close()
            study = StudySnapshot(base.handoff, parsed, base.model, base.solver_sha256, base.model_sha256)
            captured = SavedStudy(study, dumps(mesh(study)), fixture.commit_id, fixture.job_id)
            revision = 0
        else:
            prior = self.repository.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id)
            saved = decode_study(prior)
            if geometry_job_id is not None:
                raise InvalidRecord("Editing settings cannot silently rebind geometry; create a new study explicitly.")
            study = StudySnapshot(saved.study.handoff, parsed, saved.study.model, saved.study.solver_sha256, saved.study.model_sha256)
            captured = SavedStudy(study, dumps(mesh(study)), saved.geometry_commit_id, saved.geometry_job_id)
            revision = prior.input_revision + 1
        return self.repository.save_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id, input_revision=revision,
            payload=study_payload(captured), expected=expected, operation_id=operation_id, command_hash=command_hash,
            purpose="create" if revision == 0 else "save", dependencies=(captured.dependency,))

    def start(self, actor: Principal, source: SavedSnapshot, *, operation_id: str, request_hash: str, retry_of: str | None = None) -> DurableJob:
        self._schema()
        replay = self.jobs.resolve_command(actor, source.project_id, operation_id=operation_id, request_hash=request_hash)
        if replay is not None:
            return replay
        captured = decode_study(source)
        if self.repository.dependencies(actor, source.project_id, source.commit_id) != (captured.dependency,):
            raise InvalidRecord("Study dependency index differs from its original source.")
        current_methods = StudySnapshot(captured.study.handoff, captured.study.settings)
        require(current_methods.to_json() == captured.study.to_json(), "SOURCE_CHANGED", "Saved model/solver hashes changed; preserve history and create a new study")
        with self.lock:
            if self.closed.is_set():
                raise StoreUnavailable("Managed study coordinator is closed.")
            receipt = self.jobs.admit(actor, source, operation_id=operation_id, request_hash=request_hash, retry_of=retry_of)
            job = self.jobs.get(actor, source.project_id, receipt.job_id)
            if job.state not in TERMINAL and job.job_id not in self.live:
                live = LiveStudy()
                self.live[job.job_id] = live
                self.pool.submit(self._run, actor, job, captured, live)
            return receipt

    def _run(self, actor: Principal, job: DurableJob, captured: SavedStudy, live: LiveStudy) -> None:
        worker: SimulationWorkbench | None = None
        try:
            if self.closed.is_set():
                self.jobs.advance(job.job_id, JobState.INTERRUPTED, RecordPayload.from_mapping({"code": "COORDINATOR_SHUTDOWN"}, "cosmos.simulation-attempt.v1"))
                return
            started = self.jobs.advance(job.job_id, JobState.RUNNING, RecordPayload.from_mapping({"code": "EXISTING_BENCHMARK_STARTING"}, "cosmos.simulation-attempt.v1"))
            if started.state is JobState.CANCELLED:
                return
            fixture = retained_fixture(self.repository, self.jobs, actor, job.project_id, captured.geometry_job_id)
            require(fixture.commit_id == captured.geometry_commit_id, "STALE_GEOMETRY", "Do not substitute newer native inputs")
            def monitor(original: dict[str, Any]) -> None:
                self.jobs.append_monitor(job.job_id, RecordPayload(dumps(original).encode(), "cosmos.simulation-monitor.v1", "p07-software-fixtures"))
                if live.cancelled.is_set() or self.closed.is_set():
                    raise DiffusionCancelled("Cancellation requested by the durable coordinator")
            worker = SimulationWorkbench(monitor_sink=monitor)
            with self.materialize(fixture) as geometry:
                context = worker.attach(actor.user_id, geometry, fixture.job_id, fixture.revision.snapshot.snapshot_id)
                # Use only settings fields, not WireContract metadata, at the existing strict change boundary.
                values = {name: getattr(captured.study.settings, name) for name in SETTINGS}
                context = worker.change(actor.user_id, context["study_id"], values)
                require(StudySnapshot.from_json(dumps(context["study"])).to_json() == captured.study.to_json()
                        and dumps(context["mesh"]) == captured.mesh_json, "PROVENANCE_MISMATCH", "Rehydration must preserve original study/mesh/model/solver bytes")
                submitted = worker.submit(actor.user_id, geometry, captured.study.content_sha256)
                native_id = submitted["run_id"]
                with self.lock:
                    live.worker, live.native_id = worker, native_id
                    if live.cancelled.is_set() or self.closed.is_set():
                        worker.cancel(actor.user_id, native_id)
                run = worker.owned(actor.user_id, native_id)
                assert run.future is not None
                run.future.result()
                status = worker.status(actor.user_id, geometry, native_id)
                self.jobs.verify_monitors(job.job_id, tuple(dumps(value).encode() for value in run.events))
                payload = RecordPayload.from_mapping({"native_run_id": native_id, "worker_status_json": dumps(status),
                    "status_scope": "captured-worker-inputs; durable dependency applicability is separate"}, "cosmos.simulation-attempt.v1",
                    source_namespace="p07-software-fixtures")
                if self.closed.is_set():
                    self.jobs.advance(job.job_id, JobState.INTERRUPTED, payload)
                else:
                    completed = run.state == "completed"
                    blobs: tuple[BlobAttachment, ...] = ()
                    if completed:
                        worker.dataset(actor.user_id, native_id)  # Existing checksum/size gate.
                        assert run.dataset is not None
                        blobs = (BlobAttachment("dataset.json", run.dataset, sha256(run.dataset).hexdigest(), "artifact"),)
                    self.jobs.advance(job.job_id, JobState.COMPLETED if completed else JobState.FAILED, payload,
                        attachments=blobs, actor=self.resolve_actor(job.creator_user_id),
                        selection_allowed=StudySnapshot(captured.study.handoff, captured.study.settings).to_json() == captured.study.to_json())
        except Exception as error:
            logging.getLogger(__name__).exception("Managed study failed; retain failure when storage permits")
            try:
                self.jobs.advance(job.job_id, JobState.FAILED, RecordPayload.from_mapping(
                    {"code": getattr(error, "code", type(error).__name__), "message": str(error)[:1024]}, "cosmos.simulation-attempt.v1"))
            except Exception:
                logging.getLogger(__name__).exception("Study terminal retention unavailable; restart recovery required")
        finally:
            if worker is not None:
                worker.close()
            with self.lock:
                self.live.pop(job.job_id, None)

    def cancel(self, actor: Principal, project_id: str, job_id: str, *, expected: Head, operation_id: str, request_hash: str) -> DurableJob:
        receipt = self.jobs.cancel(actor, project_id, job_id, expected=expected, operation_id=operation_id, request_hash=request_hash)
        with self.lock:
            live = self.live.get(job_id)
            if live is not None:
                live.cancelled.set()
                if live.worker is not None and live.native_id is not None:
                    live.worker.cancel(receipt.creator_user_id, live.native_id)
        return receipt

    def close(self) -> None:
        self.closed.set()
        with self.lock:
            for live in self.live.values():
                live.cancelled.set()
                # The monitor sink observes cancellation even before native ID assignment.
        self.pool.shutdown(wait=True)
