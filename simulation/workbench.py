"""Actor-scoped asynchronous benchmark orchestration, not engineering storage."""
from __future__ import annotations

import hashlib
import json
import math
import threading
import time
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

from core.exceptions import CosmosError
from numerics.finite_volume.radial_diffusion import DiffusionCancelled, solve
from physics.heat_transfer.spherical_conduction import reference_temperature
from plugins.geometry.protocol import checked_file
from systems.contracts.geometry import MappingStatus, NamedSelection
from systems.contracts.geometry._wire import (
    GeometryContractError,
    digest,
    dumps,
    require,
)
from systems.geometry.source_contract import GeometrySource

from .contracts import FixtureHandoff, StudySettings, StudySnapshot


def mesh(study: StudySnapshot) -> dict[str, Any]:
    """Explicit analytic symmetry reduction; never reuse display triangles."""
    h, n = study.handoff, study.settings.cells
    faces = [h.radius_m * i / n for i in range(n + 1)]
    result: dict[str, Any] = {"kind": "1d-spherical-finite-volume", "units": "m", "frame_id": h.frame_id,
        "geometry_revision_id": h.artifact.geometry_revision_id, "geometry_snapshot_id": h.geometry_snapshot_id,
        "geometry_sha256": h.artifact.sha256, "source_sha256": h.artifact.source_artifact_sha256,
        "integrity_sha256": h.integrity_sha256, "handoff_sha256": h.content_sha256,
        "faces_m": faces, "cells": n, "material_region": "solid-sphere",
        "cell_volumes_m3": [4 * math.pi / 3 * (b**3 - a**3) for a, b in pairwise(faces)],
        "named_selection": json.loads(h.selection.to_json()), "outer_boundary_face": n,
        "center_condition": "regular-zero-flux", "production_handoff": False}
    result["mesh_sha256"] = digest(result)
    return result


@dataclass
class Run:
    study: StudySnapshot
    job_id: str
    geometry_job: str
    token: threading.Event = field(default_factory=threading.Event)
    state: str = "queued"
    events: tuple[dict[str, Any], ...] = ()
    future: Future[None] | None = None
    dataset: bytes | None = None
    checksum: str | None = None
    diagnostic: dict[str, str] | None = None


@dataclass
class Session:
    current: str | None = None
    studies: dict[str, tuple[StudySnapshot, str]] = field(default_factory=dict)
    runs: dict[str, Run] = field(default_factory=dict)


class SimulationWorkbench:
    def __init__(self, *, monitor_sink: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.lock = threading.RLock()
        self.sessions: dict[str, Session] = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cosmos-simulation")
        self.slots = threading.BoundedSemaphore(2)
        self.closed = False
        self.monitor_sink = monitor_sink

    def session(self, actor: str) -> Session:
        with self.lock:
            if actor not in self.sessions:
                require(len(self.sessions) < 16, "SESSION_LIMIT", "Restart isolated preview after local session limit")
                self.sessions[actor] = Session()
            return self.sessions[actor]

    def context(self, actor: str) -> dict[str, Any]:
        with self.lock:
            session = self.session(actor)
            study = session.studies[session.current][0] if session.current else None
            return {"scope": "software-benchmark-only", "project_id": "p07-software-fixtures", "study_id": session.current,
                "study": json.loads(study.to_json()) if study else None, "mesh": mesh(study) if study else None,
                "default_settings": json.loads(StudySettings().to_json()), "run_ids": list(session.runs),
                "production_handoff": False, "experimental_validation": "not-performed", "engineering_review": "pending"}

    def attach(self, actor: str, geometry: GeometrySource, job: str, snapshot: str) -> dict[str, Any]:
        revision, candidate = geometry.accepted(actor, job, snapshot)
        require(revision.settings["backend"] == "occt" and revision.settings["operation"] == "sphere",
                "UNQUALIFIED_HANDOFF", "Only an independently accepted OCCT sphere qualifies; no inferred Boolean/PicoGK boundary mapping")
        artifact = candidate.record.artifacts[0]
        # Both actual source and export files must still match their independent QA.
        checked_file(candidate.directory, "source.brep", artifact.source_artifact_sha256)
        qa = json.loads(candidate.evidence_json)
        require(qa["qa-step"]["pass"] is True, "QA_REJECTED", "Independent STEP reimport acceptance is required")
        selection = NamedSelection("outer-surface", artifact.geometry_revision_id, "body", ("radial-outer-shell",), 1., MappingStatus.EXACT)
        selection.validate_binding(revision.graph, artifact)
        handoff = FixtureHandoff(artifact, selection, hashlib.sha256(candidate.evidence_json.encode()).hexdigest(), .01, "world", snapshot)
        study = StudySnapshot(handoff, StudySettings())
        geometry.accepted(actor, job, snapshot)
        with self.lock:
            session = self.session(actor)
            require(len(session.studies) < 16, "REVISION_LIMIT", "Local immutable study limit reached")
            session.studies[study.content_sha256] = (study, job)
            session.current = study.content_sha256
            return self.context(actor)

    def change(self, actor: str, base: str, settings: dict[str, Any]) -> dict[str, Any]:
        require(type(settings) is dict and set(settings) == {"conductivity_w_m_k", "generation_w_m3", "surface_k", "cells", "relative_residual", "max_iterations"},
                "INVALID_SETTINGS", "Exact SI settings required; no defaults silently applied")
        parsed = StudySettings(**settings)
        with self.lock:
            session = self.session(actor)
            require(base == session.current and base in session.studies, "STALE_STUDY", "Reload the active immutable study before editing")
            require(len(session.studies) < 16, "REVISION_LIMIT", "Local immutable study limit reached")
            old, job = session.studies[base]
            study = StudySnapshot(old.handoff, parsed)
            session.studies[study.content_sha256] = (study, job)
            session.current = study.content_sha256
            return self.context(actor)

    def activate(self, actor: str, study_id: str) -> dict[str, Any]:
        with self.lock:
            session = self.session(actor)
            require(study_id in session.studies, "UNKNOWN_STUDY", "Undo only existing studies owned by this actor")
            session.current = study_id
            return self.context(actor)

    def owned(self, actor: str, job: str) -> Run:
        session = self.session(actor)
        require(job in session.runs, "UNKNOWN_RUN", "Run is absent or belongs to another actor")
        return session.runs[job]

    def submit(self, actor: str, geometry: GeometrySource, study_id: str) -> dict[str, str]:
        with self.lock:
            session = self.session(actor)
            require(study_id == session.current and study_id in session.studies, "STALE_STUDY", "Run requires the exact active study")
            study, geometry_job = session.studies[study_id]
            geometry.accepted(actor, geometry_job, study.handoff.geometry_snapshot_id)
            require(not self.closed and len(session.runs) < 8 and sum(len(s.runs) for s in self.sessions.values()) < 32,
                    "RUN_LIMIT", "Restart isolated preview after bounded history limit")
            require(self.slots.acquire(blocking=False), "QUEUE_FULL", "Two local solver slots are occupied; wait or cancel")
            job = "sim-" + uuid.uuid4().hex
            run = Run(study, job, geometry_job)
            session.runs[job] = run
            try:
                run.future = self.pool.submit(self.execute, actor, geometry, run)
            except RuntimeError:
                self.slots.release(); session.runs.pop(job)
                raise
            return {"run_id": job, "study_id": study_id}

    def execute(self, actor: str, geometry: GeometrySource, run: Run) -> None:
        start = time.perf_counter()
        try:
            _, candidate = geometry.accepted(actor, run.geometry_job, run.study.handoff.geometry_snapshot_id)
            checked_file(candidate.directory, "source.brep", run.study.handoff.artifact.source_artifact_sha256)
            current_source = StudySnapshot(run.study.handoff, run.study.settings)
            require(current_source.solver_sha256 == run.study.solver_sha256 and current_source.model_sha256 == run.study.model_sha256,
                    "SOURCE_CHANGED", "Solver/model bytes changed since immutable study; create a new study")
            with self.lock:
                run.state = "running"
            def monitor(index: int, residual: float, balance: float) -> None:
                with self.lock:
                    run.events += ({"seq": len(run.events), "iteration": index, "normalized_residual": residual,
                                    "power_imbalance_w": balance, "correlation_id": run.job_id},)
                    original = dict(run.events[-1])
                if self.monitor_sink is not None:
                    self.monitor_sink(original)
            s, h = run.study.settings, run.study.handoff
            result = solve(h.radius_m, s.cells, s.conductivity_w_m_k, s.generation_w_m3, s.surface_k,
                           tolerance=s.relative_residual, max_iterations=s.max_iterations, monitor=monitor, cancelled=run.token.is_set)
            if run.token.is_set():
                raise DiffusionCancelled("Cancellation requested")
            expected = [reference_temperature(h.radius_m, r, s.conductivity_w_m_k, s.generation_w_m3, s.surface_k) for r in result.centers]
            error = float(max(abs(actual - ref) for actual, ref in zip(result.values, expected)))
            error_limit = s.generation_w_m3 * h.radius_m**2 / (6 * s.conductivity_w_m_k * s.cells**2)
            relative_balance = abs(result.outward - result.generated) / result.generated
            conservation_limit = 2 * math.sqrt(s.cells) * s.relative_residual
            physical = all(math.isfinite(v) and v > 0 for v in result.values)
            verification = result.converged and relative_balance <= conservation_limit and error <= error_limit and physical
            dataset: dict[str, Any] = {"schema_version": "p09-dataset-v1", "run_id": run.job_id, "study_id": run.study.content_sha256,
                "study": json.loads(run.study.to_json()), "mesh": mesh(run.study), "execution_status": "completed", "termination_reason": result.termination,
                "numerical_convergence": "converged" if result.converged else "nonconverged",
                "conservation_checks": {"generated_power_w": result.generated, "outward_power_w": result.outward,
                    "signed_imbalance_w": result.outward - result.generated, "relative_imbalance": relative_balance,
                    "limit": conservation_limit, "passed": relative_balance <= conservation_limit},
                "physical_admissibility": "passed-positive-finite-temperature" if physical else "failed",
                "solution_verification": "analytic-benchmark-passed" if verification else "not-accepted",
                "experimental_validation": "not-performed", "engineering_review": "pending", "production_handoff": False,
                "radii_m": list(result.centers), "temperature_k": list(result.values), "reference_k": expected,
                "field": {"quantity": "Temperature", "unit": "K", "min": min(result.values), "max": max(result.values),
                          "clipping": "none", "color_map": "Blue-Gold", "interpretation": "1D radial profile; not a 3D field"},
                "residual_definition": "L2(b-A(T-Ts))/L2(b); b=qV", "residual_scale": "linear",
                "iterations": list(result.iterations), "normalized_residuals": list(result.residual_history),
                "power_imbalance_w": list(result.balance_history), "max_reference_error_k": error, "reference_error_limit_k": error_limit,
                "cfl_time_step": "not-applicable-steady-elliptic", "elapsed_s": time.perf_counter() - start,
                "diagnostics": [] if verification else [{"code": "NUMERICAL_ITERATION_LIMIT" if not result.converged else "VERIFICATION_NOT_ACCEPTED",
                    "cause": "Iteration limit reached before equation residual tolerance" if not result.converged else "Independent solution checks did not pass",
                    "action": "Inspect residual and conservation; explicitly revise settings or mesh and submit a new run"}],
                "source_refs": [{"path": "physics/heat_transfer/spherical_conduction.py", "sha256": run.study.model_sha256},
                                {"path": "numerics/finite_volume/radial_diffusion.py", "sha256": run.study.solver_sha256}]}
            data = dumps(dataset).encode()
            with self.lock:
                if run.token.is_set():
                    raise DiffusionCancelled("Cancellation requested before dataset commit")
                run.dataset = data; run.checksum = hashlib.sha256(data).hexdigest(); run.state = "completed"
        except DiffusionCancelled:
            with self.lock:
                run.state = "cancelled"
                run.diagnostic = {"code": "CANCELLED", "cause": "User requested cancellation", "action": "Submit a new immutable run when ready"}
        except (CosmosError, ValueError, TypeError, KeyError, OSError, RuntimeError, ArithmeticError, MemoryError) as error:
            with self.lock:
                run.state = "failed"
                run.diagnostic = {"code": error.code if isinstance(error, GeometryContractError) else "SOLVER_FAILURE",
                                  "cause": str(error)[:1024], "action": "Inspect geometry lineage and numerical settings; retry a new run"}
        finally:
            self.slots.release()

    def dataset(self, actor: str, job: str) -> dict[str, Any]:
        with self.lock:
            run = self.owned(actor, job)
            require(run.state == "completed" and run.dataset is not None and len(run.dataset) < 512 * 1024,
                    "DATASET_UNAVAILABLE", "No complete bounded result; inspect termination diagnostic")
            assert run.dataset is not None
            require(hashlib.sha256(run.dataset).hexdigest() == run.checksum, "CORRUPT_DATASET", "Result checksum mismatch; preserve evidence and rerun")
            return json.loads(run.dataset)

    def status(self, actor: str, geometry: GeometrySource, job: str) -> dict[str, Any]:
        with self.lock:
            run = self.owned(actor, job)
            current_geometry = geometry.context(actor)["snapshot"]["content_sha256"]
            geometry_integrity = False
            try:
                _, candidate = geometry.accepted(actor, run.geometry_job, run.study.handoff.geometry_snapshot_id)
                checked_file(candidate.directory, "source.brep", run.study.handoff.artifact.source_artifact_sha256)
                geometry_integrity = True
            except (GeometryContractError, OSError):
                pass  # Preserve original immutable run; current acceptance is false.
            current = self.session(actor).current == run.study.content_sha256 and current_geometry == run.study.handoff.geometry_snapshot_id and geometry_integrity
            value = {"run_id": job, "study_id": run.study.content_sha256, "state": run.state,
                     "freshness": "current" if current else "stale", "events": list(run.events),
                     "geometry_integrity_current": geometry_integrity,
                     "diagnostic": run.diagnostic, "dataset_sha256": run.checksum, "production_handoff": False}
            if run.state == "completed":
                value["result"] = self.dataset(actor, job)
            return value

    def cancel(self, actor: str, job: str) -> dict[str, bool]:
        with self.lock:
            run = self.owned(actor, job)
            requested = run.state in {"queued", "running"}
            if requested:
                run.token.set()
            return {"cancel_requested": requested}

    def close(self) -> None:
        with self.lock:
            self.closed = True
            for session in self.sessions.values():
                for run in session.runs.values():
                    run.token.set()
        self.pool.shutdown(wait=True)
