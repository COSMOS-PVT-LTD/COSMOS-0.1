"""Selected-cycle operating-point/thermal software verification, not physical validation."""

from copy import deepcopy
from itertools import pairwise

import pytest

pytest.importorskip("cea", reason="Explicit pinned NASA CEA runtime required for coupled operating qualification; no fallback")

from core.exceptions import InvalidInputError
from physics.exceptions import OutOfRangeError
from plugins.nasa_cea.chamber import NasaHPChamber
from systems.cycle.engine_operating import assess
from systems.cycle.operating_contract import quantity as q
from systems.cycle.operating_contract import validate
from tests.fixtures.engine_operating import design, specification, v
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_manufactured_operating_point_all_unknowns_independently_fixed(cycle):
    baseline = design(cycle)
    original = baseline.to_canonical_json()
    spec, expected = specification(baseline)
    result = assess(baseline, spec)
    assert baseline.to_canonical_json() == original
    output = result.outputs
    assert output["solved_candidate_usable"] and output["numerical_convergence"]
    assert output["termination_reason"] == "RESIDUAL_CONVERGED"
    assert not output["workflow_cycle_complete"] and output["physical_validation"] == "NOT_PERFORMED"
    candidate = output["candidate"]
    for key, target in expected.items():
        assert candidate["unknowns"][key]["value"] == pytest.approx(target, rel=3e-6)
    assert all(row["passed"] for row in candidate["residuals"])
    for name in ("oxidizer", "fuel"):
        stream = candidate["streams"][name]
        assert stream["pump_flow_kg_s"] == stream["core_flow_kg_s"] + stream["gg_flow_kg_s"]
    assert len(output["solver"]["history"]) >= 2


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_bidirectional_heat_recomputes_combustion_nozzle_feed_and_power(cycle):
    baseline = design(cycle)
    spec, _ = specification(baseline)
    adiabatic = assess(baseline, spec).outputs["candidate"]
    spec["cooling"]["mode"] = "FUEL_CORE_SERIES"
    out = assess(baseline, spec).outputs
    assert out["solved_candidate_usable"]
    hot = out["candidate"]
    assert hot["cooling"]["total_heat_w"] > 0
    assert hot["core"]["gas"]["temperature_k"] != adiabatic["core"]["gas"]["temperature_k"]
    assert hot["unknowns"]["fuel_flow"]["value"] != adiabatic["unknowns"]["fuel_flow"]["value"]
    assert hot["core"]["nozzle"]["stations"][-1]["total_enthalpy_j_kg"] < hot["core"]["gas"]["cp_j_kg_k"] * hot["core"]["gas"]["temperature_k"]
    residuals = {r["name"]: r for r in hot["residuals"]}
    for name in ("core_net_energy_including_regeneration", "heat_exchange_coupling", "coolant_energy", "nozzle_energy", "nozzle_momentum_max"):
        assert residuals[name]["passed"]
    assert hot["thermal_history"][-1]["heat_l1_residual_w"] <= spec["cooling"]["heat_tolerance"]["value"]
    if cycle == "GAS_GENERATOR":
        assert hot["unknowns"]["shaft_speed"]["value"] != adiabatic["unknowns"]["shaft_speed"]["value"]
        assert residuals["shaft_power"]["passed"]


def test_cea_hp_reference_enthalpy_and_augmentation_are_real_not_temperature_alias():
    chamber = NasaHPChamber("methane", "oxygen", 111.66, 90.17)
    state = chamber.solve(q(5e6,"Pa"),3.,q(0,"J/kg"))
    heated = chamber.solve(q(5e6,"Pa"),3.,q(1e5,"J/kg"))
    # Independently recorded native HP quick-start-style state and enthalpy.
    assert state.temperature_k == pytest.approx(3431.4648573817603, rel=1e-8)
    assert state.product_enthalpy_j_kg == pytest.approx(-1694782.0058653945, abs=.5)
    assert heated.temperature_k > state.temperature_k
    assert heated.product_enthalpy_j_kg - state.product_enthalpy_j_kg == pytest.approx(1e5, abs=1.)
    assert abs(state.enthalpy_residual_j_kg) < 1
    assert state.cp_j_kg_k > state.gas_constant_j_kg_k
    assert len(state.provenance["database_sha256"]["thermo.lib"]) == 64
    with pytest.raises(OutOfRangeError):
        NasaHPChamber("methane", "oxygen", 300., 90.17)


def test_unknown_criteria_units_boolean_and_extra_flags_refused():
    baseline = design()
    good, _ = specification(baseline)
    for bad in (
        {**good, "physical_validation": "PASSED"},
        {**good, "cycle_type": "EXPANDER"},
        {**good, "solver": {**good["solver"], "max_iterations": True}},
    ):
        with pytest.raises(InvalidInputError):
            validate(bad)
    bad = deepcopy(good)
    bad["feeds"]["fuel"]["cp"]["unit"] = "kJ/kg/K"
    with pytest.raises(InvalidInputError):
        validate(bad)


def test_exhausted_budget_no_candidate_even_with_last_finite_iterate():
    baseline = design()
    spec, _ = specification(baseline)
    spec["solver"]["max_iterations"] = 1
    out = assess(baseline, spec).outputs
    assert not out["numerical_convergence"] and out["termination_reason"] == "MAX_ITERATIONS"
    assert out["candidate"] is None and not out["solved_candidate_usable"]


def test_thermal_budget_and_phase_map_limits_fail_closed():
    baseline = design("GAS_GENERATOR")
    spec, _ = specification(baseline, cooling=True)
    spec["cooling"]["max_iterations"] = 1
    out = assess(baseline, spec).outputs
    assert not out["solved_candidate_usable"] and out["candidate"] is None
    assert "THERMAL_MAX_ITERATIONS" in out["last_rejected_trial"]
    spec, _ = specification(baseline)
    spec["feeds"]["fuel"]["pump"]["speed_min"] = v(1200,"rad/s")
    out = assess(baseline, spec).outputs
    assert not out["solved_candidate_usable"] and "no extrapolation" in out["last_rejected_trial"]


def test_independent_conservation_gate_is_not_just_newton_convergence():
    baseline = design()
    spec, _ = specification(baseline)
    spec["tolerances"]["specific_energy"] = v(1e-12,"J/kg")
    out = assess(baseline, spec).outputs
    assert out["numerical_convergence"] and not out["solved_candidate_usable"]
    assert out["candidate"] is None and out["unaccepted_diagnostics"]


def test_thermal_relaxation_and_tolerance_refinement_agree():
    baseline = design()
    spec, _ = specification(baseline,cooling=True)
    first = assess(baseline,spec).outputs["candidate"]
    spec["cooling"]["heat_tolerance"] = v(.001,"W")
    spec["cooling"]["relaxation"] = .4
    second = assess(baseline,spec).outputs["candidate"]
    assert second["unknowns"]["chamber_pressure"]["value"] == pytest.approx(first["unknowns"]["chamber_pressure"]["value"],rel=2e-7)
    assert second["cooling"]["total_heat_w"] == pytest.approx(first["cooling"]["total_heat_w"],rel=1e-6)


def test_coupled_contour_refinement_decreases_successive_changes():
    from api.propulsion_workflow import run_subsystems

    baseline = design()
    thrust, heat = [], []
    for count in (17,33,65,129):
        cfg = {**baseline.subsystem_inputs["nozzle"],"point_count":count}
        assert run_subsystems(baseline,inputs={"nozzle":cfg},stages=("nozzle",))["execution_ok"]
        spec,_ = specification(baseline,cooling=True)
        out = assess(baseline,spec).outputs
        assert out["solved_candidate_usable"]
        thrust.append(out["candidate"]["core"]["thrust_n"])
        heat.append(out["candidate"]["cooling"]["total_heat_w"])
    for sequence,limit in ((thrust,1e-3),(heat,1e-4)):
        changes = [abs(b-a) for a,b in pairwise(sequence)]
        assert changes[2] < changes[1] < changes[0]
        assert changes[-1]/abs(sequence[-1]) < limit
