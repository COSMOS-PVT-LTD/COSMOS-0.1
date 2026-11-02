"""Synthetic regression inputs ONLY; not a fluid database or buildable engine."""

from api.propulsion_workflow import (
    create_design,
    run_phase3,
    run_phase4,
    update_requirements,
)


def injector_inputs():
    return {
        "oxidizer_density_kg_m3": 1000.0,
        "fuel_density_kg_m3": 800.0,
        "oxidizer_viscosity_pa_s": 0.001,
        "fuel_viscosity_pa_s": 0.002,
        "oxidizer_pressure_drop_pa": 1e6,
        "fuel_pressure_drop_pa": 1e6,
        "oxidizer_cd": 0.7,
        "fuel_cd": 0.7,
        "oxidizer_hole_count": 60,
        "fuel_hole_count": 60,
        "property_source": "Synthetic constant-property regression fixture; NOT physical validation.",
    }


def nozzle_inputs(count=81):
    return {
        "length_fraction": 0.8,
        "start_angle_deg": 30.0,
        "exit_angle_deg": 8.0,
        "blend_radius_ratio": 0.382,
        "point_count": count,
    }


def cooling_inputs():
    return {
        "coolant_mass_flow_kg_s": 1.0,
        "inlet_temperature_k": 300.0,
        "inlet_pressure_pa": 8e6,
        "density_kg_m3": 800.0,
        "viscosity_pa_s": 0.0005,
        "conductivity_w_m_k": 0.6,
        "cp_j_kg_k": 2500.0,
        "channel_width_m": 0.001,
        "channel_depth_m": 0.001,
        "rib_width_m": 0.0005,
        "channel_count": 60,
        "wall_thickness_m": 0.0005,
        "wall_conductivity_w_m_k": 300.0,
        "min_temperature_k": 200.0,
        "max_temperature_k": 1500.0,
        "max_wall_temperature_k": 2000.0,
        "max_vapour_pressure_pa": 1e5,
        "direction": "exit_to_throat",
        "film_mode": "none",
        "property_source": "Synthetic constant-property regression fixture; NOT physical validation.",
    }


def film_inputs():
    return {
        "film_mode": "gaseous_slot",
        "film_slot_x_m": 0.04,
        "film_slot_height_m": 0.0005,
        "film_blowing_ratio": 0.1,
        "film_temperature_k": 300.0,
        "film_cp_j_kg_k": 5000.0,
        "film_delta0_m": 0.0005,
        "film_delta_growth_rate": 0.01,
        "film_valid_length_m": 1.0,
        "film_source": "Synthetic boundary-layer regression inputs, NOT calibrated rocket data.",
    }


def seeded_design():
    design = create_design(name="Synthetic subsystem regression only")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 5e6,
            "ambient_pressure": 0,
            "mixture_ratio": 2.3,
            "expansion_ratio": 8,
            "propellant_selection": "LOX/RP-1",
        },
    )
    assert run_phase3(
        design,
        chamber_temperature_k=3000,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.001,
        expansion_ratio=8,
    )["execution_ok"]
    assert run_phase4(
        design,
        characteristic_length_m=1,
        contraction_ratio=2.5,
        wall_thickness_m=0.001,
        material_id="stainless_304",
        external_pressure_pa=0,
        material_temperature_k=300,
        viscosity_pa_s=8e-5,
        conductivity_w_m_k=0.3,
        cp_j_kg_k=2500,
        wall_temperature_k=800,
    )["execution_ok"]
    return design
