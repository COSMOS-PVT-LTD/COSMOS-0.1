"""Exact authorized cross-workbench source navigation and bounded activity."""
from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid5

from api.geometry_projects import job_dto
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    Head,
    HeadConflict,
    InvalidRecord,
    Principal,
    RecordNotFound,
)


def record(api: Any, actor: Principal, project_id: str, commit_id: str) -> dict[str, Any]:
    repo = api.repository
    source = repo.resolve_snapshot(actor, project_id, commit_id)
    head = repo.get_snapshot(actor, project_id, domain=source.domain, object_id=source.object_id)
    deps = repo.dependencies(actor, project_id, commit_id)
    applicable = repo.dependencies_current(actor, project_id, commit_id)
    if source.domain == "engineering-report" and api.evidence is not None:
        applicable = api.evidence.service.report_current(actor, source)
    elif source.domain == "comparison-assessment" and api.evidence is not None:
        _, assessment = api.evidence.service.comparison(actor, project_id, source.object_id)
        applicable = assessment.report(actor.user_id, source.object_id)["freshness"] == "current"
    elif source.domain == "simulation-benchmark" and api.studies is not None:
        applicable = applicable and api.studies.envelope(actor, source)["methods_current"]
    elif source.domain == "propulsion-sensitivity" and api.sensitivity is not None:
        applicable = api.sensitivity.service.read(actor, source)["upstream_current"]
    elif source.domain == "pressure-fed-assessment" and api.pressure_fed is not None:
        applicable = api.pressure_fed.service.read(actor, source)["upstream_current"]
    elif source.domain == "coupled-cycle-assessment" and api.cycle_assessments is not None:
        applicable = api.cycle_assessments.service.read(actor, source)["upstream_current"]
    elif source.domain == "engine-operating-point" and api.engine_operating is not None:
        applicable = api.engine_operating.service.read(actor, source)["upstream_current"]
    elif source.domain == "operating-sensitivity" and api.operating_sensitivity is not None:
        applicable = api.operating_sensitivity.service.read(actor, source)["upstream_current"]
    elif source.domain == "engine-geometry-intent" and api.engine_geometry is not None:
        applicable = api.engine_geometry.service.read(actor, source)["upstream_current"]
    elif source.domain == "engine-nozzle-build" and api.engine_builds is not None:
        applicable = api.engine_builds.coordinator.current(actor, source)
    elif source.domain == "engine-component-model" and api.components is not None:
        applicable = api.components.models.current(actor,source)
    elif source.domain == "engine-component-build" and api.components is not None:
        applicable = api.components.builds.coordinator.current(actor,source)
    elif source.domain in {"engine-component-review","engine-component-study"} and api.components is not None:
        applicable = api.components.evidence(actor,source)["upstream_current"]
    elif source.domain in {"propulsion-validation-plan", "propulsion-measurement", "propulsion-validation-assessment"} and api.propulsion_validation is not None:
        applicable = api.propulsion_validation.service.read(actor, source)["upstream_current"]
    upstream = [{**asdict(d), "source": "/api/projects/" + project_id + "/records/" + d.commit_id,
        "job": "/api/projects/" + project_id + "/jobs/" + d.job_id if d.job_id else None} for d in deps]
    return {"ok": True, "authority": {"project_id": project_id, "domain": source.domain, "object_id": source.object_id,
        "commit_id": source.commit_id, "head": asdict(source.head), "input_revision": source.input_revision,
        "is_current": source.commit_id == head.commit_id, "purpose": source.purpose, "current_head": asdict(head.head)}, "source_canonical_json": source.payload.decode(),
        "upstream_current": applicable, "upstream": upstream,
        "origin": "/api/projects/" + project_id + "/records/" + source.source_commit_id if source.source_commit_id else None,
        "scope": "Exact retained source; CURRENT is freshness, not scientific validation or engineering acceptance"}


def handle(api: Any, actor: Principal, method: str, project_id: str, parts: list[str], query: dict[str, list[str]], body: dict[str, Any]) -> dict[str, Any]:
    from api.project_authority import _allowed, expected_head
    repo = api.repository
    limit = int(query.get("limit", ["20"])[0])
    if parts == ["domains"] and method == "GET":
        return {"ok": True, "domains": repo.list_domains(actor, project_id, limit=limit, after=query.get("after", [""])[0])}
    if parts == ["context"] and method == "GET":
        domain = query.get("domain", [None])[0]
        return {"ok": True, "project": asdict(repo.get_project(actor, project_id)),
            "domains": repo.list_domains(actor, project_id, limit=20), "domain": domain,
            "objects": [asdict(v) for v in repo.list_objects(actor, project_id, domain=domain, limit=limit, after_id=query.get("after", [""])[0])] if domain else [],
            "source_of_truth": "Authenticated server project/commit IDs; browser preferences are not authority"}
    if parts == ["timeline"] and method == "GET":
        before = query.get("before", [None])[0]
        return {"ok": True, "events": repo.project_events(actor, project_id, limit=limit, before=int(before) if before else None)}
    if parts and parts[0] == "jobs" and method == "GET" and api.geometry is not None:
        jobs = api.geometry.coordinator.jobs
        if len(parts) == 1:
            before = query.get("before", [None])[0]
            ids = jobs.list_ids(actor, project_id, limit=limit, before=int(before) if before else None,
                object_id=query.get("object", [None])[0], domain=query.get("domain", [None])[0])
            return {"ok": True, "attempts": [{"ordinal": order, "domain": job.domain, **job_dto(job, detail=False)} for order, key in ids for job in (jobs.get(actor, project_id, key),)]}
        if len(parts) == 2:
            job = jobs.get(actor, project_id, parts[1])
            return {"ok": True, "domain": job.domain, **job_dto(job), "input_source": "/api/projects/" + project_id + "/records/" + job.source_commit_id}
        if len(parts) == 3 and parts[2] == "plots" and api.evidence is not None:
            from systems.visualization.plots import simulation_plots
            run = api.evidence.service.run(actor, project_id, parts[1])
            return simulation_plots(json.loads(run.raw))
    if len(parts) == 4 and parts[0] == "objects" and parts[3] == "history" and method == "GET":
        before = query.get("before", [None])[0]
        ids = repo.list_commit_ids(actor, project_id, domain=parts[1], object_id=parts[2], limit=limit, before_version=int(before) if before else None)
        return {"ok": True, "commits": [{"commit_id": s.commit_id, "head": asdict(s.head), "input_revision": s.input_revision}
            for s in (repo.resolve_snapshot(actor, project_id, key) for key in ids)]}
    if parts and parts[0] == "records" and len(parts) in {2, 3}:
        if len(parts) == 2 and method == "GET":
            return record(api, actor, project_id, parts[1])
        if len(parts) == 3 and parts[2] == "plots" and method == "GET":
            from systems.projects.propulsion_authority import decode_design
            from systems.visualization.plots import design_plots
            source = repo.resolve_snapshot(actor, project_id, parts[1])
            current = repo.get_snapshot(actor, project_id, domain=source.domain, object_id=source.object_id)
            if source.commit_id != current.commit_id:
                raise InvalidRecord("Current plot contract refuses historical sources; inspect their exact retained bytes instead.")
            return design_plots(decode_design(source))
        if len(parts) == 3 and parts[2] in {"activate", "branch"} and method == "POST":
            _allowed(body, {"expected", "operation_id"})
            command_hash = sha256(json.dumps({"project": project_id, "path": parts, "body": body}, sort_keys=True, allow_nan=False).encode()).hexdigest()
            replay = repo.resolve_command(actor, project_id, operation_id=body["operation_id"], command_hash=command_hash)
            if replay is not None:
                return record(api, actor, project_id, replay.commit_id)
            source = repo.resolve_snapshot(actor, project_id, parts[1])
            if source.domain not in {"geometry-fixture", "simulation-benchmark"}:
                raise InvalidRecord("Use domain-specific propulsion history; derived evidence is immutable, not activated as fresh results.")
            current = repo.get_snapshot(actor, project_id, domain=source.domain, object_id=source.object_id)
            expected = expected_head(body["expected"])
            if current.head != expected:
                raise HeadConflict(current.head)
            branch = parts[2] == "branch"
            object_id = str(uuid5(UUID(project_id), actor.user_id + ":" + body["operation_id"])) if branch else source.object_id
            saved = repo.save_snapshot(actor, project_id, domain=source.domain, object_id=object_id,
                input_revision=0 if branch else current.input_revision + 1,
                payload=RecordPayload(source.payload, source.schema_id, source.source_namespace), expected=Head.absent() if branch else expected,
                operation_id=body["operation_id"], command_hash=command_hash, purpose=parts[2], source_commit_id=source.commit_id,
                dependencies=repo.dependencies(actor, project_id, source.commit_id))
            return record(api, actor, project_id, saved.commit_id)
    if parts == ["requirements"] and method == "POST":
        _allowed(body, {"requirements", "components", "expected", "operation_id"})
        requirements, components = body["requirements"], body["components"]
        if type(requirements) is not list or len(requirements) > 64 or any(type(r) is not str or not 0 < len(r.strip()) <= 4096 or "\0" in r for r in requirements):
            raise InvalidRecord("Use at most64 explicit bounded requirement statements; no inferred acceptance criteria.")
        if type(components) is not list or len(components) > 16 or len(set(components)) != len(components):
            raise InvalidRecord("Select at most16 distinct exact owning-project component commits.")
        deps = tuple(Dependency("component-" + str(i), repo.resolve_snapshot(actor, project_id, key).commit_id) for i, key in enumerate(components))
        expected = expected_head(body["expected"])
        source = repo.save_snapshot(actor, project_id, domain="project-definition", object_id="mission", input_revision=expected.version,
            payload=RecordPayload.from_mapping({"requirements": requirements, "components": components,
                "scope": "Recorded project intent; not independently accepted engineering requirements"}, "cosmos.project-definition.v1"),
            expected=expected, operation_id=body["operation_id"], dependencies=deps)
        return record(api, actor, project_id, source.commit_id)
    raise RecordNotFound("Unknown exact project context/history route.")
