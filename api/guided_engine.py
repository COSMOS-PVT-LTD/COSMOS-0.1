"""Authorized guided design routes and trusted process composition; no equations."""

from __future__ import annotations

import json
import sys
from hashlib import sha256
from pathlib import Path

from api.geometry_projects import job_dto
from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.guided_engine.sources import package
from systems.guided_engine.resolution import PROFILE_ID, RULES, digest, exact, resolve
from systems.projects.authority import InvalidRecord, RecordNotFound
from systems.projects.guided_engine import DOMAIN, GuidedEngines


def methods():
    root = Path(__file__).resolve().parents[1]
    files = {
        p
        for name in (
            "core",
            "numerics",
            "physics",
            "systems/configuration",
            "systems/stages",
            "systems/workflow",
            "systems/guided_engine",
            "plugins/nasa_cea",
            "plugins/guided_engine",
        )
        for p in (root / name).rglob("*.py")
    }
    files.update(
        root / name
        for name in (
            "api/guided_engine.py",
            "systems/projects/guided_engine.py",
            "systems/projects/models.py",
            "systems/requirements/models.py",
            "systems/propellants/models.py",
        )
    )
    files.update((root / "plugins/guided_engine/data").glob("*.tsv"))
    return {
        str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest()
        for p in sorted(files)
    }


class Runner:
    def __init__(self):
        self.root = Path(__file__).resolve().parents[1]
        # env assignments are trusted host paths, never supplied by the UI.
        # PYTHONHOME is needed by the self-contained installed Python copy.
        self.command = WorkerCommand(
            (
                "/usr/bin/env",
                "PYTHONHOME=" + sys.base_prefix,
                sys.executable,
                "-B",
                "-m",
                "plugins.guided_engine.worker",
            ),
            (
                (
                    "PYTHONPATH",
                    str(self.root)
                    + ":"
                    + str(Path(sys.prefix) / "lib/python3.11/site-packages"),
                ),
                ("OPENBLAS_NUM_THREADS", "1"),
            ),
        )
        self.supervisor = WorkerSupervisor(
            max_workers=1, max_queued=2, timeout_s=120, stdout_limit=2 * 1024 * 1024
        )

    def submit(self, job_id, data):
        return self.supervisor.submit(job_id, self.command, data, self.root)

    def cancel(self, job_id):
        return self.supervisor.cancel(job_id)

    def close(self):
        self.supervisor.close()


class GuidedAPI:
    def __init__(self, api, jobs, resolve_actor):
        self.api = api
        self.service = GuidedEngines(
            api.repository, jobs, Runner(), methods, resolve_actor
        )

    def handle(self, actor, method, project, parts, query, body):
        from api.project_authority import expected_head

        repo, service = self.api.repository, self.service
        if query and not (method == "GET" and not parts and set(query) <= {"after"}):
            raise InvalidRecord(
                "Only a bounded guided listing cursor is supported; no ignored historical/runtime overrides."
            )
        request_hash = digest({"project": project, "path": parts, "body": body})
        if parts and parts[0] == "retained-cad" and method == "GET" and len(parts) <= 2:
            selected = None
            if len(parts) == 2:
                selected = repo.resolve_snapshot(actor, project, parts[1])
                if selected.domain != "propulsion":
                    raise InvalidRecord(
                        "CAD comparison requires an exact same-project propulsion commit"
                    )
            candidates = []
            for domain, segment, backend in (
                ("picogk-component-build", "picogk-component-builds", "PicoGK"),
                ("engine-component-build", "component-builds", "OCCT"),
            ):
                for ordinal, job_id in service.jobs.list_ids(
                    actor, project, domain=domain, limit=20
                ):
                    job = service.jobs.get(actor, project, job_id)
                    if job.state.value != "COMPLETED":
                        continue
                    captured = repo.resolve_snapshot(
                        actor, project, job.source_commit_id
                    )
                    model_commit = json.loads(captured.payload)["model_commit_id"]
                    model = repo.resolve_snapshot(actor, project, model_commit)
                    value = json.loads(model.payload)
                    path = (
                        "/api/projects/"
                        + project
                        + "/"
                        + segment
                        + "/"
                        + job.object_id
                        + "/jobs/"
                        + job.job_id
                    )
                    candidates.append(
                        {
                            "ordinal": ordinal,
                            "backend": backend,
                            "title": value["title"],
                            "job_id": job.job_id,
                            "model_commit_id": model_commit,
                            "physics_commit_id": value["baseline_commit_id"],
                            "matches_selected_physics": selected is not None
                            and selected.commit_id == value["baseline_commit_id"],
                            "detail_url": path,
                            "preview_url": path + "/preview",
                            "context_url": path
                            + (
                                "/mesh-context"
                                if backend == "PicoGK"
                                else "/review-context"
                            ),
                            "scope": "Retained preliminary geometry; no new calculation binding or engineering acceptance",
                        }
                    )
            return {
                "ok": True,
                "candidates": sorted(
                    candidates, key=lambda row: row["ordinal"], reverse=True
                ),
                "listing_scope": "Most recent20 attempts per component backend in this authorized project; no cross-root discovery or regeneration",
            }
        if parts == ["capabilities"] and method == "GET":
            return {
                "ok": True,
                "profile_id": PROFILE_ID,
                "scope": "Preliminary methalox pressure-fed target sizing; not full-engine qualification",
                "expert_mode_preserved": True,
                "generation": "ON_HOLD",
                "r08": "ON_HOLD",
                "property_package": package(),
                "profile_parameters": [
                    {
                        "key": k,
                        "value": v[0],
                        "unit": v[1],
                        "minimum": v[2],
                        "maximum": v[3],
                        "basis": v[5],
                    }
                    for k, v in RULES.items()
                ],
            }
        if parts == ["preview"] and method == "POST":
            exact(body, {"brief", "overrides", "profile_id"}, "Guided preview")
            if body["profile_id"] != PROFILE_ID:
                raise InvalidRecord(
                    "No matching reviewed guided profile; no substitution."
                )
            return {
                "ok": True,
                "persisted": False,
                "resolution": resolve(
                    body["brief"], body["overrides"], package(), methods()
                ),
            }
        if not parts:
            if method == "GET":
                rows = repo.list_objects(
                    actor,
                    project,
                    domain=DOMAIN,
                    limit=20,
                    after_id=query.get("after", [""])[0],
                )
                return {
                    "ok": True,
                    "inputs": [
                        service.envelope(
                            actor,
                            repo.get_snapshot(
                                actor, project, domain=DOMAIN, object_id=r.object_id
                            ),
                        )
                        for r in rows
                    ],
                }
            exact(
                body,
                {"brief", "overrides", "profile_id", "review_hash", "operation_id"},
                "Guided acceptance",
            )
            if body["profile_id"] != PROFILE_ID:
                raise InvalidRecord("Unknown guided profile")
            plan = resolve(body["brief"], body["overrides"], package(), methods())
            if body["review_hash"] != plan["review_hash"]:
                raise InvalidRecord(
                    "The brief, sources or methods changed since review. Review the new basis before accepting."
                )
            return service.envelope(
                actor,
                service.accept(
                    actor, project, plan, body["operation_id"], request_hash
                ),
            )
        if len(parts) == 1 and method == "GET":
            return service.envelope(
                actor,
                repo.get_snapshot(actor, project, domain=DOMAIN, object_id=parts[0]),
            )
        if len(parts) == 2 and parts[1] == "jobs":
            source = repo.get_snapshot(
                actor, project, domain=DOMAIN, object_id=parts[0]
            )
            if method == "GET":
                return {
                    "ok": True,
                    "attempts": [
                        job_dto(service.jobs.get(actor, project, job_id), detail=False)
                        for _, job_id in service.jobs.list_ids(
                            actor,
                            project,
                            object_id=source.object_id,
                            domain=DOMAIN,
                            limit=20,
                        )
                    ],
                }
            exact(body, {"expected", "operation_id"}, "Guided run")
            if source.head != expected_head(body["expected"]):
                raise InvalidRecord("Accepted guided input head changed")
            return job_dto(
                service.start(actor, source, body["operation_id"], request_hash)
            )
        if len(parts) in {3, 4} and parts[1] == "jobs":
            job = service.jobs.get(actor, project, parts[2])
            if job.domain != DOMAIN or job.object_id != parts[0]:
                raise RecordNotFound("Attempt is not owned by this exact guided source")
            if len(parts) == 3 and method == "GET":
                response = job_dto(job)
                value = json.loads(job.payload)
                response["result"] = value
                commit = value.get("design_commit_id")
                if commit:
                    saved = repo.resolve_snapshot(actor, project, commit)
                    head = repo.get_snapshot(
                        actor, project, domain="propulsion", object_id=saved.object_id
                    )
                    response["result_current"] = (
                        saved.commit_id == head.commit_id
                        and service.envelope(
                            actor,
                            repo.resolve_snapshot(actor, project, job.source_commit_id),
                        )["methods_current"]
                    )
                return response
            if parts[3:] == ["cancel"] and method == "POST":
                exact(body, {"expected", "operation_id"}, "Guided cancellation")
                return job_dto(
                    service.cancel(
                        actor,
                        project,
                        job.job_id,
                        expected_head(body["expected"]),
                        body["operation_id"],
                        request_hash,
                    )
                )
        raise RecordNotFound(
            "Unsupported guided action; no migrate, purge, native build or engineering-release route"
        )
