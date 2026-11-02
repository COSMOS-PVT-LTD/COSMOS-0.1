"""Managed geometry API. Fixed-fixture source namespace is never ownership."""
from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid5

from systems.geometry.authority import DOMAIN, ManagedGeometry, decode_source
from systems.persistence.job_repository import DurableJob
from systems.projects.authority import (
    InvalidRecord,
    Principal,
    RecordNotFound,
    SavedSnapshot,
)


def _allowed(body: dict[str, Any], fields: set[str]) -> None:
    if body.keys() - fields:
        raise InvalidRecord("Unknown managed geometry fields; posted paths, roles and worker commands are forbidden.")


@dataclass(frozen=True)
class BinarySource:
    name: str
    data: bytes
    content_hash: str


def snapshot_dto(saved: SavedSnapshot, current: SavedSnapshot) -> dict[str, Any]:
    revision = decode_source(saved)
    return {"ok": True, "authority": {"project_id": saved.project_id, "object_id": saved.object_id,
        "commit_id": saved.commit_id, "head": asdict(saved.head), "input_revision": saved.input_revision,
        "is_current": current.commit_id == saved.commit_id}, "source_canonical_json": saved.payload.decode(),
        "settings": revision.settings, "snapshot_id": revision.snapshot.snapshot_id,
        "source_namespace": revision.snapshot.project_id, "published": False, "physical_validation": False}


def job_dto(job: DurableJob, *, detail: bool = True) -> dict[str, Any]:
    result = {"ok": True, "job_id": job.job_id, "project_id": job.project_id, "object_id": job.object_id,
        "source_commit_id": job.source_commit_id, "retry_of": job.retry_of, "state": job.state.value,
        "head": asdict(job.head), "events": [{**asdict(item), "state": item.state.value} for item in job.events],
        "source_canonical_json": job.payload.decode(), "blobs": [asdict(item) for item in job.blobs],
        "selected_attempt": job.selected, "input_current": job.current_input,
        "byte_integrity": "NOT_CHECKED_AT_THIS_READ", "published": False, "engineering_export_eligible": False,
        "physical_validation": False}
    if not detail:
        result.pop("source_canonical_json")
        result.pop("events")
    return result


class GeometryProjectAPI:
    def __init__(self, coordinator: ManagedGeometry) -> None:
        self.coordinator = coordinator

    def handle(self, actor: Principal, method: str, project_id: str, parts: list[str],
               query: dict[str, list[str]], body: dict[str, Any]) -> dict[str, Any] | BinarySource:
        from api.project_authority import expected_head

        repo, jobs = self.coordinator.repository, self.coordinator.jobs
        limit = int(query.get("limit", ["20"])[0])
        command_hash = sha256(json.dumps({"project": project_id, "path": parts, "body": body},
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if not parts:
            if method == "GET":
                return {"ok": True, "objects": [asdict(item) for item in repo.list_objects(actor, project_id,
                    domain=DOMAIN, limit=limit, after_id=query.get("after", [""])[0])]}
            _allowed(body, {"settings", "expected", "operation_id"})
            object_id = str(uuid5(UUID(project_id), actor.user_id + ":geometry:" + body["operation_id"]))
            saved = self.coordinator.save(actor, project_id, object_id, settings=body["settings"], expected=expected_head(body["expected"]),
                operation_id=body["operation_id"], command_hash=command_hash)
            return snapshot_dto(saved, repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id))
        object_id, tail = parts[0], parts[1:]
        source = repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id,
                                   commit_id=query.get("commit", [None])[0])
        if not tail:
            if method != "GET":
                _allowed(body, {"settings", "expected", "operation_id"})
                source = self.coordinator.save(actor, project_id, object_id, settings=body["settings"], expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], command_hash=command_hash)
            return snapshot_dto(source, repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id))
        if tail == ["history"] and method == "GET":
            before = query.get("before", [None])[0]
            ids = repo.list_commit_ids(actor, project_id, domain=DOMAIN, object_id=object_id, limit=limit,
                                       before_version=int(before) if before is not None else None)
            return {"ok": True, "commits": [{"commit_id": item.commit_id, "head": asdict(item.head), "input_revision": item.input_revision}
                for item in (repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id, commit_id=commit) for commit in ids)]}
        if tail == ["jobs"]:
            if method == "GET":
                before = query.get("before", [None])[0]
                rows = jobs.list_ids(actor, project_id, object_id=object_id, limit=limit, before=int(before) if before else None, domain=DOMAIN)
                return {"ok": True, "attempts": [{"ordinal": ordinal, **job_dto(jobs.get(actor, project_id, job_id), detail=False)} for ordinal, job_id in rows]}
            _allowed(body, {"expected", "operation_id", "retry_of"})
            replay = jobs.resolve_command(actor, project_id, operation_id=body["operation_id"], request_hash=command_hash)
            if replay is not None:
                return job_dto(replay)
            if source.head != expected_head(body["expected"]):
                from systems.projects.authority import HeadConflict
                raise HeadConflict(source.head)
            return job_dto(self.coordinator.start(actor, source, operation_id=body["operation_id"], request_hash=command_hash, retry_of=body.get("retry_of")))
        if len(tail) >= 2 and tail[0] == "jobs":
            job = jobs.get(actor, project_id, tail[1])
            if job.object_id != object_id or job.domain != DOMAIN:
                raise RecordNotFound("Attempt not bound to this exact geometry object.")
            if len(tail) == 2 and method == "GET":
                return job_dto(job)
            if len(tail) == 3 and tail[2] == "stages" and method == "GET":
                return {"ok": True, "stages": [asdict(item) for item in jobs.list_stages(
                    actor, project_id, job.job_id, after=int(query.get("after", ["-1"])[0]), limit=limit)]}
            if len(tail) == 4 and tail[2] == "stages" and method == "GET":
                data = jobs.stage_source(actor, project_id, job.job_id, int(tail[3]))
                return {"ok": True, "source_canonical_json": data.decode(), "sha256": sha256(data).hexdigest()}
            if len(tail) == 3 and tail[2] == "cancel" and method == "POST":
                _allowed(body, {"expected", "operation_id"})
                return job_dto(self.coordinator.cancel(actor, project_id, job.job_id, expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], request_hash=command_hash))
            if len(tail) == 3 and tail[2] == "inspect" and method == "GET":
                for blob in job.blobs:
                    jobs.blob(actor, project_id, job.job_id, blob.name)
                if jobs.supports_stages:
                    for after in (-1, 99):
                        for stage in jobs.list_stages(actor, project_id, job.job_id, after=after, limit=100):
                            jobs.stage_source(actor, project_id, job.job_id, stage.sequence)
                return {**job_dto(job), "byte_integrity": True}
            if len(tail) in {4, 5} and tail[2] == "blobs" and method == "GET":
                data = jobs.blob(actor, project_id, job.job_id, tail[3])
                if len(tail) == 5:
                    if tail[4] != "binary":
                        raise RecordNotFound("Unknown attachment representation.")
                    return BinarySource(tail[3], data, sha256(data).hexdigest())
                if len(data) > 1024*1024:
                    raise InvalidRecord("Attachment exceeds JSON inspection budget; use the exact binary source endpoint.")
                return {"ok": True, "name": tail[3], "sha256": sha256(data).hexdigest(), "content_base64": base64.b64encode(data).decode(),
                        "scope": "immutable-software-fixture-source-not-engineering-publication"}
        raise RecordNotFound("Unknown managed geometry route.")
