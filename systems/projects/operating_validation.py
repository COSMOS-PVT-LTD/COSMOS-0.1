"""Retained solved-candidate predictions/context for predeclared evidence plans."""

from __future__ import annotations

import json
from typing import Any

from core.exceptions import CosmosError
from systems.cycle.operating_sensitivity import at_path
from systems.projects.authority import InvalidRecord, SavedSnapshot
from systems.projects.models import PropulsionDesign
from validation import propulsion as vv

TARGETS = {
    "thrust": ("core.thrust_n", "N"),
    "core_mass_flow": ("core.mass_flow_kg_s", "kg/s"),
    "solved_chamber_pressure": ("unknowns.chamber_pressure.value", "Pa"),
    "solved_core_mixture_ratio": ("core.mixture_ratio", "1"),
    "solved_shaft_speed": ("unknowns.shaft_speed.value", "rad/s"),
    "coolant_outlet_temperature": ("cooling.outlet_temperature_k", "K"),
    "coolant_pressure_loss": ("cooling.total_pressure_loss_pa", "Pa"),
    "coolant_heat_pickup": ("cooling.total_heat_w", "W"),
}


def candidate(source: SavedSnapshot, targets: list[str]) -> dict[str, Any]:
    if type(targets) is not list or not 1 <= len(targets) <= 8 or len(set(targets)) != len(targets) or any(name not in TARGETS for name in targets):
        raise InvalidRecord("Select unique supported solved-candidate prediction targets; no frozen-core or imposed-state fallback.")
    record = json.loads(source.payload)
    result = record["evaluation"]["result"] if record["status"] == "COMPLETED" else None
    if not result or not result["outputs"]["solved_candidate_usable"]:
        raise InvalidRecord("Validation planning requires an actual usable solved operating candidate, not a failed trial.")
    solved = result["outputs"]["candidate"]
    recipe = record["command"]["specification"]
    design = PropulsionDesign.from_canonical_dict(json.loads(record["baseline_canonical_json"]))
    if design.operating_point.ambient_pressure is None:
        raise InvalidRecord("Exact solved-candidate ambient boundary is missing.")
    conditions: dict[str, Any] = {}
    properties: dict[str, Any] = {}

    def row(destination, name, value, unit, origin):
        destination[name] = {"value": value if type(value) is str else vv.number(value, name), "unit": unit, "source": origin}

    row(conditions, "cycle_type", recipe["cycle_type"], "1", source.commit_id)
    row(conditions, "ambient_pressure", design.operating_point.ambient_pressure.to_si(), "Pa", "exact saved operating-point baseline")
    for name in ("oxidizer", "fuel"):
        row(conditions, name + "_id", getattr(design.propellant_configuration, name + "_id"), "1", "exact saved propellants")
        feed = recipe["feeds"][name]
        for key in ("temperature", "tank_pressure"):
            row(conditions, name + "_" + key, feed[key]["value"], feed[key]["unit"], feed["source"])
        for key in ("density", "cp", "viscosity", "conductivity", "reference_temperature", "reference_pressure", "vapour_pressure", "core_resistance"):
            row(properties, name + "_" + key, feed[key]["value"], feed[key]["unit"], feed["source"])
        if feed["pump"] is not None:
            for key in ("speed_coefficient", "flow_coefficient"):
                value = feed["pump"][key]
                row(properties, name + "_pump_" + key, value["value"], value["unit"], feed["pump"]["source"])
            row(properties, name + "_pump_efficiency", feed["pump"]["efficiency"], "1", feed["pump"]["source"])
            row(properties, name + "_gg_resistance", feed["gg_resistance"]["value"], feed["gg_resistance"]["unit"], feed["source"])
    contour = design.workflow.current_result("nozzle")
    if contour is None:
        raise InvalidRecord("Exact solved-candidate contour source is missing.")
    for key, unit in (("throat_area_m2", "m2"), ("expansion_ratio", "1"), ("length_m", "m")):
        row(conditions, key, contour.outputs[key], unit, contour.result_id)
    row(conditions, "cooling_mode", recipe["cooling"]["mode"], "1", recipe["cooling"]["source"])
    if solved["cooling"] is not None:
        cfg = design.subsystem_inputs["cooling"]
        for key, unit in (("wall_thickness_m", "m"), ("channel_width_m", "m"), ("channel_depth_m", "m"), ("rib_width_m", "m"), ("channel_count", "1"), ("wall_conductivity_w_m_k", "W/m/K")):
            row(properties, key, cfg[key], unit, "exact retained channel/wall input; material/temperature applicability still needs qualified review")
    if recipe["gas_generator"] is not None:
        gg = recipe["gas_generator"]
        for key in ("throat_area", "exhaust_pressure", "auxiliary_power"):
            row(conditions, "gg_" + key, gg[key]["value"], gg[key]["unit"], gg["source"])
        for key in ("shaft_efficiency", "turbine_efficiency"):
            row(properties, "gg_" + key, gg[key], "1", gg["source"])
    predictions = {}
    for name in targets:
        path, unit = TARGETS[name]
        try:
            value = at_path(solved, path)
        except CosmosError as error:
            raise InvalidRecord("Prediction unavailable in selected candidate: " + name) from error
        predictions[name] = {"value": vv.number(value, name), "unit": unit, "stage": "engine-operating-point", "source_result_id": result["result_id"], "model_id": result["model_id"], "validity": result["validity"]}
    return {"baseline_commit_id": source.commit_id, "baseline_sha256": source.head.content_hash, "baseline_canonical_json": source.payload.decode(), "predictions": predictions, "conditions": conditions, "properties": properties, "source_results": {"operating_candidate": result}, "scope": "Selected solved PF/GG operating/thermal model only. Predeclared reported-output comparison, not full uncertainty propagation, source authentication, hardware applicability or independent physical acceptance."}
