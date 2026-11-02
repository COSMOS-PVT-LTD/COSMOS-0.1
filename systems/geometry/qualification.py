"""R08 orchestration over existing project/job authority; never another store."""

from __future__ import annotations

import json
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4, uuid5

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry import BuildState, GeometryBuildRecord
from systems.contracts.geometry._wire import require
from systems.geometry.component_authority import from_source
from systems.geometry.component_authority import methods as component_methods
from systems.geometry.pico_component_builds import methods as pico_methods
from systems.geometry.qualification_policy import SCHEMA, exact, text, validate
from systems.persistence.job_repository import TERMINAL, BlobAttachment, JobState
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    ProjectStoreError,
)

ROOT = Path(__file__).resolve().parents[2]
POLICIES = "geometry-qualification-policy"
INPUTS = "geometry-qualification"
REVIEWS = "geometry-qualification-review"
INPUT_SCHEMA = "cosmos.geometry-qualification-input.v1"
REVIEW_SCHEMA = "cosmos.geometry-qualification-review.v1"
CHECKS = {
    "reference_and_applicability",
    "critical_feature_coverage",
    "topology_and_interoperability",
    "sampling_refinement_and_outliers",
    "materials_boundaries_mesh_intent",
    "declared_limitations",
}


def methods():
    files = (
        "systems/geometry/qualification.py",
        "systems/geometry/qualification_policy.py",
        "systems/geometry/surface_discrepancy.py",
        "plugins/geometry/workers/qualification_worker.py",
        "api/geometry_qualification.py",
        "scripts/qualify_geometry_qa.py",
    )
    return {
        **component_methods(),
        **pico_methods(),
        **{p: sha256((ROOT / p).read_bytes()).hexdigest() for p in files},
    }


class QualificationRuntime:
    def __init__(self, configuration):
        self.configuration = configuration
        self.supervisor = WorkerSupervisor(
            timeout_s=300, max_workers=1, max_queued=1, stdout_limit=8 * 1024**2
        )

    def run(self, reference, candidate, payload, token):
        cfg = self.configuration()
        with tempfile.TemporaryDirectory(prefix="cosmos-r08-") as directory:
            root = Path(directory).resolve()
            for name, raw in (
                ("reference.stl", reference),
                ("candidate.stl", candidate),
            ):
                with (root / name).open("xb") as f:
                    f.write(raw)
            command = WorkerCommand(
                (
                    cfg["python"],
                    str(ROOT / "plugins/geometry/workers/qualification_worker.py"),
                ),
                (
                    ("PYTHONPATH", str(ROOT)),
                    ("OMP_NUM_THREADS", "1"),
                    ("OPENBLAS_NUM_THREADS", "1"),
                ),
            )
            result = self.supervisor.submit(
                "r08-" + uuid4().hex,
                command,
                json.dumps(payload, allow_nan=False).encode(),
                root,
                cancellation=token,
            ).result(timeout=310)
            require(
                result.code == "OK" and result.exit_code == 0,
                "R08_WORKER",
                "Bounded qualification worker failed: "
                + result.code
                + "; "
                + result.stderr.decode(errors="replace")[-1000:],
            )
            value = json.loads(result.stdout)
            require(
                value["reference_sha256"] == sha256(reference).hexdigest()
                and value["candidate_sha256"] == sha256(candidate).hexdigest(),
                "R08_INTEGRITY",
                "Direct comparison returned another source",
            )
            value["process"] = {
                "code": result.code,
                "exit_code": result.exit_code,
                "elapsed_s": result.elapsed_s,
                "observed_rss_bytes": result.maximum_rss_bytes,
            }
            return value

    def close(self):
        self.supervisor.close()


class GeometryQualification:
    def __init__(
        self, repository, jobs, components, pico, resolve_actor, runtime_factory
    ):
        self.repository, self.jobs, self.components, self.pico = (
            repository,
            jobs,
            components,
            pico,
        )
        self.resolve_actor, self.runtime_factory = resolve_actor, runtime_factory
        self.pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="r08-qualification"
        )
        self.lock = threading.RLock()
        self.live = {}
        self.closed = False
        self.loaded_methods = methods()

    def current_policy(self, actor, saved):
        value = json.loads(saved.payload)
        return (
            saved.domain == POLICIES
            and saved.schema_id == SCHEMA
            and value["method_sources"] == self.loaded_methods == methods()
            and self.repository.dependencies_current(
                actor, saved.project_id, saved.commit_id
            )
            and self.components.models.current(
                actor,
                self.repository.resolve_snapshot(
                    actor, saved.project_id, value["model_commit_id"]
                ),
            )
        )

    def save_policy(self, actor, project, command, command_hash):
        exact(
            command,
            {"model_commit_id", "expected_model", "policy", "operation_id"},
            "policy command",
        )
        prior = self.repository.resolve_command(
            actor,
            project,
            operation_id=command["operation_id"],
            command_hash=command_hash,
        )
        if prior is not None:
            return prior
        actor.require(write=True)
        model = self.repository.resolve_snapshot(
            actor, project, command["model_commit_id"]
        )
        require(
            self.components.models.current(actor, model)
            and self.loaded_methods == methods(),
            "R08_STALE",
            "Policy requires exact CURRENT saved component model/methods",
        )
        exact(
            command["expected_model"],
            {"version", "content_hash"},
            "expected model head",
        )
        if Head(**command["expected_model"]) != model.head:
            raise HeadConflict(model.head)
        validate(command["policy"], from_source(model))
        value = {
            "model_commit_id": model.commit_id,
            "model_sha256": model.head.content_hash,
            "policy": command["policy"],
            "method_sources": methods(),
            "engineering_acceptance": "NOT_PERFORMED",
            "physical_validation": "NOT_PERFORMED",
        }
        object_id = str(
            uuid5(
                UUID(project), actor.user_id + ":r08-policy:" + command["operation_id"]
            )
        )
        return self.repository.save_snapshot(
            actor,
            project,
            domain=POLICIES,
            object_id=object_id,
            input_revision=model.input_revision,
            payload=RecordPayload.from_mapping(value, SCHEMA),
            expected=Head.absent(),
            operation_id=command["operation_id"],
            command_hash=command_hash,
            dependencies=(Dependency("component-model", model.commit_id),),
            purpose="create",
        )

    def candidate(self, actor, project, job_id, policy):
        job = self.jobs.get(actor, project, job_id)
        require(
            job.domain in {"engine-component-build", "picogk-component-build"}
            and job.state is JobState.COMPLETED
            and job.selected
            and job.current_input,
            "R08_CANDIDATE",
            "Exact selected completed component candidate required",
        )
        source = self.repository.resolve_snapshot(actor, project, job.source_commit_id)
        value = json.loads(source.payload)
        pol = json.loads(policy.payload)
        coordinator = (
            self.components.builds.coordinator
            if job.domain == "engine-component-build"
            else self.pico.coordinator
            if self.pico
            else None
        )
        require(
            coordinator is not None
            and coordinator.current(actor, source)
            and coordinator.runtime_current(source),
            "R08_STALE",
            "Exact current source/method/runtime required",
        )
        require(
            value["model_commit_id"] == pol["model_commit_id"]
            and value["model_sha256"] == pol["model_sha256"],
            "R08_SOURCE",
            "All representations/resolutions must bind the exact same saved model",
        )
        require(
            datetime.fromisoformat(source.created_at)
            > datetime.fromisoformat(policy.created_at),
            "R08_PREDECLARATION",
            "Policy must predate every build capture; existing exploratory builds cannot acquire retroactive intended-use acceptance",
        )
        envelope = json.loads(job.payload)
        record = GeometryBuildRecord.from_json(envelope["record_json"])
        qa = json.loads(envelope["evidence_json"])
        revision = coordinator.decode(source)
        require(
            record.snapshot == revision.snapshot
            and record.feature_graph == revision.graph
            and record.request == revision.request,
            "R08_SOURCE",
            "Candidate must bind exact captured snapshot, graph and native request",
        )
        require(
            record.state is BuildState.ACCEPTED
            and qa["qa-stl"]["pass"]
            and qa["qa-stl"]["topology_pass"],
            "R08_TOPOLOGY",
            "Failed/unverified topology cannot enter accepted qualification",
        )
        if job.domain == "engine-component-build":
            require(
                qa["qa-step"]["pass"] and qa["qa-step"]["semantic_mapping_pass"],
                "R08_REIMPORT",
                "Independent analytic reimport and semantic mapping required",
            )
        blobs = {}
        for blob in job.blobs:
            if blob.kind in {"source", "artifact"}:
                raw = self.jobs.blob(actor, project, job_id, blob.name)
                require(
                    sha256(raw).hexdigest() == blob.content_hash,
                    "R08_INTEGRITY",
                    "Exact retained source/export bytes required",
                )
                blobs[blob.name] = blob.content_hash
        for artifact in record.artifacts:
            require(
                blobs.get(artifact.storage_uri.rsplit("/", 1)[-1]) == artifact.sha256
                and artifact.source_artifact_sha256 in blobs.values(),
                "R08_INTEGRITY",
                "Native source and export hashes must bind retained originals separately",
            )
        return job, source, record, qa, blobs

    def inputs(self, actor, project, policy, analytic, implicit):
        require(
            self.current_policy(actor, policy),
            "R08_STALE",
            "Current predeclared policy/model required",
        )
        p = json.loads(policy.payload)["policy"]
        require(
            type(analytic) is str
            and type(implicit) is list
            and all(type(v) is str for v in implicit)
            and len(implicit) in {0, 3}
            and len({analytic, *implicit}) == 1 + len(implicit),
            "R08_REFINEMENT",
            "Unique analytic attempt and zero/three explicit implicit attempts required",
        )
        require(
            len(implicit) == len(p["refinement_resolutions_m"]),
            "R08_REFINEMENT",
            "Every predeclared implicit resolution needs its own retained attempt; no silent refinement or omitted failure",
        )
        candidates = [
            self.candidate(actor, project, j, policy) for j in [analytic, *implicit]
        ]
        require(
            candidates[0][0].domain == "engine-component-build"
            and all(c[0].domain == "picogk-component-build" for c in candidates[1:]),
            "R08_REPRESENTATION",
            "Analytic reference plus direct PicoGK fields/mesh required; no representation relabelling",
        )
        for h, c in zip(p["refinement_resolutions_m"], candidates[1:], strict=True):
            actual = json.loads(c[1].payload)["qa_specification"]["voxel_resolution"][
                "value"
            ]
            require(
                abs(actual - h) <= h * 1e-12,
                "R08_REFINEMENT",
                "Implicit study spacing/order differs from the predeclared policy",
            )
        return candidates

    def start(self, actor, project, command, command_hash):
        actor.require(write=True)
        exact(
            command,
            {"policy_commit_id", "analytic_job_id", "implicit_job_ids", "operation_id"},
            "qualification command",
        )
        replay = self.jobs.resolve_command(
            actor,
            project,
            operation_id=command["operation_id"],
            request_hash=command_hash,
        )
        if replay is not None:
            return replay
        runtime = self.runtime_factory()
        runtime.configuration()
        policy = self.repository.resolve_snapshot(
            actor, project, command["policy_commit_id"]
        )
        candidates = self.inputs(
            actor,
            project,
            policy,
            command["analytic_job_id"],
            command["implicit_job_ids"],
        )
        object_id = str(
            uuid5(
                UUID(project), actor.user_id + ":r08-attempt:" + command["operation_id"]
            )
        )
        value = {
            "command": command,
            "method_sources": methods(),
            "runtime": runtime.configuration(),
            "policy_commit_id": policy.commit_id,
            "job_heads": {c[0].job_id: asdict(c[0].head) for c in candidates},
            "artifact_hashes": {c[0].job_id: c[4] for c in candidates},
        }
        op = (
            "r08-input-"
            + sha256((actor.user_id + command["operation_id"]).encode()).hexdigest()
        )
        prior = self.repository.resolve_command(
            actor, project, operation_id=op, command_hash=command_hash
        )
        source = prior or self.repository.save_snapshot(
            actor,
            project,
            domain=INPUTS,
            object_id=object_id,
            input_revision=policy.input_revision,
            payload=RecordPayload.from_mapping(value, INPUT_SCHEMA),
            expected=Head.absent(),
            operation_id=op,
            command_hash=command_hash,
            dependencies=(
                Dependency("intended-use-policy", policy.commit_id),
                *(
                    Dependency(
                        "geometry-candidate-" + str(i), c[1].commit_id, c[0].job_id
                    )
                    for i, c in enumerate(candidates)
                ),
            ),
            purpose="create",
        )
        return self.launch(actor, source, command["operation_id"], command_hash)

    def launch(self, actor, source, operation, command_hash, retry_of=None):
        with self.lock:
            require(
                not self.closed and len(self.live) < 4,
                "R08_CAPACITY",
                "Qualification coordinator closed or four bounded pending attempts already admitted",
            )
            job = self.jobs.admit(
                actor,
                source,
                operation_id=operation,
                request_hash=command_hash,
                retry_of=retry_of,
            )
            if job.state not in TERMINAL and job.job_id not in self.live:
                token = threading.Event()
                self.live[job.job_id] = token
                self.pool.submit(self._run, job, source, token)
            return job

    def retry(self, actor, project, job_id, operation, command_hash):
        actor.require(write=True)
        old = self.jobs.get(actor, project, job_id)
        source = self.repository.resolve_snapshot(actor, project, old.source_commit_id)
        require(
            old.domain == INPUTS and old.state in TERMINAL,
            "R08_RETRY",
            "Only terminal exact R08 sources may be retried",
        )
        value = json.loads(source.payload)
        require(
            value["method_sources"] == methods()
            and self.runtime_factory().configuration() == value["runtime"],
            "R08_STALE",
            "Changed methods/runtime need a new capture, not an exact retry",
        )
        policy = self.repository.resolve_snapshot(
            actor, project, value["policy_commit_id"]
        )
        c = value["command"]
        self.inputs(actor, project, policy, c["analytic_job_id"], c["implicit_job_ids"])
        return self.launch(actor, source, operation, command_hash, retry_of=job_id)

    def _run(self, job, source, token):
        campaign = []
        try:
            started = self.jobs.advance(
                job.job_id,
                JobState.RUNNING,
                RecordPayload.from_mapping(
                    {"code": "R08_CHECKING_EXACT_ORIGINALS"}, INPUT_SCHEMA
                ),
            )
            if started.state is JobState.CANCELLED:
                return
            actor = self.resolve_actor(job.creator_user_id)
            v = json.loads(source.payload)
            require(
                v["method_sources"] == methods()
                and v["runtime"] == self.runtime_factory().configuration(),
                "R08_STALE",
                "Qualification sources/runtime changed after admission",
            )
            policy = self.repository.resolve_snapshot(
                actor, job.project_id, v["policy_commit_id"]
            )
            p = json.loads(policy.payload)
            c = v["command"]
            candidates = self.inputs(
                actor,
                job.project_id,
                policy,
                c["analytic_job_id"],
                c["implicit_job_ids"],
            )
            require(
                v["job_heads"] == {x[0].job_id: asdict(x[0].head) for x in candidates}
                and v["artifact_hashes"] == {x[0].job_id: x[4] for x in candidates},
                "R08_INTEGRITY",
                "Candidate heads/original hashes changed after capture",
            )
            model = self.repository.resolve_snapshot(
                actor, job.project_id, p["model_commit_id"]
            )
            plan = from_source(model)
            a = candidates[0]
            reference = self.jobs.blob(actor, job.project_id, a[0].job_id, "export.stl")
            # Evaluate the analytic mesh itself and all three implicit meshes.
            for current in candidates:
                require(
                    not token.is_set() and not self.closed,
                    "CANCELLED",
                    "R08 qualification cancelled before publication",
                )
                raw = self.jobs.blob(
                    actor, job.project_id, current[0].job_id, "export.stl"
                )
                payload = {
                    "snapshot_json": plan.snapshot.to_json(),
                    "graph_json": plan.graph.to_json(),
                    "policy": p["policy"],
                    "reference_parts": a[3]["worker_observations"]["parts"],
                    "candidate_parts": current[3]["worker_observations"]["parts"],
                    "reference_sha256": sha256(reference).hexdigest(),
                    "candidate_sha256": sha256(raw).hexdigest(),
                    "compare": current is not a,
                }
                actual = self.runtime_factory().run(reference, raw, payload, token)
                actual.update(
                    job_id=current[0].job_id,
                    voxel_resolution_m=None
                    if current is a
                    else json.loads(current[1].payload)["qa_specification"][
                        "voxel_resolution"
                    ]["value"],
                    generation_process=current[3].get("process"),
                    source_export_hashes=current[4],
                )
                campaign.append(actual)
            mappings = []
            steps = {x["part_id"]: x for x in a[3]["qa-step"]["parts"]}
            for boundary in p["policy"]["boundaries"]:
                entities = (
                    [boundary["part_id"]]
                    if boundary["scope"] == "WHOLE_PART"
                    else steps[boundary["part_id"]]["semantic_entities"].get(
                        boundary["semantic_id"].removeprefix(boundary["part_id"] + ":"),
                        [],
                    )
                )
                mappings.append(
                    {
                        **boundary,
                        "entities": entities,
                        "status": "EXACT_FOR_CAPTURED_ANALYTIC_REVISION"
                        if entities
                        else "UNRESOLVED",
                        "geometry_revision_id": a[2].artifacts[0].geometry_revision_id,
                    }
                )
            passed = (
                all(x["pass"] for x in campaign)
                and all(x["entities"] for x in mappings)
                and not p["policy"]["require_certified_self_intersection"]
            )
            report = {
                "schema": "cosmos.geometry-qualification-report.v1",
                "pass": passed,
                "policy_commit_id": policy.commit_id,
                "policy_sha256": policy.head.content_hash,
                "model_commit_id": model.commit_id,
                "intended_use": p["policy"]["intended_use"],
                "campaign": campaign,
                "named_selections": mappings,
                "regions": p["policy"]["regions"],
                "mesh_intent": p["policy"]["mesh_intent"],
                "frames": json.loads(plan.snapshot.to_json())["frames"],
                "artifact_hashes": v["artifact_hashes"],
                "job_heads": v["job_heads"],
                "method_sources": methods(),
                "refinement_status": "THREE_EXPLICIT_RESOLUTIONS_EVALUATED_NOT_EXTRAPOLATED"
                if len(candidates) == 4
                else "ANALYTIC_ONLY_NO_IMPLICIT_QUALIFICATION",
                "reader_kernel_independence": False,
                "reimport": "Retained independent Gmsh STEP import and independent encoded mesh checks; original units/placements/part identities verified",
                "self_intersection": "NOT_CERTIFIED; OCCT native BREP validity and encoded topology are narrower checks",
                "mesh_status": "NOT_GENERATED",
                "engineering_acceptance": "AWAITING_INDEPENDENT_REVIEW",
                "manufacturing_acceptance": "NOT_PERFORMED",
                "physical_validation": "NOT_PERFORMED",
            }
            raw = json.dumps(
                report, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
            digest = sha256(raw).hexdigest()
            require(
                len(raw) <= 8 * 1024**2,
                "R08_CAPACITY",
                "Bounded retained qualification report required",
            )
            self.jobs.advance(
                job.job_id,
                JobState.INTERRUPTED if self.closed else JobState.COMPLETED,
                RecordPayload.from_mapping(
                    {"pass": passed, "report_sha256": digest}, INPUT_SCHEMA
                ),
                attachments=()
                if self.closed
                else (BlobAttachment("qualification.json", raw, digest, "diagnostic"),),
                actor=actor,
                selection_allowed=self.current_policy(actor, policy),
            )
        except Exception as error:  # noqa: BLE001 -- retain unexpected async failures, never invent success
            self.jobs.advance(
                job.job_id,
                JobState.INTERRUPTED if self.closed else JobState.FAILED,
                RecordPayload.from_mapping(
                    {
                        "code": getattr(error, "code", "R08_FAILED"),
                        "message": str(error)[:4096],
                        "completed_campaign": campaign,
                    },
                    INPUT_SCHEMA,
                ),
            )
        finally:
            with self.lock:
                self.live.pop(job.job_id, None)

    def cancel(self, actor, project, job_id, expected, operation, command_hash):
        actor.require(write=True)
        job = self.jobs.get(actor, project, job_id)
        require(job.domain == INPUTS, "R08_SOURCE", "Exact R08 attempt required")
        result = self.jobs.cancel(
            actor,
            project,
            job_id,
            expected=expected,
            operation_id=operation,
            request_hash=command_hash,
        )
        with self.lock:
            token = self.live.get(job_id)
            if token:
                token.set()
        return result

    def report(self, actor, project, job_id):
        job = self.jobs.get(actor, project, job_id)
        require(
            job.domain == INPUTS and job.state is JobState.COMPLETED,
            "R08_REPORT",
            "Exact completed R08 calculation required; completion is not engineering acceptance",
        )
        source = self.repository.resolve_snapshot(actor, project, job.source_commit_id)
        v = json.loads(source.payload)
        raw = self.jobs.blob(actor, project, job_id, "qualification.json")
        require(
            sha256(raw).hexdigest() == json.loads(job.payload)["report_sha256"],
            "R08_INTEGRITY",
            "Report bytes differ from terminal evidence",
        )
        report = json.loads(raw)
        policy = self.repository.resolve_snapshot(actor, project, v["policy_commit_id"])
        current = (
            job.selected
            and job.current_input
            and self.current_policy(actor, policy)
            and v["method_sources"] == methods()
        )
        if current:
            try:
                current = self.runtime_factory().configuration() == v["runtime"]
                c = v["command"]
                if current:
                    self.inputs(
                        actor,
                        project,
                        policy,
                        c["analytic_job_id"],
                        c["implicit_job_ids"],
                    )
            except (ValueError, ProjectStoreError, OSError):
                current = False
        return job, source, report, raw, bool(current)

    def review(self, actor, project, job_id, command, command_hash):
        exact(
            command,
            {
                "decision",
                "expected_job",
                "expected_review",
                "report_sha256",
                "qualification_source",
                "rationale",
                "limitations",
                "checks",
                "operation_id",
            },
            "independent review",
        )
        replay = self.repository.resolve_command(
            actor,
            project,
            operation_id=command["operation_id"],
            command_hash=command_hash,
        )
        if replay is not None:
            return replay
        actor.require(write=True)
        job, source, report, raw, current = self.report(actor, project, job_id)
        require(
            current,
            "R08_STALE",
            "Historical report cannot receive current engineering acceptance",
        )
        exact(command["expected_job"], {"version", "content_hash"}, "expected job head")
        if Head(**command["expected_job"]) != job.head:
            raise HeadConflict(job.head)
        require(
            command["report_sha256"] == sha256(raw).hexdigest(),
            "R08_INTEGRITY",
            "Review must bind exact retained report bytes",
        )
        policy = self.repository.resolve_snapshot(
            actor, project, report["policy_commit_id"]
        )
        builders = {
            self.jobs.get(actor, project, key).creator_user_id
            for key in report["artifact_hashes"]
        }
        if actor.user_id in builders | {job.creator_user_id, policy.creator_user_id}:
            raise AccessDenied(
                "A different active authorized project engineer must review; no synthetic/self sign-off"
            )
        require(
            type(command["decision"]) is str
            and command["decision"] in {"ACCEPT", "REJECT"},
            "R08_REVIEW",
            "Explicit ACCEPT/REJECT decision required",
        )
        exact(command["checks"], CHECKS, "independent review checks")
        require(
            all(type(v) is bool for v in command["checks"].values()),
            "R08_REVIEW",
            "Every review check requires an explicit Boolean",
        )
        require(
            command["decision"] != "ACCEPT"
            or report["pass"]
            and all(command["checks"].values()),
            "R08_REVIEW",
            "Failed/incomplete evidence cannot receive accepted export",
        )
        for key in ("qualification_source", "rationale", "limitations"):
            text(command[key], key)
        # One CAS-governed decision stream per qualification. A later rejection
        # supersedes the old acceptance; old URLs cannot bypass withdrawal.
        object_id = job.job_id
        exact(
            command["expected_review"],
            {"version", "content_hash"},
            "expected review head",
        )
        expected = Head(**command["expected_review"])
        value = {
            "command": command,
            "reviewer_user_id": actor.user_id,
            "qualification_job_id": job.job_id,
            "qualification_input_commit_id": source.commit_id,
            "report_sha256": sha256(raw).hexdigest(),
            "method_sources": methods(),
            "qualification_status": "REVIEWER_DECLARED_NOT_EXTERNALLY_CREDENTIAL_VERIFIED",
            "engineering_acceptance": "ACCEPTED_FOR_" + report["intended_use"]
            if command["decision"] == "ACCEPT"
            else "REJECTED",
            "manufacturing_acceptance": "NOT_PERFORMED",
            "physical_validation": "NOT_PERFORMED",
        }
        return self.repository.save_snapshot(
            actor,
            project,
            domain=REVIEWS,
            object_id=object_id,
            input_revision=source.input_revision,
            payload=RecordPayload.from_mapping(value, REVIEW_SCHEMA),
            expected=expected,
            operation_id=command["operation_id"],
            command_hash=command_hash,
            dependencies=(
                Dependency("qualification", source.commit_id, job.job_id),
                Dependency("policy", policy.commit_id),
            ),
            purpose="create" if expected == Head.absent() else "save",
        )

    def accepted(self, actor, project, object_id):
        saved = self.repository.get_snapshot(
            actor, project, domain=REVIEWS, object_id=object_id
        )
        v = json.loads(saved.payload)
        require(
            v["command"]["decision"] == "ACCEPT"
            and v["method_sources"] == methods()
            and self.repository.dependencies_current(actor, project, saved.commit_id),
            "R08_NOT_ACCEPTED",
            "Current authentic evidence-bound independent acceptance required",
        )
        _job, _, report, raw, current = self.report(
            actor, project, v["qualification_job_id"]
        )
        reviewer = self.resolve_actor(v["reviewer_user_id"])
        reviewer.require(write=True)
        self.repository.get_project(reviewer, project)
        require(
            current
            and report["pass"]
            and v["report_sha256"] == sha256(raw).hexdigest(),
            "R08_STALE",
            "Accepted handoff evidence changed or is stale",
        )
        return saved, report

    def close(self):
        with self.lock:
            self.closed = True
            for token in self.live.values():
                token.set()
        self.pool.shutdown(wait=True, cancel_futures=False)
