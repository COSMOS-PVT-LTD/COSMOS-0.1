"""Coupled actual subsystem lineage, balance and refusal verification."""

import json
from copy import deepcopy
from hashlib import sha256

import pytest

from api.cycle_assessment import evaluate
from core.exceptions import InvalidInputError
from physics.exceptions import InsufficientDataError, OutOfRangeError
from systems.contracts.results import ResultStatus
from tests.fixtures.coupled_cycle import design, specification
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("cycle", ["GAS_GENERATOR", "PRESSURE_FED"])
@pytest.mark.parametrize("cooling,film", [(False, False), (True, False), (True, True)])
def test_actual_stage_coupling_exact_source_and_no_mutation(cycle, cooling, film):
    base = design(cycle, cooling=cooling, film=film)
    spec = specification(base, cooling=cooling, film=film)
    original, request = base.to_canonical_json(), deepcopy(spec)
    result = evaluate(base, spec)["result"]
    out = result["outputs"]
    assert out["assessment_status"] == "BALANCED_DECLARED_DESIGN_POINT", out[
        "residuals"
    ]
    assert base.to_canonical_json() == original and spec == request
    assert result["inputs"]["baseline_canonical_text"] == original
    assert result["inputs"]["baseline_sha256"] == sha256(original.encode()).hexdigest()
    for stage, source in result["inputs"]["source_results"].items():
        assert source == json.loads(original)["workflow"]["results"][stage]
    assert not out["workflow_cycle_complete"] and result["stage_id"] is None
    assert result["validation"]["status"] == "NOT_PERFORMED"
    if cycle == "GAS_GENERATOR":
        assert out["power"]["gg_mass_flow_kg_s"] > 0
        assert out["total_withdrawal_kg_s"] > out["core_mass_flow_kg_s"]
        assert (
            out["core_only_thrust_effective_isp_s"]
            < base.workflow.results["performance"].outputs["specific_impulse"]["value"]
        )
    else:
        assert out["power"] is None
    if cooling:
        assert (
            out["cooling"]["heat_pickup_w"]
            == json.loads(original)["workflow"]["results"]["cooling"]["outputs"][
                "total_heat_w"
            ]
        )
        assert out["streams"]["fuel"]["core_flow_kg_s"] == pytest.approx(
            out["cooling"]["flow_kg_s"]
        )
    if film:
        assert (
            out["streams"]["fuel"]["film_flow_kg_s"]
            == base.workflow.results["cooling"].outputs["film_mass_flow_estimate_kg_s"]
        )


@pytest.mark.parametrize(
    "change", ["energy", "core_pressure", "GG_pressure", "coolant_flow"]
)
def test_independent_residual_failure_does_not_become_qualified_success(change):
    base = design(cooling=True)
    spec = specification(base, cooling=True)
    if change == "energy":
        spec["gas_generator"]["net_released_energy"]["value"] += 100
    elif change == "core_pressure":
        spec["streams"]["fuel"]["core_control_drop"]["value"] += 100
    elif change == "GG_pressure":
        spec["streams"]["fuel"]["gg_control_drop"]["value"] += 100
    else:
        base.workflow.results["cooling"].inputs["coolant_mass_flow_kg_s"] += 0.1
    out = evaluate(base, spec)["result"]["outputs"]
    assert out["assessment_status"] == "UNBALANCED"
    assert not out["assessment_balances_closed_within_declared_tolerances"]
    assert any(not row["passed"] for row in out["residuals"])


@pytest.mark.parametrize(
    "stage", ["performance", "injector", "cooling", "nozzle", "thermal"]
)
def test_stale_results_refused(stage):
    base = design(cooling=True)
    spec = specification(base, cooling=True)
    base.workflow.results[stage].status = ResultStatus.STALE
    with pytest.raises(InsufficientDataError):
        evaluate(base, spec)


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf"), -1, "1000"])
def test_strict_quantities_refuse(bad):
    base = design()
    spec = specification(base)
    spec["streams"]["fuel"]["density"]["value"] = bad
    with pytest.raises(InvalidInputError):
        evaluate(base, spec)


def test_wrong_units_cycle_context_and_silent_film_discard_refused():
    base = design()
    spec = specification(base)
    spec["pressure_tolerance"]["unit"] = "kPa"
    with pytest.raises(InvalidInputError):
        evaluate(base, spec)
    spec = specification(base)
    spec["cycle_type"] = "EXPANDER"
    with pytest.raises(OutOfRangeError):
        evaluate(base, spec)
    base = design(cooling=True, film=True)
    spec = specification(base, cooling=True)
    with pytest.raises(InvalidInputError, match="film"):
        evaluate(base, spec)


def test_lineage_and_density_mismatch_refused():
    base = design()
    spec = specification(base)
    base.workflow.results["injector"].inputs["performance_result_id"] = "different"
    with pytest.raises(InvalidInputError, match="Injector"):
        evaluate(base, spec)
    base = design()
    spec = specification(base)
    spec["streams"]["fuel"]["density"]["value"] += 1
    with pytest.raises(InvalidInputError, match="density"):
        evaluate(base, spec)


def test_other_withdrawals_are_counted_and_each_pressure_path_is_checked():
    base = design()
    spec = specification(base)
    spec["streams"]["fuel"]["external_flow"]["value"] = 0.2
    spec["streams"]["fuel"]["external_control_drop"]["value"] = 5.9e6
    out = evaluate(base, spec)["result"]["outputs"]
    assert out["assessment_status"] == "BALANCED_DECLARED_DESIGN_POINT"
    row = out["streams"]["fuel"]
    assert row["withdrawal_kg_s"] == pytest.approx(
        row["core_flow_kg_s"] + row["gg_flow_kg_s"] + 0.2
    )
    spec["streams"]["fuel"]["external_control_drop"]["value"] -= 100
    out = evaluate(base, spec)["result"]["outputs"]
    assert not next(
        r for r in out["residuals"] if r["name"] == "fuel.external_pressure"
    )["passed"]


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_real_cea_core_adapter_preserves_native_mass_flow_and_provenance(cycle):
    pytest.importorskip("cea")
    from api.propulsion_workflow import run_phase3, run_subsystems, update_cycle
    from tests.fixtures.propulsion_subsystems import injector_inputs
    from tests.unit_tests.api.test_cea_workflow import CONFIG, cea_design

    base = cea_design()
    update_cycle(base, cycle)
    assert run_phase3(base, thermochemistry_configuration=CONFIG, throat_area_m2=0.001)[
        "execution_ok"
    ]
    assert run_subsystems(
        base, inputs={"injector": injector_inputs()}, stages=("injector",)
    )["execution_ok"]
    spec = specification(base)
    original = base.to_canonical_json()
    out = evaluate(base, spec)["result"]["outputs"]
    assert out["assessment_status"] == "BALANCED_DECLARED_DESIGN_POINT"
    assert out["core_performance_adapter"] == "performance.cea_ideal_nozzle"
    assert (
        out["core_mass_flow_kg_s"]
        == json.loads(original)["workflow"]["results"]["performance"]["outputs"][
            "mass_flow"
        ]["magnitude"]
    )
    assert base.to_canonical_json() == original
