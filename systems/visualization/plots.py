"""Project verified finite source rows into declared-unit scientific plot DTOs."""
from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from typing import Any

from systems.contracts.results import ResultStatus
from systems.projects.models import PropulsionDesign


def _canonical_source(value: dict[str, Any]) -> str:
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":"))


def _digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_source(value).encode()).hexdigest()


def _plot(identifier: str, title: str, rows: list[dict[str, Any]], x: tuple[str, str, str],
          ys: list[tuple[str, str]], unit: str, source: dict[str, Any], notes: list[str]) -> dict[str, Any]:
    if not 2 <= len(rows) <= 10_000:
        raise ValueError("Plot source must contain 2 to 10000 samples")
    for row in rows:
        for key in (x[0], *(key for key, _ in ys)):
            if type(row.get(key)) not in {int, float} or not math.isfinite(row[key]):
                raise ValueError(f"Non-finite or missing source field: {key}")
    ordered = sorted(rows, key=lambda row: row[x[0]])
    return {"id": identifier, "title": title, "x": {"label": x[1], "unit": x[2]},
        "y": {"label": title, "unit": unit}, "series": [
            {"name": name, "role": "reference" if key == "reference_k" else "computed",
             "points": [[row[x[0]], row[key]] for row in ordered]} for key, name in ys],
        "rows": deepcopy(rows), "source": deepcopy(source), "notes": notes,
        "uncertainty": "not quantified", "sample_count": len(rows), "clipping": "none"}


def design_plots(design: PropulsionDesign) -> dict[str, Any]:
    plots: list[dict[str, Any]] = []
    unavailable: list[dict[str, str]] = []
    definitions = (
        ("nozzle", "stations", [
            ("contour", "Nozzle contour radius", [("radius_m", "Radius")], "m"),
            ("mach", "Mach number", [("mach", "Mach")], "1"),
            ("pressure", "Static pressure", [("pressure_pa", "Pressure")], "Pa"),
            ("temperature", "Static temperature", [("temperature_k", "Temperature")], "K")]),
        ("cooling", "segments", [
            ("wall", "Wall and coolant temperature", [("hot_wall_temperature_k", "Hot wall"),
                ("cold_wall_temperature_k", "Cold wall"), ("coolant_out_temperature_k", "Coolant outlet")], "K"),
            ("heat-flux", "Wall heat flux", [("heat_flux_w_m2", "Heat flux")], "W/m²"),
            ("coolant-pressure", "Coolant outlet pressure", [("coolant_out_pressure_pa", "Coolant pressure")], "Pa"),
            ("film", "Film effectiveness", [("film_effectiveness", "Film effectiveness")], "1")]),
    )
    for stage, field, charts in definitions:
        result = design.workflow.results.get(stage)
        if result is None or result.status is not ResultStatus.CURRENT:
            unavailable.append({"stage": stage, "status": result.status.value if result else "NOT_CALCULATED",
                "reason": "Run this stage for the current design; stale/failed results are not plotted as current."})
            continue
        dto = result.to_canonical_dict()
        source = {"domain": "propulsion", "design_id": design.design_id, "revision": design.revision,
            "result_id": result.result_id, "content_sha256": _digest(dto), "status": result.status.value,
            "model_id": result.model_id, "freshness": "current", "verification": dto["verification"], "validation": dto["validation"],
            "validity": dto["validity"], "assumptions": list(result.assumptions), "warnings": list(result.warnings),
            "source_record": dto, "source_canonical_json": _canonical_source(dto)}
        rows = result.outputs.get(field)
        if not isinstance(rows, list):
            unavailable.append({"stage": stage, "status": "MISSING_DATA", "reason": "No supported source rows available."})
            continue
        for identifier, title, ys, unit in charts:
            try:
                plots.append(_plot(f"{stage}-{identifier}", title, rows, ("x_m", "Axial position", "m"), ys, unit, source,
                    ["Source rows are unchanged; plotting order is increasing axial position.",
                     "Preliminary model output, not experimental measurements or hardware acceptance."]))
            except (ValueError, KeyError, TypeError) as error:
                unavailable.append({"stage": stage, "status": "INVALID_DATA", "reason": str(error)})
    return {"schema_version": "cosmos-plots-v1", "design_id": design.design_id, "revision": design.revision,
        "plots": plots, "unavailable": unavailable, "production_handoff": False}


def simulation_plots(dataset: dict[str, Any]) -> dict[str, Any]:
    """Adapt the existing P09 radial dataset; never invent a 3D field or CFL."""
    if dataset.get("schema_version") != "p09-dataset-v1":
        raise ValueError("Unsupported simulation dataset schema")
    if dataset.get("execution_status") != "completed" or dataset.get("study", {}).get("model") != "steady-spherical-conduction-v1":
        raise ValueError("A completed declared spherical benchmark source is required")
    source = {"domain": "simulation", "run_id": dataset["run_id"], "study_id": dataset["study_id"],
        "content_sha256": _digest(dataset), "status": dataset["execution_status"], "freshness": "current",
        "model_id": dataset["study"]["model"],
        "verification": dataset["solution_verification"], "validation": dataset["experimental_validation"],
        "convergence": dataset["numerical_convergence"], "conservation": dataset["conservation_checks"],
        "source_refs": dataset["source_refs"], "assumptions": [],
        "warnings": [json.dumps(item, sort_keys=True) for item in dataset["diagnostics"]],
        "source_record": deepcopy(dataset), "source_canonical_json": _canonical_source(dataset)}
    def rows(keys: tuple[str, ...]) -> list[dict[str, Any]]:
        values = [dataset[key] for key in keys]
        if any(not isinstance(value, list) for value in values) or len({len(value) for value in values}) != 1:
            raise ValueError("Simulation source column lengths do not match")
        return [dict(zip(keys, row)) for row in zip(*values)]
    plots = [_plot("radial-temperature", "Radial temperature", rows(("radii_m", "temperature_k", "reference_k")),
        ("radii_m", "Radius", "m"), [("temperature_k", "Computed"), ("reference_k", "Analytic reference")], "K", source,
        ["One-dimensional radial profile; not an arbitrary 3D field."])]
    history = rows(("iterations", "normalized_residuals", "power_imbalance_w"))
    if len(history) >= 2:
        plots += [_plot("residual-history", "Normalized residual", history, ("iterations", "Iteration", "1"),
            [("normalized_residuals", "Residual")], "1", source, [dataset["residual_definition"]]),
            _plot("power-balance", "Signed power imbalance", history, ("iterations", "Iteration", "1"),
            [("power_imbalance_w", "Outward minus generated power")], "W", source,
            ["Signed values; use a linear axis."])]
    return {"schema_version": "cosmos-plots-v1", "plots": plots, "unavailable": [], "production_handoff": False}
