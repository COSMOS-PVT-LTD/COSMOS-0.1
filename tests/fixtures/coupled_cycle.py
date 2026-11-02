"""Real software stages plus explicit synthetic design-point assumptions only."""

from api.propulsion_workflow import run_phase3, run_phase4, run_subsystems, update_cycle
from systems.cycle.coupled import INPUT_SCHEMA
from tests.fixtures.propulsion_subsystems import (
    cooling_inputs,
    film_inputs,
    injector_inputs,
    nozzle_inputs,
    seeded_design,
)


def value(number, unit):
    return {"value": number, "unit": unit}


def design(cycle="GAS_GENERATOR", *, cooling=False, film=False):
    result = seeded_design()
    update_cycle(result, cycle)
    assert run_phase3(
        result,
        chamber_temperature_k=3000,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.001,
        expansion_ratio=8,
    )["execution_ok"]
    inputs = {"injector": injector_inputs()}
    stages = ("injector",)
    if cooling or film:
        assert run_phase4(
            result,
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
        core = result.operating_point.mass_flow.to_si() / (
            1 + result.operating_point.mixture_ratio
        )
        cfg = cooling_inputs() | {"coolant_mass_flow_kg_s": core}
        if film:
            cfg |= film_inputs()
        inputs |= {"nozzle": nozzle_inputs(), "cooling": cfg}
        stages = ("injector", "nozzle", "cooling")
    outcome = run_subsystems(result, inputs=inputs, stages=stages)
    assert outcome["execution_ok"], outcome
    return result


def specification(baseline, *, cooling=False, film=False):
    cycle = baseline.cycle_configuration.cycle_type.value
    streams = {}
    for name in ("oxidizer", "fuel"):
        pout = 8e6 if cooling and name == "fuel" else 6e6
        manifold = baseline.workflow.results["injector"].outputs[name][
            "manifold_pressure_pa"
        ]
        dp = (
            baseline.workflow.results["cooling"].outputs["total_pressure_loss_pa"]
            if cooling and name == "fuel"
            else 0
        )
        streams[name] = {
            "phase": "LIQUID",
            "density": value(1000 if name == "oxidizer" else 800, "kg/m3"),
            "inlet_pressure": value(1e6 if cycle == "GAS_GENERATOR" else pout, "Pa"),
            "outlet_pressure": value(pout, "Pa"),
            "efficiency": 0.5 if cycle == "GAS_GENERATOR" else None,
            "core_loss": value(0, "Pa"),
            "core_control_drop": value(pout - manifold - dp, "Pa"),
            "gg_loss": value(0, "Pa"),
            "gg_control_drop": value(
                pout - 4e5 if cycle == "GAS_GENERATOR" else 0, "Pa"
            ),
            "external_flow": value(0, "kg/s"),
            "external_sink_pressure": value(1e5, "Pa"),
            "external_loss": value(0, "Pa"),
            "external_control_drop": value(0, "Pa"),
            "source": "Synthetic software reference: explicit constant liquid properties/design-point total-head-equivalent branch losses; not measured hardware/map data",
        }
    gg = (
        {
            "temperature": value(1000, "K"),
            "inlet_pressure": value(4e5, "Pa"),
            "outlet_pressure": value(1e5, "Pa"),
            "cp": value(1000, "J/kg/K"),
            "inlet_specific_enthalpy": value(0, "J/kg"),
            "net_released_energy": value(1e6, "J/kg"),
            "heat_loss": value(0, "W"),
            "auxiliary_power": value(0, "W"),
            "maximum_flow": value(100, "kg/s"),
            "mixture_ratio": 1,
            "gamma": 2,
            "turbine_efficiency": 0.8,
            "shaft_efficiency": 0.9,
            "source": "Synthetic calorically perfect gas/efficiencies, consistent common-reference enthalpy and net reaction heat; not a GG combustion prediction",
        }
        if cycle == "GAS_GENERATOR"
        else None
    )
    boundary = (
        {
            "boundary": "EXTERNALLY_CONDITIONED_FUEL",
            "sink_pressure": value(1e5, "Pa"),
            "loss": value(0, "Pa"),
            "control_drop": value(
                streams["fuel"]["outlet_pressure"]["value"] - 1e5, "Pa"
            ),
            "source": "Synthetic external film conditioner boundary; phase-change energy and gas feed system not solved",
        }
        if film
        else None
    )
    return {
        "schema": INPUT_SCHEMA,
        "cycle_type": cycle,
        "regime": "STEADY_DESIGN_POINT",
        "cooling_mode": "FUEL_CORE_SERIES" if cooling else "NONE_EXPLICIT",
        "film": boundary,
        "streams": streams,
        "gas_generator": gg,
        "pressure_tolerance": value(1e-6, "Pa"),
        "mass_flow_tolerance": value(1e-10, "kg/s"),
        "power_tolerance": value(1e-5, "W"),
    }
