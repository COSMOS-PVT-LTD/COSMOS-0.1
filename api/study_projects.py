"""Authenticated owning-project study/run transport; software benchmark only."""
from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid5

from api.geometry_projects import BinarySource, job_dto
from simulation.contracts import StudySettings, StudySnapshot
from systems.persistence.job_repository import DurableJob
from systems.projects.authority import (
    HeadConflict,
    InvalidRecord,
    Principal,
    RecordNotFound,
    SavedSnapshot,
)
from systems.projects.study_authority import DOMAIN, ManagedStudies, decode_study


def allowed(body: dict[str, Any], names: set[str]) -> None:
    if body.keys() - names:
        raise InvalidRecord("Unsupported study fields; posted results/roles/paths/solver commands are not authority.")


class StudyProjectAPI:
    def __init__(self, coordinator: ManagedStudies) -> None:
        self.coordinator = coordinator

    def attempt(self, actor: Principal, job: DurableJob, *, detail: bool = True) -> dict[str, Any]:
        source = self.coordinator.repository.get_snapshot(actor, job.project_id, domain=DOMAIN, object_id=job.object_id, commit_id=job.source_commit_id)
        saved = decode_study(source)
        methods = StudySnapshot(saved.study.handoff, saved.study.settings).to_json() == saved.study.to_json()
        return {**job_dto(job, detail=detail), "methods_current": methods, "input_current": job.current_input and methods,
                "scope": "software-spherical-benchmark-only", "experimental_validation": "not-performed"}

    def envelope(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        repo = self.coordinator.repository
        saved = decode_study(source)
        current = repo.get_snapshot(actor, source.project_id, domain=DOMAIN, object_id=source.object_id)
        dependencies = repo.dependencies(actor, source.project_id, source.commit_id)
        if dependencies != (saved.dependency,):
            raise InvalidRecord("Stored study source and dependency index disagree.")
        methods = StudySnapshot(saved.study.handoff, saved.study.settings)
        return {"ok": True, "authority": {"project_id": source.project_id, "object_id": source.object_id,
            "commit_id": source.commit_id, "head": asdict(source.head), "input_revision": source.input_revision,
            "is_current": source.commit_id == current.commit_id}, "study_id": saved.study.content_sha256,
            "source_canonical_json": source.payload.decode(), "study_json": saved.study.to_json(), "mesh_json": saved.mesh_json,
            "settings": {name: getattr(saved.study.settings, name) for name in (
                "conductivity_w_m_k", "generation_w_m3", "surface_k", "cells", "relative_residual", "max_iterations")},
            "dependencies": [asdict(value) for value in dependencies],
            "upstream_current": repo.dependencies_current(actor, source.project_id, source.commit_id),
            "methods_current": methods.to_json() == saved.study.to_json(), "source_namespace": source.source_namespace,
            "scope": "software-sphere-radial-benchmark-only", "production_handoff": False, "experimental_validation": "not-performed"}

    def handle(self, actor: Principal, method: str, project_id: str, parts: list[str], query: dict[str, list[str]], body: dict[str, Any]) -> dict[str, Any] | BinarySource:
        from api.project_authority import expected_head

        repo, jobs = self.coordinator.repository, self.coordinator.jobs
        limit = int(query.get("limit", ["20"])[0])
        command_hash = sha256(json.dumps({"project": project_id, "path": parts, "body": body},
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        if not parts:
            if method == "GET":
                defaults = StudySettings()
                return {"ok": True, "objects": [asdict(value) for value in repo.list_objects(actor, project_id, domain=DOMAIN,
                    limit=limit, after_id=query.get("after", [""])[0])], "default_settings": {name: getattr(defaults, name) for name in (
                        "conductivity_w_m_k", "generation_w_m3", "surface_k", "cells", "relative_residual", "max_iterations")},
                    "scope": "existing-software-benchmark-settings-not-engine-design-defaults"}
            allowed(body, {"settings", "geometry_job_id", "expected", "operation_id"})
            object_id = str(uuid5(UUID(project_id), actor.user_id + ":study:" + body["operation_id"]))
            saved = self.coordinator.save(actor, project_id, object_id, values=body["settings"], geometry_job_id=body["geometry_job_id"],
                expected=expected_head(body["expected"]), operation_id=body["operation_id"], command_hash=command_hash)
            return self.envelope(actor, saved)
        object_id, tail = parts[0], parts[1:]
        source = repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id, commit_id=query.get("commit", [None])[0])
        if not tail:
            if method != "GET":
                allowed(body, {"settings", "expected", "operation_id"})
                source = self.coordinator.save(actor, project_id, object_id, values=body["settings"], expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], command_hash=command_hash)
            return self.envelope(actor, source)
        if tail == ["history"] and method == "GET":
            before = query.get("before", [None])[0]
            ids = repo.list_commit_ids(actor, project_id, domain=DOMAIN, object_id=object_id, limit=limit, before_version=int(before) if before else None)
            return {"ok": True, "commits": [{"commit_id": saved.commit_id, "head": asdict(saved.head), "input_revision": saved.input_revision}
                for saved in (repo.get_snapshot(actor, project_id, domain=DOMAIN, object_id=object_id, commit_id=key) for key in ids)]}
        if tail == ["jobs"]:
            if method == "GET":
                before = query.get("before", [None])[0]
                rows = jobs.list_ids(actor, project_id, object_id=object_id, limit=limit, before=int(before) if before else None, domain=DOMAIN)
                return {"ok": True, "attempts": [{"ordinal": order, **self.attempt(actor, jobs.get(actor, project_id, key), detail=False)} for order, key in rows]}
            allowed(body, {"expected", "operation_id", "retry_of"})
            replay = jobs.resolve_command(actor, project_id, operation_id=body["operation_id"], request_hash=command_hash)
            if replay is not None:
                return self.attempt(actor, replay)
            if source.head != expected_head(body["expected"]):
                raise HeadConflict(source.head)
            return self.attempt(actor, self.coordinator.start(actor, source, operation_id=body["operation_id"], request_hash=command_hash, retry_of=body.get("retry_of")))
        if len(tail) >= 2 and tail[0] == "jobs":
            job = jobs.get(actor, project_id, tail[1])
            if job.domain != DOMAIN or job.object_id != object_id:
                raise RecordNotFound("Run is not bound to this exact owning study.")
            if len(tail) == 2 and method == "GET":
                return self.attempt(actor, job)
            if tail[2:] == ["cancel"] and method == "POST":
                allowed(body, {"expected", "operation_id"})
                return self.attempt(actor, self.coordinator.cancel(actor, project_id, job.job_id, expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], request_hash=command_hash))
            if tail[2:] == ["monitors"] and method == "GET":
                return {"ok": True, "monitors": [asdict(value) for value in jobs.list_monitors(actor, project_id, job.job_id,
                    after=int(query.get("after", ["-1"])[0]), limit=limit)]}
            if len(tail) == 4 and tail[2] == "monitors" and method == "GET":
                raw = jobs.monitor_source(actor, project_id, job.job_id, int(tail[3]))
                return {"ok": True, "source_canonical_json": raw.decode(), "sha256": sha256(raw).hexdigest()}
            if tail[2:] == ["dataset"] and method == "GET":
                raw = jobs.blob(actor, project_id, job.job_id, "dataset.json")
                return BinarySource("dataset.json", raw, sha256(raw).hexdigest())
        raise RecordNotFound("Unknown project-owned study/run route.")
