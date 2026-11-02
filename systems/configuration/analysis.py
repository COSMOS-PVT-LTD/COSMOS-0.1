"""Persist explicit analysis inputs separately from replaceable solver outputs."""

from systems.configuration.subsystems import configure_subsystems

PHASE4_FIELDS = {
    "chamber": ("characteristic_length_m", "contraction_ratio"),
    "thermal": ("viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k", "wall_temperature_k", "throat_curvature_radius_m"),
    "materials": ("material_id",),
    "structure": ("wall_thickness_m", "external_pressure_pa", "external_pressure_source", "material_temperature_k", "pressure_model"),
}


def configure_analysis_inputs(design, overrides):
    updates = {}
    for stage, keys in PHASE4_FIELDS.items():
        supplied = {key: overrides[key] for key in keys if overrides.get(key) is not None}
        if supplied:
            updates[stage] = {**design.subsystem_inputs.get(stage, {}), **supplied}
    if overrides.get("gas_property_mode") is not None:
        thermal = updates.setdefault("thermal", dict(design.subsystem_inputs.get("thermal", {})))
        thermal["property_mode"] = overrides["gas_property_mode"]
        if overrides["gas_property_mode"] == "CEA_CHAMBER_FROZEN_TRANSPORT":
            # Clear only the old *input selection*; do not silently mix sources.
            for key in ("viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k"):
                if overrides.get(key) is None:
                    thermal.pop(key, None)
    if updates:
        configure_subsystems(design, updates)
