"""Read-only dimensional comparison, not acceptance or engine sizing."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from api.propulsion_workflow import get_stage_result_payload
from core.quantity import Quantity
from core.unit import get_unit_registry
from systems.visualization.targets import thrust_comparison
from tests.fixtures.propulsion_subsystems import seeded_design


def fixture(target=5, calculated=4500, *, current=True):
    units = get_unit_registry()
    result = SimpleNamespace(result_id="result-A", design_revision=7,
        outputs={"thrust": Quantity(calculated, units.get("N")).to_canonical_dict()},
        to_canonical_dict=lambda: {"inputs": {"ambient_pressure": Quantity(0, units.get("Pa")).to_canonical_dict()}})
    return SimpleNamespace(design_id="A", revision=7, requirements=SimpleNamespace(target_thrust=Quantity(target, units.get("kN"))),
        workflow=SimpleNamespace(current_result=lambda _stage: result if current else None)), result


def test_signed_difference_is_core_dimensional_backend_comparison():
    design, result = fixture()
    original = deepcopy(result.outputs)
    value = thrust_comparison(design)
    assert value["status"] == "AVAILABLE"
    assert value["quantities"]["requested_thrust"]["magnitude"] == 5000
    assert value["quantities"]["signed_difference"]["magnitude"] == -500
    assert value["quantities"]["signed_difference"]["unit"]["symbol"] == "N"
    assert value["source_target"]["unit"]["symbol"] == "kN"
    assert value["tolerance_assessment"] == "NOT_DECLARED" and not value["input_changes"]
    assert value["operating_conditions"]["ambient_pressure"]["magnitude"] == 0
    assert result.outputs == original and design.revision == 7


def test_zero_target_and_achieved_remain_exact_zero_without_relative_division():
    design, _result = fixture(0, 0)
    value = thrust_comparison(design)
    assert value["status"] == "AVAILABLE"
    assert all(q["magnitude"] == 0 for q in value["quantities"].values())
    assert "relative_error" not in value


@pytest.mark.parametrize("kind", ["stale", "revision", "missing_target", "missing_output", "dimension", "scalar"])
def test_missing_stale_or_incompatible_values_are_unavailable_not_zero(kind):
    design, result = fixture(current=kind != "stale")
    if kind == "revision":
        result.design_revision = 6
    elif kind == "missing_target":
        design.requirements.target_thrust = None
    elif kind == "missing_output":
        result.outputs = {}
    elif kind == "dimension":
        result.outputs["thrust"] = Quantity(5, get_unit_registry().get("m"))
    elif kind == "scalar":
        result.outputs["thrust"] = 4500
    value = thrust_comparison(design)
    assert value["status"] == "UNAVAILABLE" and value["quantities"] == {} and value["code"]


def test_api_adds_comparison_beside_unchanged_canonical_current_result():
    design = seeded_design()
    canonical = design.workflow.current_result("performance").to_canonical_dict()
    value = get_stage_result_payload(design, "performance")
    assert value["result"] == canonical and value["displayable_as_current"]
    assert value["target_comparison"]["status"] == "UNAVAILABLE"
    # Phase4 now persists actual subsystem inputs, creating a newer input
    # revision. Never restamp the old performance result to match it.
    assert canonical["design_revision"] < design.revision
    assert value["target_comparison"]["code"] == "NO_CURRENT_PERFORMANCE"
    assert "target_comparison" not in canonical
