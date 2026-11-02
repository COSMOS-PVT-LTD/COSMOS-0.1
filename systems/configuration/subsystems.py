"""Persisted subsystem analysis inputs, distinct from derived result slots."""

from __future__ import annotations

import math
from typing import Any

from core.exceptions import InvalidInputError
from systems.projects.models import PropulsionDesign

SUBSYSTEM_FIELDS = {
    "chamber": {"characteristic_length_m", "contraction_ratio"},
    "thermal": {"viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k", "wall_temperature_k",
                "throat_curvature_radius_m", "property_mode", "property_source"},
    "materials": {"material_id"},
    "structure": {"wall_thickness_m", "external_pressure_pa", "external_pressure_source", "material_temperature_k", "pressure_model"},
    "injector": {
        "oxidizer_density_kg_m3",
        "fuel_density_kg_m3",
        "oxidizer_viscosity_pa_s",
        "fuel_viscosity_pa_s",
        "oxidizer_pressure_drop_pa",
        "fuel_pressure_drop_pa",
        "oxidizer_cd",
        "fuel_cd",
        "oxidizer_hole_count",
        "fuel_hole_count",
        "property_source",
    },
    "nozzle": {
        "length_fraction",
        "start_angle_deg",
        "exit_angle_deg",
        "blend_radius_ratio",
        "point_count",
    },
    "cooling": {
        "coolant_mass_flow_kg_s",
        "inlet_temperature_k",
        "inlet_pressure_pa",
        "density_kg_m3",
        "viscosity_pa_s",
        "conductivity_w_m_k",
        "cp_j_kg_k",
        "channel_width_m",
        "channel_depth_m",
        "rib_width_m",
        "channel_count",
        "wall_thickness_m",
        "wall_conductivity_w_m_k",
        "min_temperature_k",
        "max_temperature_k",
        "max_wall_temperature_k",
        "max_vapour_pressure_pa",
        "direction",
        "property_source",
        "film_mode",
        "film_slot_x_m",
        "film_slot_height_m",
        "film_blowing_ratio",
        "film_temperature_k",
        "film_cp_j_kg_k",
        "film_delta0_m",
        "film_delta_growth_rate",
        "film_valid_length_m",
        "film_source",
    },
}
_TEXT_FIELDS = {"property_source", "direction", "film_mode", "film_source", "property_mode", "material_id", "external_pressure_source", "pressure_model"}
_INTEGER_FIELDS = {
    "oxidizer_hole_count",
    "fuel_hole_count",
    "channel_count",
    "point_count",
}


def configure_subsystems(design: PropulsionDesign, updates: dict[str, Any]) -> None:
    """Replace submitted configurations atomically; omitted stages are kept.

    Partial configurations may be saved, but solvers require every needed field.
    Empty objects deliberately clear a stage. No equations/defaults here.
    """
    if not isinstance(updates, dict) or updates.keys() - SUBSYSTEM_FIELDS.keys():
        raise InvalidInputError(
            "Subsystem inputs contain an unknown engineering stage."
        )
    clean: dict[str, dict[str, Any]] = {}
    for stage, data in updates.items():
        if not isinstance(data, dict) or data.keys() - SUBSYSTEM_FIELDS[stage]:
            raise InvalidInputError(f"Unknown or malformed {stage} input fields.")
        clean[stage] = {}
        for key, value in data.items():
            if value is None:
                continue
            if key in _TEXT_FIELDS:
                if not isinstance(value, str) or len(value) > 1000:
                    raise InvalidInputError(
                        f"{key} must be at most 1000 characters of text."
                    )
                clean[stage][key] = value.strip()
                if key == "property_mode" and value not in {"EXPLICIT", "CEA_CHAMBER_FROZEN_TRANSPORT"}:
                    raise InvalidInputError("Choose EXPLICIT or CEA_CHAMBER_FROZEN_TRANSPORT gas properties.")
                if key == "pressure_model" and value not in {"THIN_WALL", "LAME_CLOSED_ENDS"}:
                    raise InvalidInputError("Choose THIN_WALL or LAME_CLOSED_ENDS pressure stresses.")
            elif (
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
            ):
                raise InvalidInputError(f"{key} must be a finite JSON number.")
            elif key in _INTEGER_FIELDS:
                if value != int(value):
                    raise InvalidInputError(f"{key} must be an integer.")
                clean[stage][key] = int(value)
            else:
                clean[stage][key] = float(value)
    for stage, data in clean.items():
        old = design.subsystem_inputs.get(stage, {})
        if old != data:
            design.subsystem_inputs[stage] = data
            design.record_input_change(f"{stage}_inputs", old, data)
