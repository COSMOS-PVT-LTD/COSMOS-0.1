"""Bounded asynchronous P06 orchestration with real QA, no design/store ownership.

Only explicitly named, separately qualified policies can accept software candidates.
There is no publish/hardware/simulation handoff path. Files remain local candidates.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.geometry import WorkerCommand, WorkerError
from plugins.geometry.adapters import GeometryBackend
from plugins.geometry.protocol import ExportFile, checked_file
from systems.contracts.geometry import (
    BuildState,
    DesignSnapshot,
    Disposition,
    GeometryArtifact,
    GeometryBuildEvent,
    GeometryBuildRecord,
    GeometryBuildRequest,
    GeometryCheck,
    GeometryContractError,
    GeometryFeatureGraph,
    GeometryValidationReport,
    OutputFormat,
)
from systems.contracts.geometry._wire import require

from .qa import (
    FixtureReference,
    SurfaceReference,
    audit_mesh,
    condition_exact_zero_faces,
)
from .step_qa import audit_step


@dataclass(frozen=True, slots=True)
class VerifiedCandidate:
    record: GeometryBuildRecord
    directory: Path
    evidence_json: str  # Immutable observations; parse a copy for presentation.


class GeometryBuildService:
    """Three admitted coordinations, one active; supervisor owns native processes."""

    policy_id = "p07.software-fixtures.v1"
    artifact_limit_bytes = 64 * 1024**2
    reviewer_id = "p07-independent-software-audit"
    acceptance_stage = "software_fixture_acceptance"
    acceptance_message = "Software fixture QA accepted; not published or physically validated"

    def prepare_audit(self, output, reference):
        """Policy-specific verified part metadata; default fixture path unchanged."""
        return reference

    def validate_policy(self, snapshot: DesignSnapshot, reference: SurfaceReference) -> None:
        require(snapshot.project_id == "p07-software-fixtures" and isinstance(reference, FixtureReference),
                "UNAPPROVED_POLICY", "Only the predeclared software-fixture reference policy is available; engineering review is separate")

    def audit_candidate(self, path: Path, format_: str, reference: SurfaceReference, request: GeometryBuildRequest,
                        job: str, token: threading.Event) -> dict:
        require(isinstance(reference, FixtureReference), "UNAPPROVED_POLICY", "Fixture service requires its qualified analytic reference")
        assert isinstance(reference, FixtureReference)
        if format_ == "stl":
            return audit_mesh(path, reference, voxel_m=request.voxel_resolution_m, export_tolerance_m=request.export_tolerance_m)
        require(self.step_reader is not None, "QA_UNAVAILABLE", "Independent STEP reader is not configured")
        assert self.step_reader is not None
        return audit_step(path, reference, reader=self.step_reader, supervisor=self.backend.supervisor,
                          job_id=job, tolerance_m=request.export_tolerance_m, cancellation=token)

    def __init__(self, backend: GeometryBackend, candidate_root: Path, *, step_reader: WorkerCommand | None = None) -> None:
        require(candidate_root.is_absolute() and candidate_root.is_dir() and not candidate_root.is_symlink(), "UNSAFE_PATH", "Use an existing trusted private candidate root")
        self.backend, self.root, self.step_reader = backend, candidate_root.resolve(), step_reader
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cosmos-geometry-coordinator")
        self._slots = threading.BoundedSemaphore(3)
        self._lock = threading.Lock()
        self._tokens: dict[str, threading.Event] = {}
        self._closed = False

    def submit(self, request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph,
               reference: SurfaceReference, *, conditioning_profile: str = "raw",
               event_sink: Callable[[GeometryBuildEvent], None] | None = None) -> tuple[str, Future[VerifiedCandidate]]:
        require(conditioning_profile in {"raw", "exact_zero_faces_v1"}, "UNSUPPORTED_PROFILE", "Unknown explicit conditioning profile")
        require(conditioning_profile == "raw" or self.backend.backend_id == "picogk", "UNSUPPORTED_PROFILE", "Exact-zero conditioning applies only to explicit PicoGK STL candidates")
        self.validate_policy(snapshot, reference)
        # Validate before creating files/admitting work. Request wire validation is repeated in the child.
        graph.validate_snapshot(snapshot)
        require(request.snapshot_id == snapshot.snapshot_id and request.feature_graph_sha256 == graph.content_sha256
                and request.feature_graph_id == graph.graph_id, "STALE_REQUEST", "Refuse stale build lineage")
        require(request.frame_id in {f.frame_id for f in snapshot.frames}, "UNKNOWN_FRAME", "Request frame is undefined")
        require(all(f.representation == request.representation for f in graph.features), "REPRESENTATION_MISMATCH", "Refuse mixed representations before admission")
        job_id = "job-" + uuid.uuid4().hex
        with self._lock:
            require(not self._closed, "SERVICE_CLOSED", "Geometry service is closed")
            require(self._slots.acquire(blocking=False), "QUEUE_FULL", "Geometry coordination queue is full")
            token = threading.Event()
            self._tokens[job_id] = token
            future = self._pool.submit(self._run, job_id, request, snapshot, graph, reference, conditioning_profile, token, event_sink)
        def completed(_: Future[VerifiedCandidate]) -> None:
            with self._lock:
                self._tokens.pop(job_id, None)
            self._slots.release()
        future.add_done_callback(completed)
        return job_id, future

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            token = self._tokens.get(job_id)
            if token is None:
                return False
            token.set()
        self.backend.cancel(job_id)
        self.backend.supervisor.cancel("qa-" + job_id)
        return True

    def close(self) -> None:
        with self._lock:
            self._closed = True
            jobs = list(self._tokens)
        for job in jobs:
            self.cancel(job)
        self._pool.shutdown(wait=True)

    def inspect(self, candidate: VerifiedCandidate, snapshot: DesignSnapshot, graph: GeometryFeatureGraph) -> dict[str, object]:
        graph.validate_snapshot(snapshot)
        try:
            integrity = all(checked_file(candidate.directory, Path(a.storage_uri).name, a.sha256) for a in candidate.record.artifacts)
        except (GeometryContractError, OSError):
            integrity = False
        current = candidate.record.snapshot.snapshot_id == snapshot.snapshot_id and candidate.record.feature_graph.content_sha256 == graph.content_sha256
        return {"state": candidate.record.state.value, "current": current, "byte_integrity": integrity,
                "export_eligibility": candidate.record.export_eligibility(snapshot, graph), "published": False, "physical_validation": False}

    def export(self, *_: object) -> None:
        raise GeometryContractError("NOT_PUBLISHED", "P07 creates software-verified candidates only; trusted engineering review/publication is not implemented")

    def _run(self, job: str, request: GeometryBuildRequest, snapshot: DesignSnapshot, graph: GeometryFeatureGraph,
             reference: SurfaceReference, profile: str, token: threading.Event,
             event_sink: Callable[[GeometryBuildEvent], None] | None = None) -> VerifiedCandidate:
        directory = self.root / job
        directory.mkdir(mode=0o700)
        events: list[GeometryBuildEvent] = []
        observations: dict[str, object] = {"policy": self.policy_id, "conditioning_profile": profile,
                                          "physical_validation_claimed": False, "publishing_performed": False, "operation": reference.operation}
        def event(state: BuildState, stage: str, code: str | None = None, message: str = "Geometry phase completed") -> None:
            events.append(GeometryBuildEvent(job, len(events), datetime.now(timezone.utc).isoformat(), state, stage,
                                             None, code, message, (), (), request.correlation_id))
            if event_sink is not None:
                event_sink(events[-1])
        def finish(artifacts=(), reports=()) -> VerifiedCandidate:
            record = GeometryBuildRecord(job, request, snapshot, graph, tuple(events), artifacts, (), reports)
            return VerifiedCandidate(record, directory, json.dumps(observations, sort_keys=True, allow_nan=False))
        event(BuildState.DRAFT, "draft")
        event(BuildState.VALIDATING, "validating")
        if not self.backend.enabled:
            event(BuildState.REJECTED, "configuration", "NGG_DISABLED", "Geometry backend is disabled")
            return finish()
        event(BuildState.QUEUED, "queued")
        if token.is_set():
            event(BuildState.CANCELLED, "queued", "CANCELLED", "Queued job cancelled before native execution")
            return finish()
        event(BuildState.RUNNING, "kernel")
        try:
            result = self.backend.build(job, request, snapshot, graph, directory, cancellation=token).result()
            observations["process"] = {"code": result.code, "pid": result.pid, "exit_code": result.exit_code,
                                       "elapsed_s": result.elapsed_s, "observed_rss_bytes": result.maximum_rss_bytes}
            if token.is_set():
                raise GeometryContractError("CANCELLED", "Cancellation requested; no artifact may be accepted")
            output = self.backend.decode(result, request, directory)
            observations["worker_observations"] = output.metrics
            reference = self.prepare_audit(output, reference)
            files = list(output.exports)
            if profile == "exact_zero_faces_v1":
                source = checked_file(directory, files[0].name, files[0].sha256)
                target = directory / "export-conditioned.stl"
                observations["conditioning"] = condition_exact_zero_faces(source, target)
                files[0] = ExportFile(target.name, hashlib.sha256(target.read_bytes()).hexdigest(), "stl", "m")
            event(BuildState.QA, "independent_qa")
            artifacts, reports, checks = [], [], []
            for index, file in enumerate(files):
                path = checked_file(directory, file.name, file.sha256,max_bytes=self.artifact_limit_bytes)
                qa = self.audit_candidate(path, file.format, reference, request, job, token)
                observations["qa-" + file.format] = qa
                artifact_id, report_id = "artifact-" + str(index), "report-" + job + "-" + str(index)
                required_checks = tuple(GeometryCheck(name, bool(qa[metric]), None, None, "1", ("evidence-" + job,))
                                        for name, metric in (("topology", "topology_pass"), ("dimensions", "dimensions_pass"), ("export_round_trip", "pass")))
                checks.append(bool(qa["pass"]))
                reports.append(GeometryValidationReport(report_id, artifact_id, required_checks, self.policy_id,
                                                         self.reviewer_id, Disposition.ACCEPTED if qa["pass"] else Disposition.REJECTED))
                artifacts.append(GeometryArtifact(artifact_id, job, "geometry-" + job, snapshot.snapshot_id, graph.content_sha256,
                                                   request.representation, request.approximation_profile, request.backend_id, request.backend_version,
                                                   "m", request.frame_id, request.source_tolerance_m, request.export_tolerance_m,
                                                   request.voxel_resolution_m, output.source_sha256, file.sha256, OutputFormat(file.format),
                                                   job + "/" + file.name, path.stat().st_size, report_id, datetime.now(timezone.utc).isoformat()))
            if token.is_set():
                event(BuildState.REJECTED, "independent_qa", "QA_CANCELLED", "Independent QA cancelled; candidate refused")
                self._remove_candidate_files(directory)
                return finish(reports=tuple(reports))
            if not all(checks):
                event(BuildState.REJECTED, "independent_qa", "QA_FAILED", "Independent topology/dimensional/reimport evidence failed")
                return finish(reports=tuple(reports))
            event(BuildState.ACCEPTED, self.acceptance_stage, message=self.acceptance_message)
            return finish(tuple(artifacts), tuple(reports))
        except (GeometryContractError, WorkerError, OSError, ValueError) as error:
            code = getattr(error, "code", "GEOMETRY_FAILURE")
            observations["diagnostic"] = {"code": code, "message": str(error)[:1024]}
            if events[-1].state is BuildState.QA:
                event(BuildState.REJECTED, "independent_qa", code, "Independent QA refused the candidate")
                if token.is_set():
                    self._remove_candidate_files(directory)
            elif code == "CANCELLED" or token.is_set():
                event(BuildState.CANCEL_REQUESTED, "kernel", "CANCELLED", "Cancellation requested")
                event(BuildState.CANCELLED, "kernel", "CANCELLED", "Worker terminated; no published artifact")
                self._remove_candidate_files(directory)
            else:
                event(BuildState.FAILED, "kernel", code, "Worker failed; no artifact accepted")
            return finish()

    @staticmethod
    def _remove_candidate_files(directory: Path) -> None:
        # Only exact registered filenames inside this service-created private job.
        for name in ("source.vdb", "source.brep", "export.stl", "export.step", "export-conditioned.stl", "native-mm.stl"):
            path = directory / name
            if path.is_file() or path.is_symlink():
                path.unlink()
