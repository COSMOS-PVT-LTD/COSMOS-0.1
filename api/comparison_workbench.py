"""Strict authenticated loopback comparison transport; references are never fetched."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from api.authentication import UserRole
from api.ngg_workbench import read_payload, transport_guard
from systems.contracts.geometry._wire import GeometryContractError, require

if TYPE_CHECKING:
    from validation.workbench import ComparisonWorkbench

ASSETS = frozenset({"model.js", "view.js", "styles.css"})
CATALOG_ITEM = {"workbench_id": "comparison", "title": "Comparison and V&V", "route": "/app/workbench/comparison", "status": "active", "page": 1,
                "description": "Scoped comparisons and evidence; not independent engineering acceptance", "validation_state": "EVIDENCE_PREVIEW_ONLY"}


def dispatch(handler: Any, path: str, session: Any, *, mutation: bool) -> None:
    app = handler.application
    if not app.comparison_enabled:
        return handler._json(404, {"error": "comparison_disabled"})
    if session is None:
        return handler._json(401, {"error": "authentication_required"})
    try:
        transport_guard(handler, mutation=mutation)
        require(not urlparse(handler.path).query, "INVALID_REQUEST", "No ambiguous query parameters")
        action = path.removeprefix("/api/comparison/")
        allowed_review = action == "review-intent" and session.user.role in {UserRole.REVIEWER, UserRole.APPROVER}
        require(not mutation or allowed_review or session.user.role in {UserRole.ADMIN, UserRole.ENGINEER}, "FORBIDDEN_ROLE", "Engineer/Admin required for evidence mutations; review intent does not approve engineering use")
        if action == "production-handoff":
            raise GeometryContractError("ENGINEERING_ACCEPTANCE_REQUIRED", "P10 evidence preview is not a trusted independent approval/publication authority")
        if mutation:
            length = handler.headers.get("Content-Length", "")
            require(length.isascii() and length.isdecimal() and 0 < int(length) <= 2300 * 1024, "REQUEST_TOO_LARGE", "Bounded JSON evidence request required")
            payload = read_payload(handler)
            schemas = {"use-run": {"run_id"}, "criteria": {"criteria"}, "analytic": {"candidate_id"}, "import": {"dataset"},
                       "assess": {"candidate_id", "reference_id", "criteria_id"}, "review-intent": {"report_id", "note"},
                       "capture-geometry": {"job_id", "snapshot_id"}, "compare-geometry": {"left_id", "right_id"}, "import-step": {"base64", "provenance"}}
            require(action in schemas and set(payload) == schemas[action], "INVALID_REQUEST", "Exact operation fields required; no paths, commands or approval flags")
            for key, value in payload.items():
                if key.endswith("_id"):
                    require(type(value) is str and 0 < len(value) <= 128, "INVALID_REQUEST", "Bounded lineage identifier required")
        manager = app.comparison_workspace(); actor = session.user.login_id
        if not mutation:
            if action == "context":
                return handler._json(200, manager.context(actor))
            parts = action.split("/")
            require(len(parts) == 2 and parts[0] == "reports", "UNKNOWN_ROUTE", "Unknown evidence route")
            return handler._json(200, manager.report(actor, parts[1], app._simulation_workspace, app._ngg_workspace))
        if action in {"use-run", "capture-geometry", "import-step"}:
            require(app.ngg_enabled, "GEOMETRY_REQUIRED", "Qualified local native runtime required")
            geometry = app.ngg_workspace()
        if action == "use-run":
            require(app.simulation_enabled, "SIMULATION_REQUIRED", "Enable P09 and create an actual current run")
            value = manager.use_run(actor, app.simulation_workspace(), geometry, payload["run_id"])
        elif action == "criteria":
            value = manager.declare(actor, payload["criteria"])
        elif action == "analytic":
            value = manager.reference(actor, payload["candidate_id"])
        elif action == "import":
            value = manager.imported(actor, payload["dataset"])
        elif action == "assess":
            value = manager.assess(actor, payload["candidate_id"], payload["reference_id"], payload["criteria_id"],
                                   app.simulation_workspace() if app.simulation_enabled else None, app.ngg_workspace() if app.ngg_enabled else None)
        elif action == "review-intent":
            value = manager.review(actor, payload["report_id"], payload["note"])
        elif action == "capture-geometry":
            value = manager.capture(actor, geometry, payload["job_id"], payload["snapshot_id"])
        elif action == "compare-geometry":
            value = manager.compare_geometry(actor, payload["left_id"], payload["right_id"])
        else:
            value = manager.import_step(actor, geometry, payload["base64"], payload["provenance"])
        handler._audit_request(session, path)
        return handler._json(200, value)
    except (GeometryContractError, ValueError, KeyError, TypeError, OSError, MemoryError) as error:
        handler.close_connection = True
        code = getattr(error, "code", "INVALID_REQUEST")
        return handler._json(403 if code in {"FORBIDDEN_ROLE", "ENGINEERING_ACCEPTANCE_REQUIRED"} else 409 if code.startswith("STALE") else 400,
            {"ok": False, "error": {"code": code, "message": str(error)[:1024], "cause": str(error)[:1024],
                                   "action": "Inspect units, frame, conditions, provenance and criteria ordering; retry a new evidence snapshot. Independent engineering acceptance remains pending."}})


def create_workspace(root: Any) -> ComparisonWorkbench:
    from validation.workbench import ComparisonWorkbench
    return ComparisonWorkbench(root)
