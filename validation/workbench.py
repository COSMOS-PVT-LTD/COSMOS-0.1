"""Bounded actor-scoped evidence preview; no engineering publication authority."""
from __future__ import annotations

import base64
import hashlib
import json
import math
import tempfile
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from plugins.geometry.protocol import checked_file
from systems.contracts.geometry._wire import digest, dumps, require
from systems.geometry.qa import FixtureReference
from systems.geometry.step_qa import audit_step
from systems.geometry.workbench import GeometryWorkbench

from .benchmarks import analytic, from_run
from .comparison import compare
from .contracts import Criteria, ThermalDataset, fields, text


@dataclass
class Session:
    sequence: int = 0
    datasets: dict[str, tuple[ThermalDataset, int]] = field(default_factory=dict)
    policies: dict[str, tuple[Criteria, int]] = field(default_factory=dict)
    first_seen: dict[str, int] = field(default_factory=dict)
    runs: dict[str, str] = field(default_factory=dict)
    reports: dict[str, bytes] = field(default_factory=dict)
    reviews: dict[str, tuple[bytes, ...]] = field(default_factory=dict)
    geometries: dict[str, bytes] = field(default_factory=dict)
    files: dict[str, tuple[Path, str]] = field(default_factory=dict)
    imports: dict[str, Future[dict[str, Any]]] = field(default_factory=dict)
    candidate: str | None = None


class ComparisonWorkbench:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.lock = threading.RLock()
        self.sessions: dict[str, Session] = {}
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cosmos-vv-import")
        self.slots = threading.BoundedSemaphore(2)

    def session(self, actor: str) -> Session:
        with self.lock:
            if actor not in self.sessions:
                require(len(self.sessions) < 16, "SESSION_LIMIT", "Local preview session limit reached")
                self.sessions[actor] = Session()
            return self.sessions[actor]

    def context(self, actor: str) -> dict[str, Any]:
        with self.lock:
            s = self.session(actor)
            imports: list[dict[str, Any]] = []
            for key, future in s.imports.items():
                if not future.done():
                    imports.append({"import_id": key, "state": "running"})
                else:
                    try:
                        imports.append({"import_id": key, "state": "completed", "result": future.result()})
                    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as error:
                        imports.append({"import_id": key, "state": "failed", "diagnostic": {"code": getattr(error, "code", "CAD_IMPORT_FAILED"), "cause": str(error), "action": "Use a trusted metre-unit analytic sphere STEP and qualified reader"}})
            candidate = s.datasets[s.candidate][0].data if s.candidate else None
            suggested = None
            if candidate:
                c = candidate["conditions"]
                bound = c["generation_w_m3"] * c["radius_m"]**2 / (6*c["conductivity_w_m_k"]*len(candidate["values"])**2)
                suggested = {"intended_use": "Independent analytic spherical software benchmark only; no physical or production release",
                    "rationale": "Predeclared P09 discretization ceiling qR²/(6kN²); uncertainty limit is an illustrative software-contract budget, not an engineering acceptance basis",
                    "max_abs_error_k": bound, "max_combined_standard_uncertainty_k": bound,
                    "coverage_factor": 2, "correlation": 0, "allow_unit_conversion": False}
            return {"schema_version": "p10-context-v1", "scope": "local-software-evidence-preview", "project_id": "p07-software-fixtures",
                "candidate_id": s.candidate, "candidate": candidate,
                "suggested_criteria": suggested,
                "datasets": [{"dataset_id": key, "kind": d.data["kind"], "source": d.data["provenance"]["source"], "sample_count": len(d.data["values"])} for key, (d, _) in s.datasets.items()],
                "criteria": [{"criteria_id": key, "criteria": p.data} for key, (p, _) in s.policies.items()],
                "report_ids": list(s.reports), "geometries": [json.loads(v) for v in s.geometries.values()], "imports": imports,
                "storage": "ephemeral bounded preview; download immutable receipts for retention",
                "experimental_validation": "not-performed", "independent_acceptance": False, "production_handoff": False}

    def declare(self, actor: str, value: dict[str, Any]) -> dict[str, str]:
        p = Criteria.parse(value)
        with self.lock:
            s = self.session(actor)
            require(len(s.policies) < 16, "CRITERIA_LIMIT", "Local criteria snapshot limit reached")
            s.sequence += 1
            s.policies.setdefault(p.content_sha256, (p, s.sequence))
            return {"criteria_id": p.content_sha256}

    def add(self, actor: str, d: ThermalDataset, *, candidate: bool = False, run_id: str | None = None) -> dict[str, str]:
        with self.lock:
            s = self.session(actor)
            require(len(s.datasets) < 16, "DATASET_LIMIT", "Local immutable dataset limit reached")
            s.sequence += 1
            s.datasets.setdefault(d.content_sha256, (d, s.sequence))
            # Reimporting the same file cannot make a later policy predeclared.
            s.first_seen.setdefault(d.data["provenance"]["source_sha256"], s.sequence)
            if candidate:
                s.candidate = d.content_sha256
            if run_id:
                s.runs[d.content_sha256] = run_id
            return {"dataset_id": d.content_sha256}

    def use_run(self, actor: str, simulation: Any, geometry: GeometryWorkbench, run_id: str) -> dict[str, str]:
        status = simulation.status(actor, geometry, run_id)
        require(status["freshness"] == "current" and status["geometry_integrity_current"], "STALE_SOURCE", "Only the current hash-checked study can be imported")
        return self.add(actor, from_run(simulation.dataset(actor, run_id)), candidate=True, run_id=run_id)

    def reference(self, actor: str, candidate_id: str) -> dict[str, str]:
        with self.lock:
            s = self.session(actor)
            require(candidate_id in s.datasets, "UNKNOWN_DATASET", "Use an owned candidate first")
            d = analytic(s.datasets[candidate_id][0])
            return self.add(actor, d)

    def imported(self, actor: str, value: dict[str, Any]) -> dict[str, str]:
        d = ThermalDataset.parse(value)
        require(d.data["kind"] in {"external-solver", "experimental", "analytic-reference"}, "INVALID_IMPORT", "A client cannot forge a COSMOS simulation dataset")
        return self.add(actor, d)

    def assess(self, actor: str, candidate_id: str, reference_id: str, criteria_id: str, simulation: Any = None, geometry: Any = None) -> dict[str, Any]:
        with self.lock:
            s = self.session(actor)
            require(candidate_id in s.datasets and reference_id in s.datasets and criteria_id in s.policies, "UNKNOWN_EVIDENCE", "All evidence must belong to the current actor")
            a, _ = s.datasets[candidate_id]; b, _ = s.datasets[reference_id]; p, seq = s.policies[criteria_id]
            require(seq < s.first_seen[b.data["provenance"]["source_sha256"]], "POST_HOC_CRITERIA", "Criteria must precede the first import of this reference source; reimport does not reset exposure")
            if candidate_id in s.runs:
                require(simulation is not None and geometry is not None, "SOURCE_UNAVAILABLE", "Current P09 source services required")
                run_id = s.runs[candidate_id]
                status = simulation.status(actor, geometry, run_id)
                require(status["freshness"] == "current" and from_run(simulation.dataset(actor, run_id)).content_sha256 == candidate_id,
                        "STALE_SOURCE", "Source study/geometry changed; preserve old receipt but create a current comparison")
            require(len(s.reports) < 16, "REPORT_LIMIT", "Local immutable assessment limit reached")
            value = compare(a, b, p)
            value.update(actor=actor, criteria=p.data, candidate=a.data, reference=b.data,
                         predeclared_in_this_session=True, predeclaration_scope="Server import ordering only; independent reviewer must establish off-platform exposure",
                         source_run_id=s.runs.get(candidate_id), current_source_at_assessment=True)
            report_id = digest(value)
            s.reports[report_id] = dumps(value).encode()
            return {"report_id": report_id, "report": json.loads(s.reports[report_id]), "canonical_json": s.reports[report_id].decode()}

    def report(self, actor: str, report_id: str, simulation: Any = None, geometry: Any = None) -> dict[str, Any]:
        with self.lock:
            s = self.session(actor)
            require(report_id in s.reports, "UNKNOWN_REPORT", "Receipt absent or owned by another actor")
            raw = s.reports[report_id]
            require(hashlib.sha256(raw).hexdigest() == report_id, "EVIDENCE_CORRUPTED", "Immutable receipt hash mismatch")
            record = json.loads(raw)
            freshness = "historical-geometry-evidence" if record["kind"] == "geometry" else "not-assessed"
            if record.get("source_run_id") and simulation is not None and geometry is not None:
                freshness = simulation.status(actor, geometry, record["source_run_id"])["freshness"]
            return {"report_id": report_id, "report": record, "canonical_json": raw.decode(), "freshness": freshness,
                    "review_intents": [json.loads(v) for v in s.reviews.get(report_id, ())]}

    def review(self, actor: str, report_id: str, note: str) -> dict[str, Any]:
        text(note, "review note")
        with self.lock:
            s = self.session(actor)
            self.report(actor, report_id)
            require(len(s.reviews.get(report_id, ())) < 8, "REVIEW_LIMIT", "Local review-intent limit reached")
            receipt = {"actor": actor, "report_sha256": report_id, "note": note, "kind": "review-intent-not-engineering-acceptance",
                       "independent_acceptance": False, "experimental_validation": False, "production_handoff": False}
            s.reviews[report_id] = (*s.reviews.get(report_id, ()), dumps(receipt).encode())
            return receipt

    def capture(self, actor: str, geometry: GeometryWorkbench, job_id: str, snapshot_id: str) -> dict[str, Any]:
        revision, candidate = geometry.accepted(actor, job_id, snapshot_id)
        qa = json.loads(candidate.evidence_json)
        key = "qa-step" if revision.settings["backend"] == "occt" else "qa-stl"
        observed = qa[key]
        artifact = candidate.record.artifacts[0]
        path = checked_file(candidate.directory, Path(artifact.storage_uri).name, artifact.sha256)
        data = {"kind": "geometry", "backend": revision.settings["backend"], "operation": revision.settings["operation"],
                "source_sha256": artifact.sha256, "source_artifact_sha256": artifact.source_artifact_sha256,
                "snapshot_id": snapshot_id, "frame_id": "world", "units": "m", "qa": observed,
                "evidence_sha256": hashlib.sha256(candidate.evidence_json.encode()).hexdigest(), "provenance": "accepted server-side native fixture"}
        return self.add_geometry(actor, data, path, artifact.sha256)

    def add_geometry(self, actor: str, data: dict[str, Any], path: Path, checksum: str) -> dict[str, Any]:
        with self.lock:
            s = self.session(actor)
            require(len(s.geometries) < 8, "GEOMETRY_LIMIT", "Local geometry comparison limit reached")
            key = digest(data)
            value = {"geometry_id": key, **data}
            s.geometries[key] = dumps(value).encode(); s.files[key] = (path, checksum)
            return value

    def compare_geometry(self, actor: str, left: str, right: str) -> dict[str, Any]:
        with self.lock:
            s = self.session(actor)
            require(left in s.geometries and right in s.geometries and left != right, "UNKNOWN_GEOMETRY", "Choose two distinct owned geometry captures")
            a, b = (json.loads(s.geometries[key]) for key in (left, right))
            for key in (left, right):
                path, checksum = s.files[key]
                checked_file(path.parent, path.name, checksum)
            require(a["operation"] == b["operation"] and a["frame_id"] == b["frame_id"] and a["units"] == b["units"], "GEOMETRY_MISMATCH", "Same fixed fixture, SI units and world frame required")
            require(a["source_sha256"] != b["source_sha256"], "SELF_COMPARISON", "Identical exported bytes are not independent comparison evidence")
            q, r = a["qa"], b["qa"]
            expected = FixtureReference(a["operation"]).volume_m3
            dv = abs(q["volume_m3"] - r["volume_m3"])/expected
            dc = math.dist(q["centroid_m"], r["centroid_m"])
            centroid_limit = q.get("centroid_limit_m", q.get("distance_limit_m")) + r.get("centroid_limit_m", r.get("distance_limit_m"))
            limit = q["relative_volume_limit"] + r["relative_volume_limit"]
            value = {"schema_version": "p10-assessment-v1", "kind": "geometry", "left": a, "right": b,
                "relative_volume_discrepancy": dv, "relative_volume_limit": limit, "centroid_discrepancy_m": dc, "centroid_limit_m": centroid_limit,
                "criteria_basis": "Sum of predeclared P07 fixture-specific independent QA bounds, via triangle inequality to the common analytic reference; not an arbitrary-design tolerance",
                "comparison_passed": q["pass"] and r["pass"] and dv <= limit and dc <= centroid_limit,
                "cross_kernel": {a["backend"], b["backend"]} == {"occt", "picogk"},
                "surface_distance_scope": "Per-operand bidirectional sampled distances to the common analytic reference retained in QA. Not direct pairwise or certified Hausdorff distance.",
                "uncertainty_scope": "Deterministic fixture-specific geometry approximation bounds; not a statistical uncertainty estimate",
                "execution": "completed", "experimental_validation": "not-performed", "engineering_review": "pending", "independent_acceptance": False, "production_handoff": False}
            require(len(s.reports) < 16, "REPORT_LIMIT", "Local report limit reached")
            report_id = digest(value); s.reports[report_id] = dumps(value).encode()
            return {"report_id": report_id, "report": json.loads(s.reports[report_id]), "canonical_json": s.reports[report_id].decode()}

    def import_step(self, actor: str, geometry: GeometryWorkbench, encoded: str, provenance: dict[str, Any]) -> dict[str, str]:
        fields(provenance, {"source", "author", "license"})
        for key, value in provenance.items():
            text(value, key)
        require(type(encoded) is str and 0 < len(encoded) <= 2 * 1024**2, "CAD_IMPORT_LIMIT", "Trusted local STEP import limit is 1.5MiB decoded")
        raw = base64.b64decode(encoded, validate=True)
        require(raw.startswith(b"ISO-10303-21;") and raw.rstrip().endswith(b"END-ISO-10303-21;"), "INVALID_STEP", "Complete trusted STEP required; no compressed archives")
        with self.lock:
            s = self.session(actor)
            require(len(s.imports) < 4 and len(s.geometries) + len(s.imports) < 8, "CAD_IMPORT_LIMIT", "Local bounded import history limit reached")
            require(self.slots.acquire(blocking=False), "QUEUE_FULL", "Two CAD import slots are occupied")
            job = "vv-cad-" + uuid.uuid4().hex
            def execute() -> dict[str, Any]:
                try:
                    directory = Path(tempfile.mkdtemp(prefix="p10-trusted-step-", dir=self.root))
                    path = directory / "import.step"
                    with path.open("xb") as stream:
                        stream.write(raw)
                    checksum = hashlib.sha256(raw).hexdigest()
                    qa = audit_step(path, FixtureReference("sphere"), reader=geometry.reader, supervisor=geometry.supervisor, job_id=job, tolerance_m=1e-6)
                    require(qa["pass"], "CAD_FIXTURE_MISMATCH", "This slice accepts only the fixed centred 10mm analytic sphere profile")
                    return self.add_geometry(actor, {"kind": "geometry", "backend": "external-step-gmsh-shared-occt", "operation": "sphere",
                        "source_sha256": checksum, "source_artifact_sha256": None, "snapshot_id": job, "frame_id": "world", "units": "m",
                        "qa": qa, "provenance": provenance, "evidence_sha256": digest(qa)}, path, checksum)
                finally:
                    self.slots.release()
            s.imports[job] = self.pool.submit(execute)
            return {"import_id": job}

    def close(self) -> None:
        self.pool.shutdown(wait=True)
