"""Authenticated candidate editing and development selection; no engineering release."""

import json
from dataclasses import asdict
from hashlib import sha256
from uuid import UUID, uuid5

from api.project_authority import expected_head
from core.serialization import canonical_json_dumps
from systems.geometry.engine_redesign_authority import DOMAIN, Redesigns
from systems.projects.authority import Head, InvalidRecord, RecordNotFound


def fields(body, names):
    if type(body) is not dict or set(body) != set(names):
        raise InvalidRecord(
            "Exact redesign fields required; posted geometry/results/paths/runtime overrides are forbidden"
        )


def handle(components, actor, method, project, parts, query, body):
    service = getattr(components, "redesigns", None)
    if service is None:
        service = components.redesigns = Redesigns(components)
    repo = components.repository
    repo.get_project(actor, project)
    if parts and parts[0] == "active-baseline":
        if query:
            raise InvalidRecord(
                "Development baseline actions do not accept query overrides"
            )
        from systems.geometry.development_baseline import DevelopmentBaselines

        baselines = getattr(service, "baselines", None)
        if baselines is None:
            baselines = service.baselines = DevelopmentBaselines(service)
        if parts == ["active-baseline"] and method == "GET":
            return baselines.current(actor, project)
        if parts == ["active-baseline", "history"] and method == "GET":
            return baselines.history(actor, project)
        if method == "POST" and parts in (
            ["active-baseline"],
            ["active-baseline", "rollback"],
        ):
            rollback = len(parts) == 2
            fields(
                body,
                ("expected", "operation_id", "reason")
                if rollback
                else (
                    "candidate_commit_id",
                    "expected_candidate",
                    "expected",
                    "operation_id",
                    "reason",
                ),
            )
            digest = sha256(
                canonical_json_dumps(
                    {"project": project, "action": parts, "body": body}
                ).encode()
            ).hexdigest()
            kwargs = {
                "expected": expected_head(body["expected"]),
                "operation_id": body["operation_id"],
                "command_hash": digest,
                "reason": body["reason"],
            }
            if rollback:
                return baselines.rollback(actor, project, **kwargs)
            return baselines.activate(
                actor,
                project,
                candidate_commit_id=body["candidate_commit_id"],
                expected_candidate=expected_head(body["expected_candidate"]),
                **kwargs,
            )
        raise RecordNotFound(
            "Unsupported development selection action; no purge or engineering release route"
        )
    allowed = (
        {"after"}
        if method == "GET" and not parts
        else {"commit"}
        if method == "GET"
        and (len(parts) == 1 or len(parts) == 2 and parts[1] == "recipe")
        else set()
    )
    if set(query) - allowed or any(len(v) != 1 or not v[0] for v in query.values()):
        raise InvalidRecord(
            "Only bounded listing cursors or an exact read revision are supported"
        )
    if method == "POST" and parts == ["seed"]:
        fields(body, ("source_commit_id",))
        return service.seed(actor, project, body["source_commit_id"])
    if method == "POST" and parts == ["preview"]:
        fields(body, ("source_commit_id", "specification"))
        return service.preview(
            actor, project, body["source_commit_id"], body["specification"]
        )
    if method == "GET" and not parts:
        return {
            "ok": True,
            "candidates": [
                asdict(v)
                for v in repo.list_objects(
                    actor,
                    project,
                    domain=DOMAIN,
                    limit=20,
                    after_id=query.get("after", [""])[0],
                )
            ],
        }
    if method == "POST" and len(parts) <= 1:
        fields(
            body,
            (
                "title",
                "source_commit_id",
                "expected_source",
                "specification",
                "expected",
                "operation_id",
            ),
        )
        expected = expected_head(body["expected"])
        if (
            type(body["operation_id"]) is not str
            or not 0 < len(body["operation_id"]) <= 128
        ):
            raise InvalidRecord("Bounded explicit operation ID required")
        if not parts and expected != Head.absent():
            raise InvalidRecord("New candidate requires absent head")
        object_id = (
            parts[0]
            if parts
            else str(
                uuid5(
                    UUID(project),
                    actor.user_id + ":engine-redesign:" + body["operation_id"],
                )
            )
        )
        digest = sha256(
            canonical_json_dumps(
                {"project": project, "object": object_id, "body": body}
            ).encode()
        ).hexdigest()
        saved = service.save(
            actor,
            project,
            object_id,
            body,
            expected,
            expected_head(body["expected_source"]),
            digest,
        )
        return service.envelope(actor, saved)
    if method == "GET" and 1 <= len(parts) <= 2:
        saved = repo.get_snapshot(
            actor,
            project,
            domain=DOMAIN,
            object_id=parts[0],
            commit_id=query.get("commit", [None])[0],
        )
        if len(parts) == 1:
            return service.envelope(actor, saved)
        if parts[1] == "history" and not query:
            ids = repo.list_commit_ids(
                actor, project, domain=DOMAIN, object_id=parts[0]
            )
            return {
                "ok": True,
                "commits": [
                    {
                        "commit_id": s.commit_id,
                        "head": asdict(s.head),
                        "input_revision": s.input_revision,
                    }
                    for s in (repo.resolve_snapshot(actor, project, c) for c in ids)
                ],
            }
        if parts[1] == "recipe" and query:
            value = json.loads(saved.payload)
            from systems.geometry.component_authority import from_source
            from systems.geometry.engine_redesign import compile_candidate

            source = repo.resolve_snapshot(actor, project, value["source_commit_id"])
            service._stable()
            if value["method_sources"] != service.loaded_methods:
                raise InvalidRecord(
                    "Historical compiler recipe cannot be regenerated with changed methods"
                )
            candidate = compile_candidate(from_source(source), value["specification"])
            return {
                "ok": True,
                "recipe": candidate.wire(),
                "authority": service.envelope(actor, saved)["authority"],
            }
    raise RecordNotFound(
        "Unsupported redesign action; activation/build/qualification are not exposed"
    )
