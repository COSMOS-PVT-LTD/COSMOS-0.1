"""Authenticated bounded read-only knowledge and immutable report transport."""
from __future__ import annotations

import hashlib
from typing import Any
from urllib.parse import unquote, urlparse

from api.authentication import UserRole
from api.ngg_workbench import read_payload, transport_guard
from knowledge.workspace.evidence_navigation import EvidenceNavigation
from systems.contracts.geometry._wire import GeometryContractError, require
from validation.contracts import fields
from validation.reporting import EngineeringReports

ASSETS = frozenset({"model.js", "view.js", "styles.css", "graph.js"})
CATALOG_ITEM = {"workbench_id": "reports", "title": "Reports, History and Governance", "route": "/app/workbench/reports", "status": "active", "page": 1,
                "description": "Reproducible research review packages; independent acceptance pending", "validation_state": "EVIDENCE_PREVIEW_ONLY"}


def dispatch(handler: Any, path: str, session: Any, *, mutation: bool) -> None:
    app = handler.application
    if not app.knowledge_reports_enabled:
        return handler._json(404, {"error": "knowledge_reports_disabled"})
    if session is None:
        return handler._json(401, {"error": "authentication_required"})
    try:
        transport_guard(handler, mutation=mutation)
        require(not urlparse(handler.path).query, "INVALID_REQUEST", "No ambiguous API query fields")
        action = path.removeprefix("/api/knowledge-reports/")
        if mutation:
            length = handler.headers.get("Content-Length", "")
            require(length.isascii() and length.isdecimal() and 0 < int(length) <= 16*1024, "BODY_LIMIT", "Report requests are bounded to 16KiB")
        body = read_payload(handler) if mutation else {}
        expected = {"search": {"query", "offset"}, "generate": {"title", "receipt_id", "claim_ids"}, "review-intent": {"report_id", "note"}}
        if mutation:
            require(action in expected, "ENGINEERING_ACCEPTANCE_REQUIRED" if action == "production-handoff" else "UNKNOWN_ROUTE", "No independent acceptance or production publication is available in this preview")
            fields(body, expected[action])
            if action != "search":
                allowed = {UserRole.ADMIN, UserRole.ENGINEER} if action == "generate" else {UserRole.ADMIN, UserRole.ENGINEER, UserRole.REVIEWER, UserRole.APPROVER}
                require(session.user.role in allowed, "FORBIDDEN_ROLE", "This role may inspect but cannot perform this report operation")
        actor = session.user.login_id
        with app._workspace_lock:
            navigation = EvidenceNavigation(app.knowledge_workspace())
            reports = app.reports_workspace()
            if not mutation:
                if action == "context":
                    return handler._json(200, {"knowledge": navigation.context(), "reports": reports.context(actor),
                        "comparison_receipts": app._comparison_workspace.context(actor)["report_ids"] if app._comparison_workspace else [],
                        "scope": "Source-aware knowledge and research reports; not independent engineering acceptance"})
                parts = action.split("/")
                if len(parts) == 2 and parts[0] in {"sources", "claims"}:
                    return handler._json(200, navigation.source(unquote(parts[1])) if parts[0] == "sources" else navigation.claim(unquote(parts[1])))
                require(len(parts) in {2, 3} and parts[0] == "reports", "UNKNOWN_ROUTE", "Unknown report evidence route")
                value = reports.get(actor, parts[1], app._comparison_workspace, app._simulation_workspace, app._ngg_workspace, navigation)
                if len(parts) == 2:
                    return handler._json(200, value)
                require(parts[2] in {"json", "md", "html", "package"}, "UNSUPPORTED_EXPORT", "Only JSON, Markdown, escaped HTML and ZIP review packages are supported")
                raw = reports.package(actor, parts[1]) if parts[2] == "package" else reports.files(actor, parts[1])["report."+parts[2]]
                filename = "COSMOS-P11-"+value["report_id"]+(".zip" if parts[2] == "package" else "."+parts[2])
                mime = {"package": "application/zip", "json": "application/json", "md": "text/markdown; charset=utf-8", "html": "text/html; charset=utf-8"}[parts[2]]
                handler.send_response(200); handler.send_header("Content-Type", mime); handler.send_header("Content-Length", str(len(raw)))
                handler.send_header("Content-Disposition", 'attachment; filename="'+filename+'"')
                handler.send_header("X-Content-Type-Options", "nosniff"); handler.send_header("X-COSMOS-SHA256", hashlib.sha256(raw).hexdigest())
                handler.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; sandbox")
                handler.end_headers(); handler.wfile.write(raw)
                return None
            if action == "search":
                value = navigation.context(body["query"], body["offset"])
            elif action == "generate":
                require(app._comparison_workspace is not None and app._simulation_workspace is not None and app._ngg_workspace is not None,
                        "SOURCE_UNAVAILABLE", "Create a current actual P09/P10 comparison before generating a report")
                value = reports.create(actor, body["title"], body["receipt_id"], body["claim_ids"], app._comparison_workspace, app._simulation_workspace, app._ngg_workspace, navigation)
            else:
                value = reports.review(actor, body["report_id"], body["note"])
            handler._audit_request(session, path)
            return handler._json(200, value)
    except (GeometryContractError, ValueError, TypeError, KeyError, OSError, RuntimeError, MemoryError) as error:
        handler.close_connection = True
        code = getattr(error, "code", "INVALID_REQUEST")
        return handler._json(403 if code in {"FORBIDDEN_ROLE", "ENGINEERING_ACCEPTANCE_REQUIRED"} else 409 if code in {"CURRENT_RUN_REQUIRED", "PROVENANCE_MISMATCH"} else 400,
            {"ok": False, "error": {"code": code, "message": str(error)[:1024], "cause": str(error)[:1024],
                                   "action": "Inspect exact source/checksum, recorded review and current study lineage; retry or omit unavailable knowledge. No independent acceptance is granted."}})


def create_workspace() -> EngineeringReports:
    return EngineeringReports()
