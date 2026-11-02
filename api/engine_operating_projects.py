"""Authenticated bounded solver, retained exact sources and iteration plots."""

from __future__ import annotations

from importlib.util import find_spec
from typing import Any

from api.cycle_projects import CycleAssessmentAPI
from api.cycle_projects import plots as balance_plots
from api.geometry_projects import BinarySource
from api.pressure_fed_projects import PressureFedAPI
from systems.cycle.operating_contract import (
    CORE_UNKNOWNS,
    FEED_UNITS,
    GG_UNKNOWNS,
    PUMP_UNITS,
    SCHEMA,
    TOLERANCE_UNITS,
)
from systems.visualization.plots import _plot


class OperatingSource(BinarySource):
    """Preliminary calculated model source, not a fixture or accepted experiment."""


class EngineOperatingAPI(CycleAssessmentAPI):
    filename_prefix = "engine-operating"

    def handle(self, actor: Any, method: str, project: str, parts: list[str], query: dict[str, list[str]], body: dict[str, Any]) -> Any:
        if parts == ["capabilities"] and method == "GET" and not query:
            return {"ok": True, "schema": SCHEMA, "runtime_installed": find_spec("cea") is not None, "cycles": ["PRESSURE_FED", "GAS_GENERATOR"], "feed_units": FEED_UNITS, "pump_units": PUMP_UNITS, "unknown_units": {**CORE_UNKNOWNS, **GG_UNKNOWNS}, "tolerance_units": TOLERANCE_UNITS, "scope": "Solved steady PF/GG network; NASA HP feedback with counterflow fuel and nonadiabatic divergent frozen-gas nozzle. Regulated tank boundaries; no film injection, shock, two-phase, startup or physical acceptance. Explicit sourced characteristic fits/windows and SI specification required; no engineering defaults.", "execution": "Input capture before bounded synchronous solve outside SQL. No cancellation/background-job claim.60s solver budget; initial/refinalization calls are separately bounded by thermal iteration count."}
        if len(parts) == 2 and parts[1] == "plots" and method == "GET":
            value = PressureFedAPI.handle(self, actor, method, project, parts[:1], query, body)
            if not isinstance(value, dict):
                raise TypeError("Expected exact operating envelope, not binary source.")
            return plots(value)
        result = PressureFedAPI.handle(self, actor, method, project, parts, query, body)
        return OperatingSource(result.name, result.data, result.content_hash) if isinstance(result, BinarySource) else result


def plots(value: dict[str, Any]) -> dict[str, Any]:
    record = value["record"]
    if not value["upstream_current"] or record["status"] != "COMPLETED":
        return {"plots": [], "unavailable": ["Historical/method-stale or failed execution: inspect original diagnostics."]}
    result = record["evaluation"]["result"]
    output = result["outputs"]
    data = []
    if len(output["residuals"]) >= 2:
        data = balance_plots(value)["plots"]
    source = {
        "domain": "engine-operating-point", "project_id": value["authority"]["project_id"], "commit_id": value["authority"]["commit_id"],
        "baseline_commit_id": record["baseline_commit_id"], "content_sha256": value["authority"]["head"]["content_hash"], "model_id": result["model_id"],
        "method_sources": record["method_sources"], "status": record["status"], "freshness": "current", "verification": result["verification"]["status"],
        "validation": "NOT_PERFORMED", "assumptions": result["assumptions"], "warnings": result["warnings"], "source_canonical_json": value["source_canonical_json"],
    }
    for plot in data:
        plot["source"] = source
    history = output["solver"]["history"]
    if len(history) >= 2:
        data.append(_plot("operating-nonlinear-history", "Operating-point normalized residual history", history, ("iteration", "Accepted Newton iteration", "1"), [("infinity_norm", "Infinity norm of dimensional residual / declared tolerance")], "1", source, ["Linear axes; each normalized equation is divided by its declared physical tolerance. Solver threshold: " + str(record["command"]["specification"]["solver"]["residual_tolerance"]), "Iteration convergence does not imply conservation, physical validation or release acceptance."]))
    candidate = output["candidate"]
    if candidate and len(candidate["thermal_history"]) >= 2:
        data.append(_plot("operating-thermal-history", "Thermal fixed-point heat mismatch", candidate["thermal_history"], ("iteration", "Thermal iteration", "1"), [("heat_l1_residual_w", "Sum of absolute cell heat mismatches")], "W", source, ["Gas extraction versus freshly recomputed coolant heat; independent whole-loop energy and HP checks also required."]))
    return {"plots": data, "unavailable": [] if data else ["Fewer than two retained history samples; no invented curve."]}
