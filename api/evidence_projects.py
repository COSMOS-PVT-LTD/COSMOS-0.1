"""Authenticated durable comparison/report DTO transport; no new science."""
from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid5

from api.geometry_projects import BinarySource
from systems.projects.authority import Principal, RecordNotFound, SavedSnapshot
from systems.projects.evidence_authority import (
    ASSESSMENT,
    LEDGER,
    LEDGER_ID,
    REPORT,
    ManagedEvidence,
    decode,
)


class EvidenceProjectAPI:
    def __init__(self, service: ManagedEvidence) -> None:
        self.service = service

    def envelope(self, actor: Principal, source: SavedSnapshot) -> dict[str, Any]:
        repo = self.service.repository
        current = repo.get_snapshot(actor, source.project_id, domain=source.domain, object_id=source.object_id)
        value = decode(source, source.domain)
        upstream = repo.dependencies_current(actor, source.project_id, source.commit_id)
        if source.domain == REPORT:
            upstream = self.service.report_current(actor, source)
        elif source.domain == ASSESSMENT:
            _, comparison = self.service.comparison(actor, source.project_id, source.object_id)
            upstream = comparison.report(actor.user_id, source.object_id)["freshness"] == "current"
        return {"ok": True, "authority": {"project_id": source.project_id, "domain": source.domain, "object_id": source.object_id,
            "commit_id": source.commit_id, "head": asdict(source.head), "input_revision": source.input_revision,
            "is_current": current.commit_id == source.commit_id}, "source_canonical_json": source.payload.decode(), "record": value,
            "upstream_current": upstream, "dependencies": [asdict(d) for d in repo.dependencies(actor, source.project_id, source.commit_id)],
            "source_namespace": source.source_namespace, "independent_acceptance": False, "production_handoff": False}

    def handle(self, actor: Principal, method: str, project_id: str, section: str, parts: list[str],
               query: dict[str, list[str]], body: dict[str, Any]) -> dict[str, Any] | BinarySource:
        from api.project_authority import _allowed, expected_head
        repo = self.service.repository
        command_hash = sha256(json.dumps({"project": project_id, "section": section, "path": parts, "body": body},
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        limit = int(query.get("limit", ["20"])[0])
        if section == "evidence":
            if not parts and method == "GET":
                try:
                    ledger = self.envelope(actor, self.service.ledger(actor, project_id))
                except RecordNotFound:
                    ledger = None
                return {"ok": True, "ledger": ledger, "ledger_id": LEDGER_ID, "assessments": [asdict(v) for v in repo.list_objects(
                    actor, project_id, domain=ASSESSMENT, limit=limit, after_id=query.get("after", [""])[0])],
                    "scope": "Project-owned software benchmark evidence; no independent acceptance"}
            if len(parts) == 2 and parts[0] == "assessments" and method == "GET":
                return self.envelope(actor, repo.get_snapshot(actor, project_id, domain=ASSESSMENT, object_id=parts[1]))
            if len(parts) == 3 and parts[0] == "assessments" and parts[2] == "review-intent" and method == "POST":
                _allowed(body, {"note", "expected", "operation_id"})
                return self.envelope(actor, self.service.review_comparison(actor, project_id, parts[1], body["note"],
                    expected=expected_head(body["expected"]), operation_id=body["operation_id"], command_hash=command_hash))
            fields = {"declare": {"criteria"}, "use-run": {"run_job_id"}, "reference": {"candidate_id"}, "import": {"dataset"},
                      "assess": {"candidate_id", "reference_id", "criteria_id"}}
            if len(parts) == 1 and parts[0] in fields and method == "POST":
                _allowed(body, fields[parts[0]] | {"expected", "operation_id"})
                action = self.service.assess if parts[0] == "assess" else self.service.command
                args = (actor, project_id, body) if parts[0] == "assess" else (actor, project_id, parts[0], body)
                return self.envelope(actor, action(*args, expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], command_hash=command_hash))
            if parts == ["history"] and method == "GET":
                return self.history(actor, project_id, LEDGER, LEDGER_ID, query)
            if parts == ["source"] and method == "GET":
                return self.envelope(actor, repo.get_snapshot(actor, project_id, domain=LEDGER, object_id=LEDGER_ID,
                    commit_id=query.get("commit", [None])[0]))
        elif section == "reports":
            if not parts and method == "GET":
                return {"ok": True, "reports": [asdict(v) for v in repo.list_objects(actor, project_id, domain=REPORT,
                    limit=limit, after_id=query.get("after", [""])[0])]}
            if method == "POST" and len(parts) <= 1:
                _allowed(body, {"title", "assessment_id", "claim_ids", "expected", "operation_id"})
                object_id = parts[0] if parts else str(uuid5(UUID(project_id), actor.user_id + ":report:" + body["operation_id"]))
                return self.envelope(actor, self.service.create_report(actor, project_id, object_id, body, expected=expected_head(body["expected"]),
                    operation_id=body["operation_id"], command_hash=command_hash))
            if parts:
                source = repo.get_snapshot(actor, project_id, domain=REPORT, object_id=parts[0], commit_id=query.get("commit", [None])[0])
                if len(parts) == 1 and method == "GET":
                    return self.envelope(actor, source)
                if parts[1:] == ["history"] and method == "GET":
                    return self.history(actor, project_id, REPORT, parts[0], query)
                if len(parts) == 3 and parts[1] == "files" and method == "GET":
                    raw = self.service.report_file(source, parts[2])
                    return BinarySource(parts[2], raw, sha256(raw).hexdigest())
                if parts[1:] == ["review-intent"] and method == "POST":
                    _allowed(body, {"note", "expected", "operation_id"})
                    return self.envelope(actor, self.service.review(actor, source, body["note"], expected=expected_head(body["expected"]),
                        operation_id=body["operation_id"], command_hash=command_hash))
        raise RecordNotFound("Unknown owning-project comparison/report route.")

    def history(self, actor: Principal, project_id: str, domain: str, object_id: str, query: dict[str, list[str]]) -> dict[str, Any]:
        repo = self.service.repository
        before = query.get("before", [None])[0]
        ids = repo.list_commit_ids(actor, project_id, domain=domain, object_id=object_id, limit=int(query.get("limit", ["20"])[0]),
            before_version=int(before) if before else None)
        return {"ok": True, "commits": [{"commit_id": s.commit_id, "head": asdict(s.head), "input_revision": s.input_revision}
            for s in (repo.get_snapshot(actor, project_id, domain=domain, object_id=object_id, commit_id=key) for key in ids)]}
