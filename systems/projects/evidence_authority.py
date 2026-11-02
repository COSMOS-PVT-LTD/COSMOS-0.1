"""Durable adapters for existing P10/P11 software evidence, not new physics.

One bounded comparison ledger per owning project preserves first exposure and
criteria ordering across users/restarts. Independent assessment/report objects
depend only on their actual inputs, not unrelated later ledger activity.
"""
from __future__ import annotations

import base64
import json
from collections.abc import Callable
from contextlib import AbstractContextManager
from dataclasses import dataclass
from hashlib import sha256
from types import SimpleNamespace
from typing import Any

from simulation.contracts import StudySnapshot
from systems.contracts.geometry._wire import digest, require
from systems.geometry.retained_source import RetainedFixture, retained_fixture
from systems.geometry.source_contract import GeometrySource
from systems.persistence.job_repository import JobRepository, JobState
from systems.persistence.project_repository import (
    Dependency,
    ProjectRepository,
    RecordPayload,
)
from systems.projects.authority import (
    AccessDenied,
    Head,
    InvalidRecord,
    Principal,
    ProjectStoreError,
    RecordNotFound,
    SavedSnapshot,
)
from systems.projects.study_authority import DOMAIN as STUDY_DOMAIN
from systems.projects.study_authority import decode_study
from validation.contracts import Criteria, ThermalDataset
from validation.reporting import RENDERER_SHA256, EngineeringReports
from validation.workbench import ComparisonWorkbench, Session

LEDGER = "comparison-ledger"
LEDGER_ID = "thermal-evidence"
ASSESSMENT = "comparison-assessment"
REPORT = "engineering-report"
REVIEW = "comparison-review"
NAMESPACE = "p07-software-fixtures"


def payload(value: dict[str, Any], kind: str) -> RecordPayload:
    return RecordPayload.from_mapping(value, "cosmos." + kind + ".v1", source_namespace=NAMESPACE)


def decode(source: SavedSnapshot, domain: str) -> dict[str, Any]:
    if source.domain != domain or source.schema_id != "cosmos." + domain + ".v1" or source.source_namespace != NAMESPACE:
        raise InvalidRecord("Unsupported exact managed evidence contract.")
    return json.loads(source.payload)


def pack_session(s: Session, run_bindings: dict[str, str], result: dict[str, Any]) -> dict[str, Any]:
    return {"sequence": s.sequence, "datasets": {key: [d.canonical.decode(), order] for key, (d, order) in s.datasets.items()},
        "policies": {key: [p.canonical.decode(), order] for key, (p, order) in s.policies.items()},
        "first_seen": s.first_seen, "runs": s.runs, "candidate": s.candidate, "run_bindings": run_bindings,
        "last_result": result, "ordering_scope": "Owning-project server first import only; off-platform exposure is not established"}


def unpack_session(value: dict[str, Any]) -> Session:
    s = Session(sequence=value["sequence"], first_seen=value["first_seen"], runs=value["runs"], candidate=value["candidate"])
    require(type(s.sequence) is int and 0 <= s.sequence < 2**53 and len(value["datasets"]) <= 16 and len(value["policies"]) <= 16,
            "EVIDENCE_LIMIT", "Stored comparison ledger exceeds its supported bounded contract")
    for key, (raw, order) in value["datasets"].items():
        d = ThermalDataset.parse(json.loads(raw))
        require(d.content_sha256 == key and d.canonical.decode() == raw and 0 < order <= s.sequence,
                "CORRUPT_DATASET", "Original dataset identity/order changed")
        s.datasets[key] = (d, order)
    for key, (raw, order) in value["policies"].items():
        p = Criteria.parse(json.loads(raw))
        require(p.content_sha256 == key and p.canonical.decode() == raw and 0 < order <= s.sequence,
                "CORRUPT_CRITERIA", "Original criteria identity/order changed")
        s.policies[key] = (p, order)
    require(all(type(seq) is int and 0 < seq <= s.sequence for seq in s.first_seen.values())
            and set(s.runs) <= set(s.datasets) and (s.candidate is None or s.candidate in s.datasets),
            "CORRUPT_ORDERING", "Stored first-exposure/run index is inconsistent")
    return s


@dataclass(frozen=True)
class CapturedRun:
    actor: str
    source: SavedSnapshot
    wrapper_id: str
    native_id: str
    raw: bytes
    original_status: dict[str, Any]
    geometry_job: str

    def dataset(self, actor: str, run_id: str) -> dict[str, Any]:
        require(actor == self.actor and run_id == self.native_id, "SOURCE_SCOPE", "Exact owning run required")
        return json.loads(self.raw)

    def status(self, actor: str, geometry: Any, run_id: str) -> dict[str, Any]:
        self.dataset(actor, run_id)
        return self.original_status

    def owned(self, actor: str, run_id: str) -> Any:
        self.dataset(actor, run_id)
        return SimpleNamespace(geometry_job=self.geometry_job)


class ManagedEvidence:
    def __init__(self, repository: ProjectRepository, jobs: JobRepository,
                 materialize: Callable[[RetainedFixture], AbstractContextManager[GeometrySource]],
                 claim_reader: Callable[[Principal, str], tuple[dict[str, Any], bytes]] | None = None) -> None:
        self.repository, self.jobs, self.materialize, self.claim_reader = repository, jobs, materialize, claim_reader

    def run(self, actor: Principal, project_id: str, job_id: str) -> CapturedRun:
        job = self.jobs.get(actor, project_id, job_id)
        require(job.domain == STUDY_DOMAIN and job.state is JobState.COMPLETED and job.selected and job.current_input,
                "CURRENT_RUN_REQUIRED", "Choose an exact current selected completed owning-project run")
        source = self.repository.get_snapshot(actor, project_id, domain=job.domain, object_id=job.object_id, commit_id=job.source_commit_id)
        study = decode_study(source)
        require(StudySnapshot(study.study.handoff, study.study.settings).to_json() == study.study.to_json(),
                "STALE_METHODS", "Original model/solver source is no longer current")
        raw = self.jobs.blob(actor, project_id, job_id, "dataset.json")
        wrapper = json.loads(job.payload)
        status = json.loads(wrapper["worker_status_json"])
        data = json.loads(raw)
        require(data["study_id"] == study.study.content_sha256 and data["run_id"] == wrapper["native_run_id"]
                and status["dataset_sha256"] == sha256(raw).hexdigest() and status["result"] == data
                and status["freshness"] == "current" and status["geometry_integrity_current"],
                "PROVENANCE_MISMATCH", "Original run/study/status/dataset identities disagree")
        return CapturedRun(actor.user_id, source, job_id, wrapper["native_run_id"], raw, status, study.geometry_job_id)

    def ledger(self, actor: Principal, project_id: str) -> SavedSnapshot:
        return self.repository.get_snapshot(actor, project_id, domain=LEDGER, object_id=LEDGER_ID)

    def command(self, actor: Principal, project_id: str, action: str, value: dict[str, Any], *, expected: Head,
                operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        try:
            before = self.ledger(actor, project_id)
        except RecordNotFound:
            before = None
        worker = ComparisonWorkbench(self._unused_root())
        try:
            bindings: dict[str, str] = {}
            deps: tuple[Dependency, ...] = ()
            if before is not None:
                saved = decode(before, LEDGER)
                worker.sessions[actor.user_id] = unpack_session(saved)
                bindings = saved["run_bindings"]
                deps = self.repository.dependencies(actor, project_id, before.commit_id)
            if action == "declare":
                result = worker.declare(actor.user_id, value["criteria"])
            elif action == "import":
                result = worker.imported(actor.user_id, value["dataset"])
            elif action == "reference":
                result = worker.reference(actor.user_id, value["candidate_id"])
            elif action == "use-run":
                run = self.run(actor, project_id, value["run_job_id"])
                result = worker.add(actor.user_id, self._candidate(run), candidate=True, run_id=run.native_id)
                bindings[result["dataset_id"]] = run.wrapper_id
                dep = Dependency("run-" + run.wrapper_id, run.source.commit_id, run.wrapper_id)
                deps = tuple({d.relation: d for d in (*deps, dep)}.values())
            else:
                raise InvalidRecord("Unsupported comparison ledger command.")
            return self.repository.save_snapshot(actor, project_id, domain=LEDGER, object_id=LEDGER_ID,
                input_revision=before.input_revision + 1 if before else 0, payload=payload(pack_session(worker.session(actor.user_id), bindings, result), LEDGER),
                expected=expected, operation_id=operation_id, command_hash=command_hash, dependencies=deps)
        finally:
            worker.close()

    @staticmethod
    def _unused_root() -> Any:
        # Thermal ledger commands do not use ComparisonWorkbench's CAD-import
        # filesystem API. No directory is created by the adapter.
        from pathlib import Path
        return Path(".")

    @staticmethod
    def _candidate(run: CapturedRun) -> ThermalDataset:
        from validation.benchmarks import from_run
        return from_run(json.loads(run.raw))

    def assess(self, actor: Principal, project_id: str, value: dict[str, Any], *, expected: Head,
               operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        source = self.ledger(actor, project_id)
        if source.head != expected:
            from systems.projects.authority import HeadConflict
            raise HeadConflict(source.head)
        state = decode(source, LEDGER)
        require(value["candidate_id"] in state["run_bindings"], "CURRENT_RUN_REQUIRED", "Managed assessment requires a real retained benchmark run")
        run = self.run(actor, project_id, state["run_bindings"][value["candidate_id"]])
        worker = ComparisonWorkbench(self._unused_root())
        try:
            worker.sessions[actor.user_id] = unpack_session(state)
            fixture = retained_fixture(self.repository, self.jobs, actor, project_id, run.geometry_job)
            with self.materialize(fixture) as geometry:
                result = worker.assess(actor.user_id, value["candidate_id"], value["reference_id"], value["criteria_id"], run, geometry)
        finally:
            worker.close()
        return self.repository.save_snapshot(actor, project_id, domain=ASSESSMENT, object_id=result["report_id"], input_revision=0,
            payload=payload({"canonical_json": result["canonical_json"], "run_job_id": run.wrapper_id, "ledger_commit_id": source.commit_id,
                "predeclaration_scope": state["ordering_scope"]}, ASSESSMENT), expected=Head.absent(), operation_id=operation_id,
            command_hash=command_hash, source_commit_id=source.commit_id, dependencies=(Dependency("run", run.source.commit_id, run.wrapper_id),))

    def comparison(self, actor: Principal, project_id: str, assessment_id: str) -> tuple[SavedSnapshot, Any]:
        saved = self.repository.get_snapshot(actor, project_id, domain=ASSESSMENT, object_id=assessment_id)
        value = decode(saved, ASSESSMENT)
        raw = value["canonical_json"]
        require(sha256(raw.encode()).hexdigest() == assessment_id, "CORRUPT_RECEIPT", "Exact P10 receipt identity changed")
        current = self.repository.dependencies_current(actor, project_id, saved.commit_id)
        if current:
            try:
                self.run(actor, project_id, value["run_job_id"])
            except (ValueError, KeyError, OSError, RuntimeError, ProjectStoreError):
                current = False
        try:
            notes = decode(self.repository.get_snapshot(actor, project_id, domain=REVIEW, object_id=assessment_id), REVIEW)["review_intents"]
        except RecordNotFound:
            notes = []
        class Source:
            def report(self, owner: str, key: str, *_args: Any) -> dict[str, Any]:
                require(owner == actor.user_id and key == assessment_id, "SOURCE_SCOPE", "Exact owned comparison required")
                return {"report_id": key, "report": json.loads(raw), "canonical_json": raw,
                        "freshness": "current" if current else "stale", "review_intents": [json.loads(note) for note in notes]}
        return saved, Source()

    def review_comparison(self, actor: Principal, project_id: str, assessment_id: str, note: str, *, expected: Head,
                          operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        assessment, comparison = self.comparison(actor, project_id, assessment_id)
        prior = None if expected == Head.absent() else self.repository.get_snapshot(actor, project_id, domain=REVIEW, object_id=assessment_id)
        worker = ComparisonWorkbench(self._unused_root())
        try:
            s = worker.session(actor.user_id)
            s.reports[assessment_id] = comparison.report(actor.user_id, assessment_id)["canonical_json"].encode()
            s.reviews[assessment_id] = tuple(raw.encode() for raw in decode(prior, REVIEW)["review_intents"]) if prior else ()
            worker.review(actor.user_id, assessment_id, note)
            value = {"review_intents": [raw.decode() for raw in s.reviews[assessment_id]], "assessment_id": assessment_id}
        finally:
            worker.close()
        return self.repository.save_snapshot(actor, project_id, domain=REVIEW, object_id=assessment_id,
            input_revision=0 if prior is None else prior.input_revision + 1, payload=payload(value, REVIEW), expected=expected,
            operation_id=operation_id, command_hash=command_hash, dependencies=(Dependency("assessment", assessment.commit_id),))

    def create_report(self, actor: Principal, project_id: str, object_id: str, value: dict[str, Any], *, expected: Head,
                      operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        assessment, comparison = self.comparison(actor, project_id, value["assessment_id"])
        bound = decode(assessment, ASSESSMENT)
        run = self.run(actor, project_id, bound["run_job_id"])
        fixture = retained_fixture(self.repository, self.jobs, actor, project_id, run.geometry_job)
        claims: dict[str, dict[str, Any]] = {}
        originals: dict[str, Any] = {}
        ids = value["claim_ids"]
        require(type(ids) is list and len(ids) <= 8 and all(type(key) is str for key in ids) and len(set(ids)) == len(ids),
                "INVALID_CLAIMS", "Choose at most eight distinct existing claims")
        for key in ids:
            require(self.claim_reader is not None, "SOURCE_UNAVAILABLE", "Authenticated knowledge original reader required")
            assert self.claim_reader is not None
            claim, original = self.claim_reader(actor, key)
            if claim["claim"]["source"] is None or claim["claim"]["source"]["project_id"] not in {project_id, "GLOBAL"}:
                raise AccessDenied("Knowledge originals must be GLOBAL or explicitly bound to this owning project.")
            require(len(original) <= 4 * 1024**2 and claim["claim"]["source"]["sha256"] == sha256(original).hexdigest()
                    and digest(claim["claim"]) == claim["evidence_sha256"], "SOURCE_CORRUPT", "Claim needs its hash-checked original, not an excerpt")
            claims[key] = claim
            originals[key] = {"sha256": sha256(original).hexdigest(), "base64": base64.b64encode(original).decode()}
        class Navigation:
            def claim(self, key: str) -> dict[str, Any]:
                return claims[key]
        reports = EngineeringReports()
        navigation: Any = Navigation()
        with self.materialize(fixture) as geometry:
            result = reports.create(actor.user_id, value["title"], value["assessment_id"], ids, comparison, run, geometry, navigation)
        report_id = result["report_id"]
        files = reports.files(actor.user_id, report_id)
        files["package.zip"] = reports.package(actor.user_id, report_id)
        captured = {"report_id": report_id, "canonical_json": result["canonical_json"], "assessment_id": value["assessment_id"],
                    "claim_originals": originals, "files": {name: {"sha256": sha256(raw).hexdigest(), "base64": base64.b64encode(raw).decode()}
                        for name, raw in files.items()}, "review_intents": []}
        revision = 0 if expected == Head.absent() else self.repository.get_snapshot(actor, project_id, domain=REPORT, object_id=object_id).input_revision + 1
        return self.repository.save_snapshot(actor, project_id, domain=REPORT, object_id=object_id, input_revision=revision,
            payload=payload(captured, REPORT), expected=expected, operation_id=operation_id, command_hash=command_hash,
            dependencies=(Dependency("assessment", assessment.commit_id), Dependency("run", run.source.commit_id, run.wrapper_id)))

    def review(self, actor: Principal, source: SavedSnapshot, note: str, *, expected: Head, operation_id: str, command_hash: str) -> SavedSnapshot:
        replay = self.repository.resolve_command(actor, source.project_id, operation_id=operation_id, command_hash=command_hash)
        if replay is not None:
            return replay
        if source.head != expected:
            from systems.projects.authority import HeadConflict
            raise HeadConflict(self.repository.get_snapshot(actor, source.project_id, domain=REPORT, object_id=source.object_id).head)
        value = decode(source, REPORT)
        require(type(note) is str and 0 < len(note.strip()) <= 1024 and "\0" not in note and len(value["review_intents"]) < 8,
                "INVALID_REVIEW", "At most eight bounded nonempty review intents; no engineering signatures")
        value["review_intents"].append({"actor": actor.user_id, "report_id": value["report_id"], "note": note,
            "kind": "review-intent-not-independent-acceptance", "independent_acceptance": False, "production_handoff": False})
        return self.repository.save_snapshot(actor, source.project_id, domain=REPORT, object_id=source.object_id, input_revision=source.input_revision,
            payload=payload(value, REPORT), expected=expected, operation_id=operation_id, command_hash=command_hash,
            dependencies=self.repository.dependencies(actor, source.project_id, source.commit_id))

    def report_current(self, actor: Principal, source: SavedSnapshot) -> bool:
        if not self.repository.dependencies_current(actor, source.project_id, source.commit_id):
            return False
        value = decode(source, REPORT)
        record = json.loads(value["canonical_json"])
        if record["reproducibility"]["renderer_source"]["sha256"] != RENDERER_SHA256:
            return False
        try:
            _, comparison = self.comparison(actor, source.project_id, value["assessment_id"])
            if comparison.report(actor.user_id, value["assessment_id"])["freshness"] != "current":
                return False
            for claim in record["claims"]:
                if self.claim_reader is None:
                    return False
                current, raw = self.claim_reader(actor, claim["claim"]["claim_id"])
                if current["evidence_sha256"] != claim["evidence_sha256"] or sha256(raw).hexdigest() != claim["claim"]["source"]["sha256"]:
                    return False
            return True
        except (ValueError, KeyError, OSError, RuntimeError, ProjectStoreError):
            return False

    @staticmethod
    def report_file(source: SavedSnapshot, name: str) -> bytes:
        value = decode(source, REPORT)
        require(name in {"report.json", "report.md", "report.html", "package.zip"}, "INVALID_EXPORT", "Exact retained report file required")
        item = value["files"][name]
        raw = base64.b64decode(item["base64"], validate=True)
        require(sha256(raw).hexdigest() == item["sha256"], "CORRUPT_EXPORT", "Retained rendered bytes changed")
        return raw
