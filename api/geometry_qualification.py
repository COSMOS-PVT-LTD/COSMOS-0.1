"""Project-scoped R08 commands/downloads. No geometric computations in API."""

import json
import os
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from api.geometry_projects import BinarySource, job_dto
from systems.contracts.geometry._wire import require
from systems.geometry.qualification import (
    CHECKS,
    INPUTS,
    POLICIES,
    REVIEWS,
    ROOT,
    GeometryQualification,
    QualificationRuntime,
    methods,
)
from systems.geometry.qualification_policy import exact
from systems.projects.authority import Head, RecordNotFound

RUNTIME_SCHEMA = "cosmos.geometry-qualification-runtime.v1"


def configuration(path):
    require(
        path is not None,
        "R08_RUNTIME",
        "Explicit separately qualified R08 runtime required; no automatic native admission",
    )
    path = Path(path)
    require(
        path.is_absolute()
        and path.is_file()
        and not path.is_symlink()
        and path.stat().st_size < 1024**2,
        "R08_RUNTIME",
        "Bounded private R08 manifest required",
    )
    cfg = json.loads(path.read_bytes())
    exact(
        cfg, {"schema", "python", "sha256", "receipt", "receipt_sha256"}, "R08 runtime"
    )
    python = ROOT / ".venv-release-p12/bin/python"
    require(
        cfg["schema"] == RUNTIME_SCHEMA
        and type(cfg["sha256"]) is dict
        and cfg["python"] == str(python)
        and methods().items() <= cfg["sha256"].items(),
        "R08_RUNTIME",
        "Exact current source/runtime qualification required",
    )
    require(
        str(python.resolve()) in cfg["sha256"]
        and str(python.parent.parent / "pyvenv.cfg") in cfg["sha256"],
        "R08_RUNTIME",
        "Pinned worker interpreter target/venv required",
    )
    for name, digest in cfg["sha256"].items():
        file = Path(name) if Path(name).is_absolute() else ROOT / name
        require(
            file.is_file()
            and not file.is_symlink()
            and sha256(file.read_bytes()).hexdigest() == digest,
            "R08_RUNTIME_CHANGED",
            "R08 method/runtime bytes changed; qualify new evidence, do not reseal history",
        )
    receipt = Path(cfg["receipt"])
    require(
        receipt.is_absolute()
        and receipt.is_file()
        and not receipt.is_symlink()
        and sha256(receipt.read_bytes()).hexdigest() == cfg["receipt_sha256"],
        "R08_RUNTIME",
        "Exact R08 qualification receipt required",
    )
    proof = json.loads(receipt.read_bytes())
    require(
        type(proof) is dict, "R08_RUNTIME", "Structured qualification receipt required"
    )
    require(
        proof.get("method_sources") == methods()
        and proof.get("sha256") == cfg["sha256"]
        and proof.get("physical_validation") == "NOT_PERFORMED",
        "R08_RUNTIME",
        "Current source-bound software evidence required",
    )
    for role, minimum in (("unit", 10), ("native", 1), ("http", 1), ("families", 22)):
        report = proof.get("reports", {}).get(role, {})
        require(
            report.get("tests", 0) >= minimum
            and all(report.get(k) == 0 for k in ("failures", "errors", "skipped")),
            "R08_RUNTIME",
            "Passing executed unskipped R08 unit/native/HTTP/family reports required",
        )
        file = Path(report["path"])
        require(
            file.is_absolute()
            and file.is_file()
            and sha256(file.read_bytes()).hexdigest() == report["sha256"],
            "R08_RUNTIME",
            "Qualification report changed",
        )
    return cfg


class GeometryQualificationAPI:
    def __init__(self, repository, jobs, components, pico, resolve_actor):
        self.path = os.environ.get("COSMOS_GEOMETRY_QUALIFICATION_CONFIG")
        self.runtime = None

        def runtime():
            if self.runtime is None:
                self.runtime = QualificationRuntime(lambda: configuration(self.path))
            return self.runtime

        self.service = GeometryQualification(
            repository, jobs, components, pico, resolve_actor, runtime
        )

    def close(self):
        self.service.close()
        if self.runtime:
            self.runtime.close()

    def saved(self, actor, snapshot):
        return {
            "ok": True,
            "authority": {
                "object_id": snapshot.object_id,
                "commit_id": snapshot.commit_id,
                "head": asdict(snapshot.head),
            },
            "record": json.loads(snapshot.payload),
            "upstream_current": self.service.current_policy(actor, snapshot)
            if snapshot.domain == POLICIES
            else self.service.repository.dependencies_current(
                actor, snapshot.project_id, snapshot.commit_id
            ),
            "physical_validation": "NOT_PERFORMED",
        }

    def job(self, actor, project, job):
        value = job_dto(job)
        require(job.domain == INPUTS, "R08_SOURCE", "Exact R08 attempt required")
        if job.state.value == "COMPLETED":
            _, _, report, _, current = self.service.report(actor, project, job.job_id)
            value.update(
                report=report,
                upstream_current=current,
                engineering_acceptance="AWAITING_INDEPENDENT_REVIEW",
                required_review_checks=sorted(CHECKS),
            )
        return value

    def handle(self, actor, method, project, parts, query, body):
        s = self.service
        repo = s.repository
        jobs = s.jobs
        repo.get_project(actor, project)
        require(
            method in {"GET", "POST"},
            "R08_METHOD",
            "Only explicit GET/POST R08 commands supported",
        )
        require(
            set(query) <= ({"limit", "after", "before"} if method == "GET" else set())
            and all(len(v) == 1 for v in query.values()),
            "R08_QUERY",
            "No source/tolerance/identity query overrides",
        )
        checksum = sha256(
            json.dumps(
                {"project": project, "parts": parts, "body": body},
                sort_keys=True,
                allow_nan=False,
            ).encode()
        ).hexdigest()
        if parts == ["capabilities"] and method == "GET":
            try:
                configuration(self.path)
                enabled = True
                reason = "Current separately qualified software runtime"
            except (OSError, ValueError, KeyError, TypeError) as error:
                enabled = False
                reason = str(error)
            return {
                "ok": True,
                "runtime_configured": enabled,
                "diagnostic": reason,
                "policy_creation": True,
                "maximum_samples_per_part": 2048,
                "maximum_critical_features": 256,
                "requires_predeclaration": True,
                "requires_independent_reviewer": True,
                "scope": "Sampled geometry-analysis preparation only; no certified Hausdorff/minimum thickness/self-intersection, volume mesh, manufacturing or physical approval",
            }
        if parts == ["policies"]:
            if method == "POST":
                return self.saved(actor, s.save_policy(actor, project, body, checksum))
            return {
                "ok": True,
                "records": [
                    asdict(v)
                    for v in repo.list_objects(
                        actor,
                        project,
                        domain=POLICIES,
                        limit=int(query.get("limit", ["20"])[0]),
                        after_id=query.get("after", [""])[0],
                    )
                ],
            }
        if len(parts) == 2 and parts[0] in {"policies", "reviews"} and method == "GET":
            return self.saved(
                actor,
                repo.get_snapshot(
                    actor,
                    project,
                    domain=POLICIES if parts[0] == "policies" else REVIEWS,
                    object_id=parts[1],
                ),
            )
        if parts == ["evaluate"] and method == "POST":
            return self.job(actor, project, s.start(actor, project, body, checksum))
        if parts == ["jobs"] and method == "GET":
            rows = jobs.list_ids(
                actor,
                project,
                domain=INPUTS,
                limit=int(query.get("limit", ["20"])[0]),
                before=int(query["before"][0]) if "before" in query else None,
            )
            return {
                "ok": True,
                "attempts": [
                    {
                        **job_dto(jobs.get(actor, project, j), detail=False),
                        "detail_required": True,
                        "qualification_currentness": "RECHECK_ON_DETAIL_OR_EXPORT",
                    }
                    for _, j in rows
                ],
            }
        if len(parts) >= 2 and parts[0] == "jobs":
            job = jobs.get(actor, project, parts[1])
            require(job.domain == INPUTS, "R08_SOURCE", "Exact R08 attempt required")
            if len(parts) == 2 and method == "GET":
                return self.job(actor, project, job)
            if parts[2:] == ["qualification.json"] and method == "GET":
                _, _, _, raw, _ = s.report(actor, project, job.job_id)
                return BinarySource(
                    "unreviewed-geometry-qualification.json",
                    raw,
                    sha256(raw).hexdigest(),
                )
            if parts[2:] == ["cancel"] and method == "POST":
                exact(body, {"expected", "operation_id"}, "cancel command")
                exact(
                    body["expected"],
                    {"version", "content_hash"},
                    "expected cancellation head",
                )
                return self.job(
                    actor,
                    project,
                    s.cancel(
                        actor,
                        project,
                        job.job_id,
                        Head(**body["expected"]),
                        body["operation_id"],
                        checksum,
                    ),
                )
            if parts[2:] == ["retry"] and method == "POST":
                exact(body, {"operation_id"}, "retry command")
                return self.job(
                    actor,
                    project,
                    s.retry(actor, project, job.job_id, body["operation_id"], checksum),
                )
            if parts[2:] == ["review"] and method == "POST":
                return self.saved(
                    actor, s.review(actor, project, job.job_id, body, checksum)
                )
        if parts == ["reviews"] and method == "GET":
            return {
                "ok": True,
                "records": [
                    asdict(v)
                    for v in repo.list_objects(
                        actor,
                        project,
                        domain=REVIEWS,
                        limit=int(query.get("limit", ["20"])[0]),
                        after_id=query.get("after", [""])[0],
                    )
                ],
            }
        if len(parts) >= 3 and parts[0] == "reviews" and method == "GET":
            review, report = s.accepted(actor, project, parts[1])
            value = json.loads(review.payload)
            if parts[2:] == ["handoff.json"]:
                result = {
                    "review_commit_id": review.commit_id,
                    "reviewer_user_id": value["reviewer_user_id"],
                    "report_sha256": value["report_sha256"],
                    "model_commit_id": report["model_commit_id"],
                    "frames": report["frames"],
                    "unit_system": "SI_m",
                    "named_selections": report["named_selections"],
                    "material_regions": report["regions"],
                    "mesh_intent": report["mesh_intent"],
                    "originals": report["artifact_hashes"],
                    "engineering_acceptance": value["engineering_acceptance"],
                    "mesh_status": "NOT_GENERATED",
                    "physical_validation": "NOT_PERFORMED",
                    "manufacturing_acceptance": "NOT_PERFORMED",
                }
                raw = json.dumps(result, sort_keys=True, allow_nan=False).encode()
                return BinarySource(
                    "reviewed-geometry-analysis-handoff.json",
                    raw,
                    sha256(raw).hexdigest(),
                )
            if len(parts) == 5 and parts[2] == "blobs":
                job_id, name = parts[3:]
                require(
                    job_id in report["artifact_hashes"]
                    and name in report["artifact_hashes"][job_id],
                    "R08_EXPORT",
                    "Only the exact reviewed original source/exchange artifacts may be exported",
                )
                raw = jobs.blob(actor, project, job_id, name)
                require(
                    sha256(raw).hexdigest() == report["artifact_hashes"][job_id][name],
                    "R08_INTEGRITY",
                    "Reviewed artifact changed",
                )
                return BinarySource(
                    "analysis-only-" + name, raw, sha256(raw).hexdigest()
                )
        if parts == ["remap-proposal"] and method == "POST":
            exact(body, {"review_commit_id", "new_model_commit_id"}, "remap proposal")
            old = repo.resolve_snapshot(actor, project, body["review_commit_id"])
            require(old.domain == REVIEWS, "R08_REMAP", "Original R08 review required")
            newer = repo.resolve_snapshot(actor, project, body["new_model_commit_id"])
            require(
                s.components.models.current(actor, newer),
                "R08_REMAP",
                "Current saved target model required",
            )
            _, _, report, _, _ = s.report(
                actor, project, json.loads(old.payload)["qualification_job_id"]
            )
            from systems.geometry.component_authority import from_source

            old_model = repo.resolve_snapshot(actor, project, report["model_commit_id"])
            a = from_source(old_model)
            b = from_source(newer)
            fingerprints = dict(a.graph.fingerprints(a.snapshot))
            other = dict(b.graph.fingerprints(b.snapshot))
            targets = {p.part_id: p for p in b.parts}
            mappings = []
            for boundary in report["named_selections"]:
                target = targets.get(boundary["part_id"])
                source_part = next(
                    p for p in a.parts if p.part_id == boundary["part_id"]
                )
                mappings.append(
                    {
                        "semantic_id": boundary["semantic_id"],
                        "status": "UNRESOLVED"
                        if target is None
                        else "PROPOSED_UNREVIEWED",
                        "fingerprint_equal": target is not None
                        and fingerprints.get(source_part.feature_id)
                        == other.get(target.feature_id),
                        "scope": boundary["scope"],
                    }
                )
            return {
                "ok": True,
                "persisted": False,
                "handoff_eligible": False,
                "mappings": mappings,
                "status": "NEW_POLICY_QUALIFICATION_AND_INDEPENDENT_REVIEW_REQUIRED",
            }
        raise RecordNotFound("Unknown R08 qualification route")
