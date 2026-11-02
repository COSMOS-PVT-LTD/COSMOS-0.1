"""Authenticated source-bound engine candidate builds; no publication authority."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import ClassVar

from api.geometry_projects import BinarySource, job_dto
from api.ngg_workbench import runtime_config
from infrastructure.geometry import WorkerCommand
from plugins.geometry.nozzle_protocol import POLICY, VERSION
from systems.contracts.geometry._wire import require
from systems.geometry.engine_builds import DOMAIN, SCHEMA, EngineBuildCoordinator
from systems.projects.authority import (
    HeadConflict,
    InvalidRecord,
    RecordNotFound,
    StoreUnavailable,
)


def create_workspace(root: Path, path: Path | None, *, enabled: bool):
    """Application composition crosses through API, never deep GUI→Systems IO."""
    from systems.geometry.nozzle_workspace import NozzleWorkspace
    if not enabled or path is None:
        raise StoreUnavailable("Engine nozzle building is disabled; configure a separately qualified local runtime explicitly.")
    runtime_configuration(path)
    return NozzleWorkspace(root / "engine_nozzle_candidates", lambda: runtime_configuration(path))


class EngineCandidateSource(BinarySource):
    """Unreviewed generated candidate bytes, not accepted engineering CAD."""


class EnginePreviewSource(BinarySource):
    """Display-only triangles from the exact retained STL, not metrology/export."""


def runtime_configuration(path: Path):
    config = runtime_config(path)
    extra = config.get("engine_nozzle")
    require(type(extra) is dict and set(extra) == {"policy", "version", "worker", "reader", "receipt", "receipt_sha256"}
            and extra["policy"] == POLICY and extra["version"] == VERSION, "NOZZLE_RUNTIME_REQUIRED", "Separately qualified engine-nozzle runtime profile required; fixture qualification is not nozzle qualification")
    assert isinstance(extra, dict)
    root = Path(__file__).resolve().parents[1]
    for name, file in (("worker", "nozzle_worker.py"), ("reader", "nozzle_step_reader.py")):
        script = root / "plugins/geometry/workers" / file
        item = extra[name]
        require(type(item) is dict and set(item) == {"argv", "environment"} and len(item["argv"]) == 2
                and Path(item["argv"][1]) == script and str(script) in config["sha256"], "NOZZLE_RUNTIME_REQUIRED", "Only separately hash-pinned server-owned nozzle commands allowed")
        WorkerCommand(tuple(item["argv"]), tuple(item["environment"].items()))
    receipt = Path(extra["receipt"])
    require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink()
            and sha256(receipt.read_bytes()).hexdigest() == extra["receipt_sha256"], "NOZZLE_QUALIFICATION_REQUIRED", "Exact local nozzle software-qualification receipt required")
    decision = json.loads(receipt.read_bytes())
    require(decision.get("software_qa_pass") is True and decision.get("policy") == POLICY and decision.get("version") == VERSION
            and decision.get("physical_validation") == "NOT_PERFORMED", "NOZZLE_QUALIFICATION_REQUIRED", "Nozzle software QA must pass separately; physical acceptance cannot be fabricated")
    required = {str(root / name) for name in ("plugins/geometry/workers/nozzle_worker.py", "plugins/geometry/workers/nozzle_step_reader.py", "plugins/geometry/nozzle_protocol.py", "systems/geometry/nozzle_reference.py", "systems/geometry/nozzle_qa.py")}
    require(type(decision.get("method_sources")) is dict and required <= set(decision["method_sources"]), "NOZZLE_QUALIFICATION_REQUIRED", "Receipt must bind actual builder, contract and independent QA methods")
    for name, digest in decision["method_sources"].items():
        method_file = Path(name)
        require(method_file.is_absolute() and method_file.is_file() and not method_file.is_symlink() and sha256(method_file.read_bytes()).hexdigest() == digest, "NOZZLE_METHOD_CHANGED", "Nozzle sources changed since qualification; reconcile and requalify without rewriting historical receipts")
    require(all(command["argv"][0] == config["occt"]["argv"][0] and command["environment"] == config["occt"]["environment"] for command in (extra["worker"], extra["reader"])), "NOZZLE_RUNTIME_REQUIRED", "Nozzle commands must use the qualified interpreter and environment, not an unpinned replacement runtime")
    return {**config, "manifest_sha256": sha256(path.read_bytes()).hexdigest()}


class EngineBuildsAPI:
    domain=DOMAIN
    schema=SCHEMA
    policy=POLICY
    version=VERSION
    source_key="intent_commit_id"
    expected_key="expected_intent"
    file_stem="nozzle"
    qa_units:ClassVar[dict[str,str]]={"relative_volume":"1","centroid":"m","surface_distance":"m"}
    build_scope="Saved divergent radial-wall nozzle → bounded native profile/revolve → independent software QA → retained STEP/STL candidates. No accepted manufacturing export or physical readiness. No unsupported fixture-policy substitution."
    def __init__(self, coordinator: EngineBuildCoordinator):
        self.coordinator = coordinator

    def source(self, actor, source):
        return {"ok": True, "authority": {"project_id": source.project_id, "object_id": source.object_id, "commit_id": source.commit_id, "head": asdict(source.head)},
                "source_canonical_json": source.payload.decode(), "inputs": json.loads(source.payload), "upstream_current": self.coordinator.current(actor, source), "engineering_acceptance": "NOT_PERFORMED", "physical_validation": "NOT_PERFORMED"}

    def job(self, actor, job):
        source = self.coordinator.repository.resolve_snapshot(actor, job.project_id, job.source_commit_id)
        value = job_dto(job)
        value.update(ok=True, domain=self.domain, methods_and_upstream_current=self.coordinator.current(actor, source), runtime_current=self.coordinator.runtime_current(source), qa=None,
                     engineering_acceptance="NOT_PERFORMED", physical_validation="NOT_PERFORMED", current_generated_candidate=False,
                     scope="Generated engine candidate; declared software QA is not human engineering acceptance, manufacturing or physical validation")
        if job.state.value == "COMPLETED":
            record = json.loads(job.payload)
            value["qa"] = json.loads(record["evidence_json"])
            value["current_generated_candidate"] = job.selected and job.current_input and value["methods_and_upstream_current"] and value["runtime_current"]
        return value

    def handle(self, actor, method, project, parts, query, body):
        from api.project_authority import expected_head
        coordinator = self.coordinator
        repo, jobs = coordinator.repository, coordinator.jobs
        allowed = {"limit", "after"} if not parts and method == "GET" else {"commit"} if parts and parts[0] != "capabilities" and method == "GET" and len(parts) == 1 else set()
        if set(query) - allowed or any(len(values) != 1 for values in query.values()):
            raise InvalidRecord("Unknown nozzle query; exact source context must not be ignored.")
        if parts == ["capabilities"] and method == "GET":
            configured, reason = False, ""
            try:
                configured = bool(coordinator.factory().runtime_hashes)
            except (ValueError, OSError, RuntimeError, StoreUnavailable) as error:
                reason = str(error)[:1024]
            return {"ok": True, "schema": self.schema, "policy": self.policy, "version": self.version, "runtime_configured": configured, "unavailable_reason": reason,
                    "output_formats": ["step", "stl"], "qa_units": self.qa_units, "scope":self.build_scope}
        command_hash = sha256(json.dumps({"project": project, "path": parts, "body": body}, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if not parts:
            if method == "GET":
                return {"ok": True, "sources": [asdict(item) for item in repo.list_objects(actor, project, domain=self.domain, limit=int(query.get("limit", ["20"])[0]), after_id=query.get("after", [""])[0])]}
            if set(body) != {self.source_key, self.expected_key, "qa_specification", "output_formats", "operation_id"} or body["output_formats"] != ["step", "stl"]:
                raise InvalidRecord("Exact intent/head, explicit QA ceilings/source, paired STEP/STL formats and operation ID required; no posted worker paths or acceptance flags.")
            replay = jobs.resolve_command(actor, project, operation_id=body["operation_id"], request_hash=command_hash)
            if replay is not None:
                return self.job(actor, replay)
            source = coordinator.capture(actor, project, body[self.source_key], expected_head(body[self.expected_key]), body["qa_specification"], body["operation_id"], command_hash)
            job = coordinator.start(actor, source, operation_id=body["operation_id"], request_hash=command_hash)
            return self.job(actor, job)
        source = repo.get_snapshot(actor, project, domain=self.domain, object_id=parts[0], commit_id=query.get("commit", [None])[0])
        if len(parts) == 1 and method == "GET":
            return self.source(actor, source)
        if parts[1:] == ["inputs.json"] and method == "GET":
            return EngineCandidateSource(self.file_stem+"-build-inputs.json", source.payload, source.head.content_hash)
        if parts[1:] == ["jobs"]:
            if method == "GET":
                rows = jobs.list_ids(actor, project, domain=self.domain, object_id=source.object_id, limit=100)
                return {"ok": True, "attempts": [self.job(actor, jobs.get(actor, project, key)) for _, key in rows]}
            if set(body) != {"expected", "operation_id", "retry_of"}:
                raise InvalidRecord("Retry only the exact retained build source/head and terminal attempt.")
            if source.head != expected_head(body["expected"]):
                raise HeadConflict(source.head)
            return self.job(actor, coordinator.start(actor, source, operation_id=body["operation_id"], request_hash=command_hash, retry_of=body["retry_of"]))
        if len(parts) >= 3 and parts[1] == "jobs":
            job = jobs.get(actor, project, parts[2])
            if job.domain != self.domain or job.object_id != source.object_id:
                raise RecordNotFound("Nozzle attempt does not belong to this exact source/project.")
            if len(parts) == 3 and method == "GET":
                return self.job(actor, job)
            if parts[3:] == ["cancel"] and method == "POST":
                if set(body) != {"expected", "operation_id"}:
                    raise InvalidRecord("Exact cancellation head/operation required.")
                return self.job(actor, coordinator.cancel(actor, project, job.job_id, expected=expected_head(body["expected"]), operation_id=body["operation_id"], request_hash=command_hash))
            if parts[3:] == ["stages"] and method == "GET":
                return {"ok": True, "stages": [{**asdict(stage), "source_canonical_json": jobs.stage_source(actor, project, job.job_id, stage.sequence).decode()} for stage in jobs.list_stages(actor, project, job.job_id, limit=100)]}
            if parts[3:] == ["record.json"] and method == "GET":
                return EngineCandidateSource(self.file_stem+"-build-record.json", job.payload, sha256(job.payload).hexdigest())
            if len(parts) == 5 and parts[3] == "blobs" and method == "GET":
                if job.state.value != "COMPLETED" or parts[4] not in {"source.brep", "export.step", "export.stl"}:
                    raise InvalidRecord("Only exact completed software-QA candidate files are available; no partial/failed export.")
                raw = jobs.blob(actor, project, job.job_id, parts[4])
                return EngineCandidateSource(parts[4], raw, sha256(raw).hexdigest())
            if parts[3:] == ["preview"] and method == "GET":
                if job.state.value != "COMPLETED":
                    raise InvalidRecord("No display mesh before complete software QA.")
                raw = jobs.blob(actor, project, job.job_id, "export.stl")
                # Reuse the strict SI STL parser without putting a worker or
                # filesystem path under browser control. Bytes already verified
                # by durable blob authority, parse through its read-only view.
                import numpy as np

                from systems.geometry.qa import STL_RECORD
                count = int.from_bytes(raw[80:84], "little")
                require(b"UNITS= m" in raw[:80] and 0 < count <= 200000 and len(raw) == 84 + 50 * count, "INVALID_PREVIEW", "Exact bounded metre STL required")
                positions = np.frombuffer(raw, STL_RECORD, count=count, offset=84)["vertices"].astype("<f4").tobytes()
                require(np.isfinite(np.frombuffer(positions, dtype="<f4")).all(), "INVALID_PREVIEW", "Preview vertices must be finite")
                return EnginePreviewSource(self.file_stem+"-display.f32", positions, sha256(positions).hexdigest())
        raise RecordNotFound("Unsupported engine nozzle build route.")
