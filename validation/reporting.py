"""Reproducible immutable P09/P10 research reports, not signed engineering release."""
from __future__ import annotations

import hashlib
import io
import json
import threading
import zipfile
from dataclasses import dataclass, field
from html import escape
from pathlib import Path
from typing import Any

from knowledge.exporters.html_exporter import export_html
from knowledge.workspace.evidence_navigation import EvidenceNavigation, identifier
from simulation.contracts import StudySnapshot
from systems.contracts.geometry._wire import (
    GeometryContractError,
    digest,
    dumps,
    require,
)

RENDERER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


@dataclass
class ReportSession:
    reports: dict[str, bytes] = field(default_factory=dict)
    review_intents: dict[str, tuple[bytes, ...]] = field(default_factory=dict)


class EngineeringReports:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.sessions: dict[str, ReportSession] = {}

    def session(self, actor: str) -> ReportSession:
        with self.lock:
            if actor not in self.sessions:
                require(len(self.sessions) < 16, "SESSION_LIMIT", "Report preview actor limit reached")
                self.sessions[actor] = ReportSession()
            return self.sessions[actor]

    def context(self, actor: str) -> dict[str, Any]:
        with self.lock:
            return {"schema_version": "p11-report-context-v1", "report_ids": list(self.session(actor).reports),
                    "storage": "Bounded ephemeral preview; retain downloaded review packages before restart",
                    "independent_acceptance": False, "production_handoff": False}

    def create(self, actor: str, title: str, receipt_id: str, claim_ids: list[str], comparison: Any, simulation: Any, geometry: Any, navigation: EvidenceNavigation) -> dict[str, Any]:
        require(type(title) is str and 0 < len(title.strip()) <= 128 and "\0" not in title, "INVALID_TITLE", "Report title must contain 1–128 characters")
        require(type(claim_ids) is list and len(claim_ids) <= 8 and all(type(v) is str for v in claim_ids)
                and len(set(claim_ids)) == len(claim_ids), "INVALID_CLAIMS", "Select at most eight distinct existing claims")
        receipt = comparison.report(actor, identifier(receipt_id), simulation, geometry)
        record = receipt["report"]
        require(record["kind"] == "thermal" and record.get("source_run_id") and receipt["freshness"] == "current",
                "CURRENT_RUN_REQUIRED", "This report slice requires a current actual P09-backed P10 thermal receipt")
        require(simulation is not None and geometry is not None, "SOURCE_UNAVAILABLE", "Current study and geometry services required")
        source = simulation.dataset(actor, record["source_run_id"])
        require(digest(source) == record["candidate"]["provenance"]["source_sha256"], "PROVENANCE_MISMATCH", "P10 candidate must bind the exact P09 dataset")
        study = StudySnapshot.from_json(dumps(source["study"]))
        require(study.content_sha256 == source["study_id"], "PROVENANCE_MISMATCH", "Study identity must match the immutable run")
        current_methods = StudySnapshot(study.handoff, study.settings)
        require(current_methods.model_sha256 == study.model_sha256 and current_methods.solver_sha256 == study.solver_sha256,
                "PROVENANCE_MISMATCH", "Model/solver files changed; create a new verified study rather than label historical methods current")
        run = simulation.owned(actor, record["source_run_id"])
        revision, candidate = geometry.accepted(actor, run.geometry_job, study.handoff.geometry_snapshot_id)
        require(revision.snapshot.content_sha256 == study.handoff.geometry_snapshot_id, "PROVENANCE_MISMATCH", "Geometry revision mismatch")
        claims = [navigation.claim(identifier(key)) for key in sorted(claim_ids)]
        require(all(c["claim"]["source"] is not None and c["claim"]["source"]["original_available"] for c in claims),
                "SOURCE_UNAVAILABLE", "Attached claims need hash-checked originals; omit missing sources rather than fabricate evidence")
        value = {"schema_version": "p11-engineering-report-v1", "title": title.strip(), "actor": actor,
                 "project_id": "p07-software-fixtures", "scope": "Steady spherical research-tool evidence; not engine qualification",
                 "comparison_receipt_id": receipt_id, "comparison_canonical_json": receipt["canonical_json"],
                 "input_revision": source["study_id"], "run_id": source["run_id"], "geometry_job_id": run.geometry_job,
                 "geometry_snapshot_id": study.handoff.geometry_snapshot_id, "geometry_artifact": json.loads(study.handoff.artifact.to_json()),
                 "geometry_qa_canonical_json": candidate.evidence_json, "geometry_qa_sha256": study.handoff.integrity_sha256,
                 "dataset_canonical_json": dumps(source), "dataset_sha256": digest(source), "claims": claims,
                 "claim_scope": "Supplementary knowledge; attachment does not establish model-use applicability",
                 "status": {"execution": source["execution_status"], "numerical_convergence": source["numerical_convergence"],
                            "conservation_passed": source["conservation_checks"]["passed"], "solution_verification": source["solution_verification"],
                            "discrepancy_criteria_passed": record["error_criteria_passed"], "output_uncertainty": record["combined_standard_uncertainty_k"],
                            "experimental_validation": record["experimental_validation"], "simulation_experimental_validation": source["experimental_validation"],
                            "engineering_review": "pending", "independent_acceptance": False, "production_handoff": False},
                 "comparison_review_intents_at_creation": receipt["review_intents"],
                 "reproducibility": {"render_version": "p11-render-v1", "deterministic": "Identical immutable inputs and title yield identical JSON/Markdown/HTML/ZIP bytes",
                                     "renderer_source": {"path": "validation/reporting.py", "sha256": RENDERER_SHA256},
                                     "source_refs": source["source_refs"], "native_distribution": "Native binaries and geometry files are not bundled; exact IDs/hashes and QA are retained",
                                     "full_solver_reexecution": "Requires the separately qualified local runtime and exact model/solver source files"},
                 "limitations": ["Research fixture only; not CFD/FEA or rocket-engine physical qualification", "Output uncertainty does not constitute a full validation budget",
                                 "No signed independent reviewer acceptance; review intents are not signatures", "Source checksums authenticate bytes, not authorship or applicability"]}
        raw = dumps(value).encode(); require(len(raw) <= 2*1024**2, "REPORT_LIMIT", "Report exceeds 2MiB bounded preview")
        require(hashlib.sha256(receipt["canonical_json"].encode()).hexdigest() == receipt_id, "CORRUPT_RECEIPT", "Comparison receipt bytes do not match ID")
        require(hashlib.sha256(candidate.evidence_json.encode()).hexdigest() == study.handoff.integrity_sha256, "PROVENANCE_MISMATCH", "Geometry QA checksum mismatch")
        report_id = hashlib.sha256(raw).hexdigest()
        with self.lock:
            s = self.session(actor)
            require(report_id in s.reports or len(s.reports) < 16, "REPORT_LIMIT", "Report history is limited to 16 immutable records")
            s.reports.setdefault(report_id, raw)
        return self.get(actor, report_id, comparison, simulation, geometry, navigation)

    def get(self, actor: str, report_id: str, comparison: Any = None, simulation: Any = None, geometry: Any = None, navigation: EvidenceNavigation | None = None) -> dict[str, Any]:
        identifier(report_id)
        with self.lock:
            s = self.session(actor); require(report_id in s.reports, "REPORT_UNAVAILABLE", "Report absent or owned by another actor")
            raw = s.reports[report_id]; require(hashlib.sha256(raw).hexdigest() == report_id, "CORRUPT_REPORT", "Immutable report checksum mismatch")
            value = json.loads(raw); intents = [json.loads(v) for v in s.review_intents.get(report_id, ())]
        freshness = "not-assessed"
        if comparison is not None:
            try:
                freshness = comparison.report(actor, value["comparison_receipt_id"], simulation, geometry)["freshness"]
                dataset = json.loads(value["dataset_canonical_json"])
                study = StudySnapshot.from_json(dumps(dataset["study"]))
                current_methods = StudySnapshot(study.handoff, study.settings)
                if current_methods.model_sha256 != study.model_sha256 or current_methods.solver_sha256 != study.solver_sha256:
                    freshness = "stale"
                if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != value["reproducibility"]["renderer_source"]["sha256"]:
                    freshness = "stale"
                if navigation is not None and any(navigation.claim(c["claim"]["claim_id"])["evidence_sha256"] != c["evidence_sha256"] for c in value["claims"]):
                    freshness = "stale"
            except (GeometryContractError, ValueError, KeyError, OSError, RuntimeError):
                freshness = "source-unavailable"
        return {"report_id": report_id, "report": value, "canonical_json": raw.decode(), "freshness": freshness, "review_intents": intents}

    def review(self, actor: str, report_id: str, note: str) -> dict[str, Any]:
        require(type(note) is str and 0 < len(note.strip()) <= 1024 and "\0" not in note, "INVALID_REVIEW", "Bounded nonempty review note required")
        with self.lock:
            self.get(actor, report_id)
            s = self.session(actor); previous = s.review_intents.get(report_id, ())
            require(len(previous) < 8, "REVIEW_LIMIT", "Preview review-intent limit reached")
            value = {"actor": actor, "report_id": report_id, "note": note, "kind": "review-intent-not-independent-acceptance", "independent_acceptance": False, "production_handoff": False}
            s.review_intents[report_id] = (*previous, dumps(value).encode())
            return value

    def files(self, actor: str, report_id: str) -> dict[str, bytes]:
        receipt = self.get(actor, report_id); r = receipt["report"]
        require(r["reproducibility"]["renderer_source"]["sha256"] == RENDERER_SHA256, "RENDERER_MISMATCH", "Use the exact recorded renderer; do not silently rerender historical evidence")
        comparison = json.loads(r["comparison_canonical_json"])
        dataset = json.loads(r["dataset_canonical_json"])
        sections = {
            "Report identity and use": {"Title": r["title"], "Scope": r["scope"], "Project": r["project_id"], "Report SHA-256": report_id},
            "Scientific status": r["status"],
            "Exact input lineage": {"study_id": r["input_revision"], "run_id": r["run_id"], "geometry_snapshot_id": r["geometry_snapshot_id"],
                "artifact_id": r["geometry_artifact"]["artifact_id"], "geometry_source_sha256": r["geometry_artifact"]["source_artifact_sha256"],
                "geometry_export_sha256": r["geometry_artifact"]["sha256"], "dataset_sha256": r["dataset_sha256"], "comparison_receipt_id": r["comparison_receipt_id"]},
            "Method and SI operating conditions": {"model": dataset["study"]["model"], "settings": dataset["study"]["settings"],
                "conditions": comparison["candidate"]["conditions"], "coordinate_unit": comparison["coordinate_unit"], "value_unit": comparison["value_unit"]},
            "Discrepancy and predeclared criteria": {"metrics": comparison["metrics"], "criteria": comparison["criteria"],
                "output_uncertainty": comparison["combined_standard_uncertainty_k"], "uncertainty_scope": comparison["uncertainty_scope"]},
            "Sources and supplementary knowledge": {"model_and_solver": r["reproducibility"]["source_refs"], "knowledge_claim_ids": [c["claim"]["claim_id"] for c in r["claims"]],
                "applicability": r["claim_scope"], "assumptions": [c["claim"]["assumptions"] for c in r["claims"]]},
            "Review and reproducibility limits": {"independent_acceptance": "PENDING", "production_handoff": "BLOCKED", "limits": r["limitations"],
                "full_solver_reexecution": r["reproducibility"]["full_solver_reexecution"], "freshness": "Immutable historical snapshot; consult the running server for current source freshness"},
        }
        # Render JSON blocks, not untrusted Markdown/HTML. Exact payload is separate.
        markdown = "# COSMOS research evidence report\n\n"
        html = '<!doctype html><html lang="en"><meta charset="utf-8"><title>COSMOS research evidence report</title><body><h1>COSMOS research evidence report</h1>'
        for heading, values in sections.items():
            raw = json.dumps(values, indent=2, ensure_ascii=True)
            markdown += "## " + heading + "\n\n```json\n" + raw + "\n```\n\n"
            html += "<section><h2>" + escape(heading) + "</h2><pre>" + escape(raw) + "</pre></section>"
        html += "<details><summary>Exact immutable record</summary>" + export_html({"title": r["title"], "provenance": report_id, "canonical_json": receipt["canonical_json"]}) + "</details></body></html>\n"
        return {"report.json": receipt["canonical_json"].encode(), "report.md": markdown.encode(), "report.html": html.encode()}

    def package(self, actor: str, report_id: str) -> bytes:
        files = self.files(actor, report_id)
        manifest = {"schema_version": "p11-package-v1", "report_id": report_id, "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()},
                    "scope": "Offline immutable research review snapshot; freshness requires the running server", "independent_acceptance": False, "production_handoff": False}
        files["manifest.json"] = dumps(manifest).encode()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(files):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0)); info.external_attr = 0o100644 << 16
                archive.writestr(info, files[name])
        require(len(stream.getvalue()) <= 8*1024**2, "REPORT_LIMIT", "Review package exceeds 8MiB")
        return stream.getvalue()
