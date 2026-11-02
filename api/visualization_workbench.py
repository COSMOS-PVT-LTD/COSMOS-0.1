"""Authenticated read-only visualization bridge; source services own all state."""
from urllib.parse import urlparse

from api.propulsion_workflow import load_design, map_systems_error
from core.exceptions import CosmosError
from systems.visualization.plots import design_plots, simulation_plots

ASSETS = frozenset({"view.js", "chart.js", "exports.js", "styles.css", "knowledge-graph.js"})
VENDOR_ASSETS = frozenset({"three/three.module.js", "three/three.core.js", "three/OrbitControls.js", "echarts/echarts.min.js"})


def dispatch(handler, path, session):
    if session is None:
        return handler._json(401, {"error": "authentication_required"})
    if handler.command != "GET" or urlparse(handler.path).query:
        return handler._json(400, {"error": "Read-only exact visualization routes are required"})
    action = path.removeprefix("/api/visualization/")
    try:
        if action == "context":
            return handler._json(200, {"schema_version": "cosmos-plots-v1", "designs": handler.application.design_store.list_summaries(),
                "simulation_enabled": handler.application.simulation_enabled,
                "capabilities": ["current nozzle/cooling profiles", "P09 radial temperature, residual and conservation histories"],
                "limitations": ["No new solver, arbitrary CSV import, 3D field map or physical validation", "Historical snapshots remain unavailable"]})
        if action.startswith("designs/") and "/" not in action.removeprefix("designs/"):
            design = load_design(action.removeprefix("designs/"), handler.application.design_store)
            return handler._json(200, design_plots(design))
        if action.startswith("simulation/") and "/" not in action.removeprefix("simulation/"):
            if not handler.application.simulation_enabled or not handler.application.ngg_enabled:
                raise ValueError("Simulation and qualified geometry must be enabled")
            manager = handler.application.simulation_workspace()
            run = action.removeprefix("simulation/")
            status = manager.status(session.user.login_id, handler.application.ngg_workspace(), run)
            if status.get("state") != "completed" or status.get("freshness") != "current" or status.get("diagnostic"):
                raise ValueError("A completed, current source-bound simulation run is required")
            return handler._json(200, simulation_plots(manager.dataset(session.user.login_id, run)))
    except CosmosError as error:
        status, payload = map_systems_error(error)
        return handler._json(status, payload)
    except (ValueError, KeyError, TypeError, OSError) as error:
        return handler._json(400, {"error": {"code": "VISUALIZATION_SOURCE_UNAVAILABLE", "message": str(error)[:1024]}})
    return handler._json(404, {"error": "not_found"})
