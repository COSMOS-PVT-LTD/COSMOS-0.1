"""Ephemeral, actor-scoped P08 software-fixture workbench. No publication authority.

All scientific lineage is held in immutable P06 DTOs. This tool neither reads nor
writes engineering DesignStore state. Fixture exchange is not service.export().
"""
from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter, PicoGKAdapter
from plugins.geometry.protocol import checked_file
from systems.contracts.geometry import (
    BuildState,
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeatureGraph,
)
from systems.contracts.geometry._wire import require

from .qa import FixtureReference, audit_mesh, read_stl
from .service import GeometryBuildService, VerifiedCandidate
from .software_fixtures import case
from .step_qa import audit_step

OPERATIONS = ("sphere", "union", "difference", "intersection", "self_union")
RECOVERY = "Inspect the exact snapshot/QA; correct settings, rebuild or retry. Engineering publication is unavailable."


@dataclass(frozen=True)
class Revision:
    settings: dict[str, Any]
    snapshot: DesignSnapshot
    graph: GeometryFeatureGraph
    request: GeometryBuildRequest


@dataclass
class Session:
    current: str
    revisions: dict[str, Revision]
    jobs: dict[str, tuple[Revision, Future[VerifiedCandidate]]] = field(default_factory=dict)
    previews: dict[str, bytes] = field(default_factory=dict)
    reimports: dict[str, Future[dict[str, Any]]] = field(default_factory=dict)


class GeometryWorkbench:
    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        require(root.is_absolute() and root.is_dir() and not root.is_symlink(), "UNSAFE_PATH", "Use trusted local candidate storage")
        self.root = root
        self.supervisor = WorkerSupervisor()
        def command(name: str) -> WorkerCommand:
            item = config[name]
            return WorkerCommand(tuple(item["argv"]), tuple(item["environment"].items()))
        self.reader = command("step_reader")
        self.preview_reader = WorkerCommand((self.reader.argv[0], str(Path(__file__).resolve().parents[2] / "plugins/geometry/workers/preview_reader.py")), self.reader.environment)
        self.services = {name: GeometryBuildService(adapter(command(name), self.supervisor, enabled=True), root, step_reader=self.reader)
                         for name, adapter in (("occt", OCCTAdapter), ("picogk", PicoGKAdapter))}
        self.lock = threading.RLock()
        self.sessions: dict[str, Session] = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ngg-reimport")
        self.reimport_slot = threading.BoundedSemaphore(1)

    @staticmethod
    def revision(settings: dict[str, Any]) -> Revision:
        require(type(settings) is dict and set(settings) == {"operation", "backend", "voxel_m"}, "INVALID_SETTINGS", "Explicit operation/backend/voxel SI fields required")
        require(settings["operation"] in OPERATIONS and settings["backend"] in {"occt", "picogk"}
                and type(settings["voxel_m"]) in (int, float) and settings["voxel_m"] in (.001, .0005, .00025),
                "UNQUALIFIED_FIXTURE", "Only fixed 10mm synthetic sphere/Boolean fixtures and declared voxel sizes are qualified")
        snapshot, graph, request = case(settings["operation"], settings["backend"], settings["voxel_m"])
        stamp = datetime.now(timezone.utc).isoformat()
        snapshot = replace(snapshot, revision_id="p08-" + uuid.uuid4().hex, created_at=stamp)
        graph = replace(graph, snapshot_id=snapshot.snapshot_id)
        request = replace(request, snapshot_id=snapshot.snapshot_id, feature_graph_sha256=graph.content_sha256,
                          request_id="request-" + uuid.uuid4().hex, correlation_id="p08-" + uuid.uuid4().hex)
        return Revision(settings.copy(), snapshot, graph, request)

    def session(self, actor: str) -> Session:
        with self.lock:
            if actor not in self.sessions:
                require(len(self.sessions) < 16, "SESSION_LIMIT", "Local qualification session limit reached")
                revision = self.revision({"operation": "sphere", "backend": "occt", "voxel_m": .0005})
                self.sessions[actor] = Session(revision.snapshot.snapshot_id, {revision.snapshot.snapshot_id: revision})
            return self.sessions[actor]

    def context(self, actor: str) -> dict[str, Any]:
        with self.lock:
            session = self.session(actor)
            revision = session.revisions[session.current]
            return {"policy": "software-fixtures-only", "project_id": revision.snapshot.project_id,
                    "settings": revision.settings.copy(), "snapshot": json.loads(revision.snapshot.to_json()),
                    "graph": json.loads(revision.graph.to_json()), "request": json.loads(revision.request.to_json()),
                    "revision_count": len(session.revisions), "job_ids": list(session.jobs), "published": False, "physical_validation": False}

    def change(self, actor: str, base_snapshot: str, settings: dict[str, Any]) -> dict[str, Any]:
        with self.lock:
            session = self.session(actor)
            require(session.current == base_snapshot, "STALE_CONTEXT", "Reload current snapshot before changing settings")
            require(len(session.revisions) < 16, "REVISION_LIMIT", "Local immutable revision limit reached; restart isolated qualification session")
            revision = self.revision(settings)
            session.revisions[revision.snapshot.snapshot_id] = revision
            session.current = revision.snapshot.snapshot_id
            return self.context(actor)

    def activate(self, actor: str, snapshot: str) -> dict[str, Any]:
        with self.lock:
            session = self.session(actor)
            require(snapshot in session.revisions, "UNKNOWN_SNAPSHOT", "Undo may activate only an existing immutable local revision")
            session.current = snapshot
            return self.context(actor)

    def build(self, actor: str, snapshot: str) -> dict[str, str]:
        with self.lock:
            session = self.session(actor)
            require(session.current == snapshot, "STALE_CONTEXT", "Build requires the exact active server snapshot")
            require(len(session.jobs) < 8 and sum(len(s.jobs) for s in self.sessions.values()) < 32, "JOB_LIMIT", "Local qualification candidate limit reached")
            revision = session.revisions[snapshot]
            service = self.services[revision.request.backend_id]
            job, future = service.submit(revision.request, revision.snapshot, revision.graph, FixtureReference(revision.settings["operation"]),
                                         conditioning_profile="exact_zero_faces_v1" if revision.request.backend_id == "picogk" else "raw")
            session.jobs[job] = (revision, future)
            return {"job_id": job, "snapshot_id": snapshot}

    def owned(self, actor: str, job: str) -> tuple[Revision, Future[VerifiedCandidate]]:
        session = self.session(actor)
        require(job in session.jobs, "UNKNOWN_JOB", "Job is unavailable in this actor's session")
        return session.jobs[job]

    def status(self, actor: str, job: str) -> dict[str, Any]:
        with self.lock:
            revision, future = self.owned(actor, job)
            current = self.session(actor).current == revision.snapshot.snapshot_id
            result: dict[str, Any] = {"job_id": job, "snapshot_id": revision.snapshot.snapshot_id, "current": current,
                                      "state": "running" if future.running() else "queued", "progress_fraction": None,
                                      "published": False, "engineering_export_eligible": False}
            if future.done():
                candidate = future.result()
                integrity = self.services[revision.request.backend_id].inspect(candidate, revision.snapshot, revision.graph)
                result.update(state=candidate.record.state.value, byte_integrity=integrity["byte_integrity"],
                              fixture_exchange_eligible=current and integrity["byte_integrity"] and candidate.record.state is BuildState.ACCEPTED,
                              record=json.loads(candidate.record.to_json()), qa=json.loads(candidate.evidence_json))
            return result

    def accepted(self, actor: str, job: str, snapshot: str) -> tuple[Revision, VerifiedCandidate]:
        with self.lock:
            revision, future = self.owned(actor, job)
            require(snapshot == self.session(actor).current == revision.snapshot.snapshot_id, "STALE_ARTIFACT", "Activate the exact built snapshot or rebuild; no stale exchange")
            require(future.done(), "BUILD_PENDING", "Wait for actual build and independent QA")
            candidate = future.result()
            require(candidate.record.state is BuildState.ACCEPTED and bool(candidate.record.artifacts), "QA_REJECTED", "No exchange or inspection of unaccepted candidates")
            require(self.services[revision.request.backend_id].inspect(candidate, revision.snapshot, revision.graph)["byte_integrity"] is True, "ARTIFACT_TAMPERED", "Candidate bytes no longer match their immutable hashes")
            return revision, candidate

    def fixture_bytes(self, actor: str, job: str, snapshot: str) -> tuple[str, bytes, str]:
        _revision, candidate = self.accepted(actor, job, snapshot)
        artifact = candidate.record.artifacts[0]
        path = checked_file(candidate.directory, Path(artifact.storage_uri).name, artifact.sha256)
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == artifact.sha256, "ARTIFACT_TAMPERED", "Fixture changed during byte read")
        self.accepted(actor, job, snapshot)
        return "COSMOS-software-fixture-" + job + "." + artifact.output_format.value, data, artifact.sha256

    def preview(self, actor: str, job: str, snapshot: str) -> bytes:
        _revision, candidate = self.accepted(actor, job, snapshot)
        with self.lock:
            session = self.session(actor)
            if job in session.previews:
                return session.previews[job]
        artifact = candidate.record.artifacts[0]
        path = checked_file(candidate.directory, Path(artifact.storage_uri).name, artifact.sha256)
        if artifact.output_format.value == "stl":
            _, triangles, _ = read_stl(path)
            points = triangles.reshape(-1, 3)
        else:
            result = self.supervisor.submit("preview-" + job, WorkerCommand((*self.preview_reader.argv, str(path)), self.preview_reader.environment), b"", candidate.directory).result()
            require(result.code == "OK", result.code, "Display triangulation failed; accepted source remains unchanged")
            payload = json.loads(result.stdout)
            require(payload.get("profile") == "gmsh-display-only-1-2mm", "INVALID_RESPONSE", "Unknown display mesh profile")
            points = np.asarray(payload["positions_m"], dtype=float).reshape(-1, 3)
        require(len(points) <= 600_000 and len(points) % 3 == 0 and bool(np.isfinite(points).all()), "INVALID_PREVIEW", "Invalid bounded display mesh")
        data = points.astype("<f4").tobytes()
        with self.lock:
            self.session(actor).previews[job] = data
        self.accepted(actor, job, snapshot)  # Snapshot/bytes could change during read.
        return data

    def measure(self, actor: str, job: str, snapshot: str, indices: list[int]) -> dict[str, Any]:
        revision, candidate = self.accepted(actor, job, snapshot)
        require(type(indices) is list and len(indices) in (0, 2) and all(type(i) is int and i >= 0 for i in indices), "INVALID_MEASUREMENT", "Select two display vertex indices or bounds")
        qa = json.loads(candidate.evidence_json)["qa-" + candidate.record.artifacts[0].output_format.value]
        result = {"snapshot_id": snapshot, "volume_m3": qa["volume_m3"], "centroid_m": qa["centroid_m"],
                  "bounds_m": FixtureReference(revision.settings["operation"]).bounds_m.tolist(),
                  "bounds_source": "predeclared fixture reference, verified against candidate QA", "physical_validation": False}
        if indices:
            points = np.frombuffer(self.preview(actor, job, snapshot), dtype="<f4").reshape(-1, 3)
            require(max(indices) < len(points), "INVALID_MEASUREMENT", "Display vertex index is outside this immutable mesh")
            result.update(distance_m=float(np.linalg.norm(points[indices[0]].astype(float) - points[indices[1]].astype(float))),
                          points_m=points[indices].tolist(), measurement_scope="sampled display vertices, not analytic feature metrology")
        return result

    def cancel(self, actor: str, job: str) -> dict[str, bool]:
        revision, _ = self.owned(actor, job)
        return {"cancel_requested": self.services[revision.request.backend_id].cancel(job)}

    def reimport(self, actor: str, job: str, snapshot: str, data: bytes) -> dict[str, str]:
        revision, candidate = self.accepted(actor, job, snapshot)
        artifact = candidate.record.artifacts[0]
        require(0 < len(data) <= 12 * 1024**2 and hashlib.sha256(data).hexdigest() == artifact.sha256, "REIMPORT_HASH_MISMATCH", "Reimport only the exact exchanged software fixture, not arbitrary files")
        with self.lock:
            require(len(self.session(actor).reimports) < 8 and self.reimport_slot.acquire(blocking=False), "QUEUE_FULL", "Local independent reimport queue is busy or full")
            import_id = "reimport-" + uuid.uuid4().hex
            def run() -> dict[str, Any]:
                try:
                    with tempfile.TemporaryDirectory(prefix="reimport-", dir=self.root) as directory:
                        path = Path(directory) / ("export." + artifact.output_format.value)
                        path.write_bytes(data)
                        reference = FixtureReference(revision.settings["operation"])
                        qa = (audit_step(path, reference, reader=self.reader, supervisor=self.supervisor, job_id=import_id,
                                         tolerance_m=revision.request.export_tolerance_m) if artifact.output_format.value == "step"
                              else audit_mesh(path, reference, voxel_m=revision.request.voxel_resolution_m, export_tolerance_m=revision.request.export_tolerance_m))
                        self.accepted(actor, job, snapshot)
                        return {"pass": qa["pass"], "qa": qa, "snapshot_id": snapshot, "artifact_sha256": artifact.sha256,
                                "independent_reimport": True, "published": False, "physical_validation": False}
                finally:
                    self.reimport_slot.release()
            self.session(actor).reimports[import_id] = self.pool.submit(run)
            return {"reimport_id": import_id}

    def reimport_status(self, actor: str, import_id: str) -> dict[str, Any]:
        with self.lock:
            jobs = self.session(actor).reimports
            require(import_id in jobs, "UNKNOWN_JOB", "Reimport belongs to another or expired actor session")
            future = jobs[import_id]
            if not future.done():
                return {"state": "running", "progress_fraction": None}
            return {"state": "completed", "result": future.result()}

    def close(self) -> None:
        for service in self.services.values():
            service.close()
        self.pool.shutdown(wait=True)
        self.supervisor.close()
