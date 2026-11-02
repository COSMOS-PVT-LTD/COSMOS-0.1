"""Authenticated loopback-only P09 software study transport; strict schemas."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from api.authentication import UserRole
from api.ngg_workbench import read_payload, transport_guard
from systems.contracts.geometry._wire import GeometryContractError, require

if TYPE_CHECKING:
    from simulation.workbench import SimulationWorkbench

ASSETS = frozenset({"model.js", "view.js", "styles.css"})


def dispatch(handler: Any, path: str, session: Any, *, mutation: bool) -> None:
    app = handler.application
    if not app.simulation_enabled:
        return handler._json(404, {"error": "simulation_disabled"})
    if session is None:
        return handler._json(401, {"error": "authentication_required"})
    try:
        transport_guard(handler, mutation=mutation)
        require(not urlparse(handler.path).query, "INVALID_REQUEST", "No ambiguous query parameters permitted")
        require(not mutation or session.user.role in {UserRole.ENGINEER, UserRole.ADMIN}, "FORBIDDEN_ROLE", "Engineer or Admin required for study mutations")
        manager = app.simulation_workspace()
        actor = session.user.login_id
        action = path.removeprefix("/api/simulation/")
        if not mutation:
            if action == "context":
                return handler._json(200, manager.context(actor))
            parts = action.split("/")
            require(len(parts) in {2, 3} and parts[0] == "runs", "UNKNOWN_ROUTE", "Unknown study route")
            if len(parts) == 3:
                require(parts[2] == "dataset", "UNKNOWN_ROUTE", "Unknown dataset route")
                return handler._json(200, manager.dataset(actor, parts[1]))
            require(app.ngg_enabled, "GEOMETRY_REQUIRED", "Enable qualified local geometry for source lineage")
            return handler._json(200, manager.status(actor, app.ngg_workspace(), parts[1]))
        if action == "production-handoff":
            raise GeometryContractError("ENGINEERING_ACCEPTANCE_REQUIRED", "No trusted engineering publication/review authority; fixture acceptance is insufficient")
        length = handler.headers.get("Content-Length", "")
        require(length.isascii() and length.isdecimal() and 0 < int(length) <= 32 * 1024, "REQUEST_TOO_LARGE", "Study request limit is 32KiB")
        payload = read_payload(handler)
        schemas = {"handoff": {"job_id", "snapshot_id"}, "settings": {"study_id", "settings"},
                   "activate": {"study_id"}, "run": {"study_id"}, "cancel": {"run_id"}}
        require(action in schemas and set(payload) == schemas[action], "INVALID_REQUEST", "Exact fields required; no file paths, native commands or client success flags")
        require(all(type(value) is str and 0 < len(value) <= 128 for key, value in payload.items() if key != "settings"), "INVALID_REQUEST", "Bounded exact lineage identifiers required")
        if action in {"handoff", "run"}:
            require(app.ngg_enabled, "GEOMETRY_REQUIRED", "Build an independently accepted current OCCT sphere first")
            geometry = app.ngg_workspace()
            value = manager.attach(actor, geometry, payload["job_id"], payload["snapshot_id"]) if action == "handoff" else manager.submit(actor, geometry, payload["study_id"])
        elif action == "settings":
            value = manager.change(actor, payload["study_id"], payload["settings"])
        elif action == "activate":
            value = manager.activate(actor, payload["study_id"])
        else:
            value = manager.cancel(actor, payload["run_id"])
        handler._audit_request(session, path)
        return handler._json(200, value)
    except (GeometryContractError, ValueError, KeyError, TypeError, OSError, MemoryError) as error:
        handler.close_connection = True
        code = error.code if isinstance(error, GeometryContractError) else "MEMORY_LIMIT" if isinstance(error, MemoryError) else "INVALID_REQUEST"
        return handler._json(403 if code in {"FORBIDDEN_ROLE", "ENGINEERING_ACCEPTANCE_REQUIRED"} else 409 if code.startswith("STALE") else 400,
            {"ok": False, "error": {"code": code, "message": str(error)[:1024], "cause": str(error)[:1024],
                                   "action": "Inspect source/selection and exact study; correct settings or retry. Production handoff remains blocked."}})


def create_workspace() -> SimulationWorkbench:
    from simulation.workbench import SimulationWorkbench
    return SimulationWorkbench()


def catalog_item(item: dict[str, Any]) -> dict[str, Any]:
    return {**item, "title": "Simulation · software benchmark", "status": "active",
            "description": "Steady spherical conduction benchmark; no engineering CFD/FEA publication",
            "modules": ["Study", "Radial mesh", "Solver", "Monitoring", "Field profile"], "validation_state": "SOFTWARE_BENCHMARK_ONLY"}
