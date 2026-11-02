"""R01C invalid-assumption and defensive-projection regressions, in memory only."""

from __future__ import annotations

from copy import deepcopy

import pytest

from api.propulsion_workflow import create_design, run_phase3, update_requirements
from core.quantity import Quantity
from core.unit import SI
from systems.contracts.results import CalculationResult, ResultStatus
from systems.projects.models import DesignChangeEvent, PropulsionDesign
from systems.stages.operating_point import run_operating_point_stage
from systems.stages.thermochemistry import run_thermochemistry_stage

BAD_ASSUMPTIONS = [
    ("temperature", value) for value in (0., -1., float("nan"), float("inf"), -float("inf"), True)
] + [
    ("gamma", value) for value in (.5, 1., 3.01, float("nan"), float("inf"), -float("inf"), True)
] + [
    ("molar_mass", value) for value in (0., -.01, float("nan"), float("inf"), -float("inf"), True)
]


def design_with_current_assumptions() -> PropulsionDesign:
    design = create_design(name="R01C synthetic software regression only")
    update_requirements(design, {"target_chamber_pressure": 3e6, "ambient_pressure": 101325,
        "mixture_ratio": 2.5, "expansion_ratio": 10., "propellant_selection": "LOX/RP-1"})
    result = run_phase3(design, chamber_temperature_k=3500., gamma=1.2,
                       molecular_weight_kg_per_mol=.025, throat_area_m2=.001, expansion_ratio=10.)
    assert result["execution_ok"]
    return design


@pytest.mark.parametrize("stage", ["operating_point", "thermochemistry"])
@pytest.mark.parametrize("field,value", BAD_ASSUMPTIONS)
def test_bad_override_never_partially_mutates_operating_point(stage, field, value):
    design = design_with_current_assumptions()
    original = design.operating_point
    before = deepcopy(original.to_canonical_dict())
    names = ({"temperature": "chamber_temperature", "gamma": "gamma",
              "molar_mass": "molecular_weight_kg_per_mol"} if stage == "operating_point" else
             {"temperature": "assume_chamber_temperature_k", "gamma": "assume_gamma",
              "molar_mass": "assume_molar_mass_kg_per_mol"})
    kwargs = {names["temperature"]: 3200., names["gamma"]: 1.25, names["molar_mass"]: .022}
    kwargs[names[field]] = value
    runner = run_operating_point_stage if stage == "operating_point" else run_thermochemistry_stage
    result = runner(design, **kwargs)
    assert result.status is ResultStatus.FAILED
    assert result.errors[0]["code"] == "InvalidInputError"
    assert design.workflow.current_result(stage) is None
    assert design.operating_point is original
    assert design.operating_point.to_canonical_dict() == before
    assert design.workflow.current_result("performance") is None
    assert design.nozzle_design["geometry_status"] == "STALE"


@pytest.mark.parametrize("stage", ["operating_point", "thermochemistry"])
@pytest.mark.parametrize("field,value", [("gamma", .5), ("molar_mass", -.01), ("temperature", 0.)])
def test_invalid_restored_assumption_cannot_be_promoted_current(stage, field, value):
    design = design_with_current_assumptions()
    if field == "temperature":
        design.operating_point.chamber_temperature = Quantity(value, SI.get("K"))
    else:
        setattr(design.operating_point, "molecular_weight" if field == "molar_mass" else field, value)
    runner = run_operating_point_stage if stage == "operating_point" else run_thermochemistry_stage
    assert runner(design).status is ResultStatus.FAILED
    assert design.workflow.current_result(stage) is None


@pytest.mark.parametrize("field,value", BAD_ASSUMPTIONS)
def test_public_phase3_api_never_exposes_bad_assumptions_as_current(field, value):
    design = design_with_current_assumptions()
    before = deepcopy(design.operating_point.to_canonical_dict())
    kwargs = {"chamber_temperature_k": 3200., "gamma": 1.25,
              "molecular_weight_kg_per_mol": .022, "throat_area_m2": .001}
    key = {"temperature": "chamber_temperature_k", "gamma": "gamma", "molar_mass": "molecular_weight_kg_per_mol"}[field]
    kwargs[key] = value
    result = run_phase3(design, **kwargs)
    assert not result["execution_ok"]
    assert result["stages"]["operating_point"]["status"] == "FAILED"
    assert result["stages"]["thermochemistry"]["status"] == "FAILED"
    assert result["stages"]["performance"]["status"] == "FAILED"
    assert design.operating_point.to_canonical_dict() == before


def test_valid_boundary_assumptions_remain_supported():
    design = design_with_current_assumptions()
    original = design.operating_point
    result = run_operating_point_stage(design, chamber_temperature=3200., gamma=3., molecular_weight_kg_per_mol=.022)
    assert result.status is ResultStatus.CURRENT
    assert design.operating_point is original
    assert run_thermochemistry_stage(design).status is ResultStatus.CURRENT
    assert design.operating_point.gamma == 3.


def test_direct_thermochemistry_invalid_override_never_invokes_external_engine():
    design = design_with_current_assumptions()
    before = deepcopy(design.operating_point.to_canonical_dict())

    class MustNotRun:
        def evaluate(self, request):
            raise AssertionError("Invalid manual input must be rejected before engine dispatch")

    result = run_thermochemistry_stage(design, engine=MustNotRun(), assume_gamma=.5)
    assert result.status is ResultStatus.FAILED
    assert result.errors[0]["code"] == "InvalidInputError"
    assert design.operating_point.to_canonical_dict() == before


def test_calculation_canonical_projections_are_nested_defensive_copies():
    result = CalculationResult("projection-regression", inputs={"rows": [{"value": 1}]},
                               outputs={"nested": {"rows": [2, 3]}})
    before = deepcopy(result.to_canonical_dict())
    exported = result.to_canonical_dict()
    exported["inputs"]["rows"][0]["value"] = 9
    exported["outputs"]["nested"]["rows"].append(4)
    assert result.to_canonical_dict() == before
    restored = CalculationResult.from_canonical_dict(before)
    before["inputs"]["rows"][0]["value"] = 8
    before["outputs"]["nested"]["rows"].append(5)
    assert restored.inputs["rows"][0]["value"] == 1
    assert restored.outputs["nested"]["rows"] == [2, 3]


SLOTS = ("injector_design", "chamber_design", "thermal_design", "cooling_design",
         "nozzle_design", "structural_design", "material_selection")


def populated_projection_design():
    design = PropulsionDesign(name="Nested projection regression")
    for slot in SLOTS:
        setattr(design, slot, {"rows": [{"value": 1}]})
    design.subsystem_inputs = {"cooling": {"rows": [{"value": 1}]}}
    design.thermochemistry_configuration = {"metadata": {"source": ["original"]}}
    design.change_log = [DesignChangeEvent("nested", {"values": [1]}, {"values": [2]}, 1, "2026-10-13T00:00:00+00:00")]
    result = CalculationResult("projection-regression", outputs={"rows": [{"value": 1}]})
    design.workflow.results["performance"] = result
    design.workflow.result_history.append(result)
    return design


def mutate_projection(data):
    for slot in SLOTS:
        data[slot]["rows"][0]["value"] = 9
    data["subsystem_inputs"]["cooling"]["rows"][0]["value"] = 9
    data["thermochemistry_configuration"]["metadata"]["source"].append("mutated")
    data["change_log"][0]["old_value"]["values"].append(9)
    data["change_log"][0]["new_value"]["values"].append(9)
    data["workflow"]["results"]["performance"]["outputs"]["rows"][0]["value"] = 9
    data["workflow"]["result_history"][0]["outputs"]["rows"][0]["value"] = 9


def test_design_projection_and_restore_do_not_alias_nested_live_state():
    design = populated_projection_design()
    before = deepcopy(design.to_canonical_dict())
    exported = design.to_canonical_dict()
    mutate_projection(exported)
    assert design.to_canonical_dict() == before
    restored = PropulsionDesign.from_canonical_dict(before)
    restored_before = deepcopy(restored.to_canonical_dict())
    mutate_projection(before)
    assert restored.to_canonical_dict() == restored_before


def test_change_event_projection_and_restore_are_defensive():
    event = DesignChangeEvent("nested", {"value": [1]}, {"value": [2]}, 1, "2026-10-13T00:00:00+00:00")
    data = event.to_canonical_dict()
    restored = DesignChangeEvent.from_canonical_dict(data)
    data["old_value"]["value"].append(9)
    data["new_value"]["value"].append(9)
    assert event.old_value == restored.old_value == {"value": [1]}
    assert event.new_value == restored.new_value == {"value": [2]}
