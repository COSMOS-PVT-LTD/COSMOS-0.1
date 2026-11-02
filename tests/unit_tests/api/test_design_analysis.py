"""Scientific execution gaps are not silently substituted or reported as success."""
import pytest

from api.propulsion_workflow import (
    get_workflow_payload,
    run_design_workflow,
)
from core.exceptions import InvalidInputError
from systems.contracts.results import ResultStatus
from systems.persistence.design_store import DesignStore
from systems.stages.consistency import run_consistency_stage
from systems.workflow.graph import StageDependency
from tests.unit_tests.api.test_cea_workflow import CONFIG, cea_design


def ready_case():
    pytest.importorskip("cea")
    design = cea_design()
    result = run_design_workflow(design, phase3_inputs={"thermochemistry_configuration": CONFIG, "throat_area_m2": .001},
        phase4_inputs={"characteristic_length_m": .8, "contraction_ratio": 3})
    return design, result


def test_one_run_preserves_successful_science_and_generates_actionable_input_requests():
    design, result = ready_case()
    assert result["phase_status"] == "INPUT_REQUIRED"
    assert result["execution_ok"] is True
    assert result["workflow_complete"] is False
    assert result["validation_level"] == "NOT_CLAIMED"
    assert design.workflow.current_result("performance") is not None
    assert design.workflow.current_result("design_review").outputs["review_verdict"] == "INCOMPLETE"
    for stage in ("injector", "thermal", "cooling", "materials", "structure"):
        assert design.workflow.results[stage].status is ResultStatus.NOT_CALCULATED
    assert any(r["stage_id"] == "materials" and r["fields"] == ["material_id"] for r in result["input_requests"])
    assert not any(r["status"] == "FAILED" for r in result["stages"].values())


def test_analysis_input_configuration_survives_reload_and_recalculation(tmp_path):
    design, _ = ready_case()
    assert design.subsystem_inputs["chamber"] == {"characteristic_length_m": .8, "contraction_ratio": 3}
    store = DesignStore(tmp_path)
    store.save(design)
    restored = store.load(design.design_id)
    result = run_design_workflow(restored)
    assert result["stages"]["chamber"]["status"] == "CURRENT"
    assert restored.chamber_design["characteristic_length_m"] == .8


def test_selected_cea_transport_is_exactly_sourced_and_does_not_choose_wall_temperature():
    design, _ = ready_case()
    result = run_design_workflow(design, phase4_inputs={"gas_property_mode": "CEA_CHAMBER_FROZEN_TRANSPORT"})
    assert design.workflow.current_result("thermal") is None
    request = next(r for r in result["input_requests"] if r["stage_id"] == "thermal")
    assert request["fields"] == ["wall_temperature_k"]
    result = run_design_workflow(design, phase4_inputs={"wall_temperature_k": 700.0})
    thermal = result["stages"]["thermal"]
    assert thermal["status"] == "CURRENT"
    thermo = design.workflow.current_result("thermochemistry")
    assert thermal["inputs"]["gas_property_source"]["thermochemistry_result_id"] == thermo.result_id
    assert design.thermal_design["cp_j_kg_k"] == thermo.outputs["rocket_stations"]["chamber"]["cp_frozen_j_kg_k"]
    assert design.subsystem_inputs["thermal"]["property_mode"] == "CEA_CHAMBER_FROZEN_TRANSPORT"


def test_invalid_values_still_fail_instead_of_becoming_input_required():
    design, _ = ready_case()
    result = run_design_workflow(design, phase4_inputs={"contraction_ratio": -2.0})
    assert result["execution_ok"] is False
    assert result["phase_status"] == "FAILED"
    assert design.workflow.results["chamber"].status is ResultStatus.FAILED
    assert design.workflow.current_result("performance") is not None


def test_invalid_material_is_not_defaulted_or_misreported_as_missing():
    design, _ = ready_case()
    result = run_design_workflow(design, phase4_inputs={"material_id": "NONEXISTENT"})
    assert result["execution_ok"] is False
    assert design.workflow.results["materials"].status is ResultStatus.FAILED


def test_thick_wall_requires_selection_and_retains_sourced_model_on_reload(tmp_path):
    design, _ = ready_case()
    # Room-temperature, smooth-cylinder software fixture; not the user's hot liner.
    p4 = {"wall_thickness_m": .006, "external_pressure_pa": 101325.,
          "material_temperature_k": 300., "material_id": "stainless_304"}
    thin = run_design_workflow(design, phase4_inputs=p4)["stages"]["structure"]
    assert thin["status"] == "OUT_OF_RANGE"
    assert thin["model_id"].endswith("thin_wall")
    result = run_design_workflow(design, phase4_inputs={"pressure_model": "LAME_CLOSED_ENDS"})
    thick = result["stages"]["structure"]
    assert thick["status"] == "CURRENT"
    assert thick["model_id"].endswith("lame_closed_ends")
    assert thick["inputs"]["pressure_model"] == "LAME_CLOSED_ENDS"
    assert thick["outputs"]["stress_basis"] == "BORE_VON_MISES"
    assert any("cooling-channel ligaments" in warning for warning in thick["warnings"])
    store = DesignStore(tmp_path)
    store.save(design)
    loaded = store.load(design.design_id)
    assert loaded.subsystem_inputs["structure"]["pressure_model"] == "LAME_CLOSED_ENDS"
    repeated = run_design_workflow(loaded)["stages"]["structure"]
    assert repeated["status"] == "CURRENT"
    assert repeated["outputs"] == thick["outputs"]


def test_pressure_model_unknown_is_rejected_without_mutation():
    design, _ = ready_case()
    revision, inputs = design.revision, dict(design.subsystem_inputs)
    with pytest.raises(InvalidInputError):
        run_design_workflow(design, phase4_inputs={"pressure_model": "AUTO"})
    assert design.revision == revision
    assert design.subsystem_inputs == inputs


def test_lame_selection_does_not_waive_material_range_or_buckling():
    design, _ = ready_case()
    base = {"wall_thickness_m": .006, "external_pressure_pa": 101325.,
            "material_temperature_k": 900., "material_id": "stainless_304",
            "pressure_model": "LAME_CLOSED_ENDS"}
    hot = run_design_workflow(design, phase4_inputs=base)["stages"]["structure"]
    assert hot["status"] == "OUT_OF_RANGE"
    pc = design.operating_point.chamber_pressure.to_si()
    external = run_design_workflow(design, phase4_inputs={"material_temperature_k": 300.,
        "external_pressure_pa": pc+1})["stages"]["structure"]
    assert external["status"] == "OUT_OF_RANGE"
    assert any("buckling" in error["message"] for error in external["errors"])


@pytest.mark.parametrize("bad", [{"phase3_inputs": []}, {"phase4_inputs": []}, {"phase3_inputs": {"engine": "unsafe"}}])
def test_nested_analysis_command_fields_are_strict(bad):
    with pytest.raises(InvalidInputError):
        run_design_workflow(cea_design(), **bad)


def test_identity_current_is_not_a_missing_calculation_and_cycle_capability_is_truthful():
    design = cea_design()
    from api.propulsion_workflow import update_cycle
    update_cycle(design, "PRESSURE_FED")
    nodes = {r["stage_id"]: r for r in get_workflow_payload(design)["nodes"]}
    assert nodes["design_project"]["result_is_current"] is True
    assert nodes["cycle"]["implementation_status"] == "PARTIAL"
    assert nodes["cycle"]["available_selected_models"] == ["PRESSURE_FED", "GAS_GENERATOR"]
    assert not nodes["cycle"]["result_is_current"]


def test_explicit_analysis_refreshes_identity_after_edit_without_fake_result():
    design, _ = ready_case()
    from api.propulsion_workflow import update_requirements
    update_requirements(design, {"notes": "Changed study boundary notes"})
    run_design_workflow(design)
    node = next(r for r in get_workflow_payload(design)["nodes"] if r["stage_id"] == "design_project")
    assert node["status"] == "CURRENT" and node["result_is_current"]
    assert node["result_id"] is None and not node["has_current_result"]
    assert "design_project" not in design.workflow.results
    assert get_workflow_payload(design)["workflow_complete"] is False


def test_consistency_checks_actual_boolean_required_dependency_failure():
    design, _ = ready_case()
    design.workflow.graph.get("performance").dependencies += (StageDependency("cycle"),)
    result = run_consistency_stage(design)
    assert result.status is ResultStatus.FAILED
    assert any("REQUIRED dependency 'cycle'" in row for row in result.outputs["violations"])
