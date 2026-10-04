"""API → Systems → frozen Physics remediation qualification."""

import pytest

from api.propulsion_workflow import (
    create_design,
    get_workflow_payload,
    run_phase3,
    run_phase4,
    run_phase6,
    update_requirements,
)
from core.quantity import Quantity
from systems.contracts.results import CalculationResult, ResultStatus
from systems.stages.performance import run_performance_stage
from systems.stages.structure import run_structure_stage
from systems.stages.thermal import run_thermal_stage
from systems.workflow.readiness import readiness_payload


def seeded_design():
    design = create_design(name="Explicit preliminary analysis")
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
    result = run_phase3(
        design,
        chamber_temperature_k=3000,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.01,
    )
    assert result["execution_ok"] is True
    return design


def explicit_phase4(design, **overrides):
    inputs = {
        "characteristic_length_m": 1.0,
        "contraction_ratio": 2.5,
        "wall_thickness_m": 0.006,
        "material_id": "stainless_304",
        "external_pressure_pa": 0,
        "material_temperature_k": 300,
        "viscosity_pa_s": 8e-5,
        "conductivity_w_m_k": 0.3,
        "cp_j_kg_k": 2500,
        "wall_temperature_k": 800,
    }
    inputs.update(overrides)
    return run_phase4(design, **inputs)


def test_execution_success_is_not_complete_design() -> None:
    design = seeded_design()
    p4 = explicit_phase4(design)
    assert p4["execution_ok"] is True
    assert p4["workflow_complete"] is False
    assert p4["engineering_readiness"] == "PRELIMINARY"
    assert p4["validation_level"] == "NOT_CLAIMED"
    assert p4["stages"]["nozzle"]["status"] == "CURRENT"
    assert any("DEFERRED" in warning for warning in p4["stages"]["nozzle"]["warnings"])
    p6 = run_phase6(design)
    assert p6["execution_ok"] is True
    assert p6["workflow_complete"] is False
    assert p6["stages"]["design_review"]["outputs"]["review_verdict"] == "INCOMPLETE"
    assert get_workflow_payload(design)["validation_level"] == "NOT_CLAIMED"


def test_missing_phase4_inputs_fail_without_defaults() -> None:
    result = run_phase4(seeded_design())
    assert result["execution_ok"] is False
    for stage in ("chamber", "thermal", "materials", "structure"):
        assert result["stages"][stage]["status"] == "FAILED"


def test_failed_required_thermochemistry_blocks_performance() -> None:
    design = seeded_design()
    previous = design.workflow.results["performance"]
    design.store_stage_result(
        "thermochemistry",
        CalculationResult(calculation_type="thermo", status=ResultStatus.FAILED),
    )
    assert previous.status is ResultStatus.STALE
    result = run_performance_stage(design)
    assert result.status is ResultStatus.FAILED
    assert "thermochemistry=FAILED" in result.errors[0]["message"]
    assert not result.outputs


def test_missing_ambient_pressure_fails() -> None:
    design = seeded_design()
    update_requirements(design, {"ambient_pressure": None})
    result = run_phase3(
        design,
        chamber_temperature_k=3000,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.01,
    )
    assert result["execution_ok"] is False
    assert "ambient_pressure" in result["stages"]["performance"]["errors"][0]["message"]


@pytest.mark.parametrize(
    "missing",
    ["viscosity_pa_s", "conductivity_w_m_k", "cp_j_kg_k", "wall_temperature_k"],
)
def test_missing_thermal_properties_fail(missing: str) -> None:
    design = seeded_design()
    result = explicit_phase4(design, **{missing: None})
    assert result["stages"]["thermal"]["status"] == "FAILED"
    assert missing in result["stages"]["thermal"]["errors"][0]["message"]


def test_bartz_curvature_and_taw_approximation_are_exposed() -> None:
    design = seeded_design()
    p4 = explicit_phase4(design)
    original = p4["stages"]["thermal"]
    assert original["inputs"]["curvature_correction"] == "ABSENT"
    radius = 0.1
    design.nozzle_design["throat_curvature_radius_m"] = radius
    result = run_thermal_stage(design)
    assert result.status is ResultStatus.CURRENT
    factor = (design.thermal_design["throat_diameter_m"] / radius) ** 0.1
    assert result.outputs["curvature_factor"]["value"] == pytest.approx(factor)
    h0 = Quantity.from_canonical_dict(original["outputs"]["h"]).to_si()
    h1 = Quantity.from_canonical_dict(result.outputs["h"]).to_si()
    assert h1 / h0 == pytest.approx(factor)
    assert "NOT computed" in result.inputs["taw_approximation"]


def test_readiness_cannot_ignore_required_missing_result() -> None:
    design = seeded_design()
    design.workflow.results["thermochemistry"].status = ResultStatus.NOT_IMPLEMENTED
    payload = readiness_payload(design.workflow)
    assert payload["engineering_readiness"] == "INCOMPLETE"
    assert payload["workflow_complete"] is False


def test_explicit_curvature_is_persisted_for_recalculation() -> None:
    design = seeded_design()
    result = explicit_phase4(design, throat_curvature_radius_m=0.1)
    assert result["execution_ok"] is True
    assert design.thermal_design["throat_curvature_radius_m"] == 0.1
    recalculated = run_thermal_stage(design)
    assert recalculated.inputs["curvature_correction"] == "APPLIED"
    assert (
        recalculated.outputs["curvature_factor"]
        == result["stages"]["thermal"]["outputs"]["curvature_factor"]
    )


def test_review_recalculation_does_not_treat_itself_as_missing_upstream() -> None:
    design = seeded_design()
    explicit_phase4(design)
    run_phase6(design)
    result = run_phase6(design)
    outputs = result["stages"]["design_review"]["outputs"]
    assert outputs["review_verdict"] == "INCOMPLETE"
    assert not any(
        reason.startswith("design_review ") for reason in outputs["incomplete_reasons"]
    )


def test_failed_recalculation_marks_retained_geometry_stale() -> None:
    from physics.quantities import pascal

    design = seeded_design()
    explicit_phase4(design)
    result = run_structure_stage(design, external_pressure=pascal(6e6))
    assert result.status is ResultStatus.OUT_OF_RANGE
    assert design.structural_design["geometry_status"] == "STALE"
    assert design.workflow.current_result("structure") is None

    design = seeded_design()
    explicit_phase4(design)
    design.store_stage_result(
        "performance",
        CalculationResult(
            calculation_type="test",
            status=ResultStatus.FAILED,
        ),
    )
    for slot in (
        design.nozzle_design,
        design.chamber_design,
        design.thermal_design,
        design.structural_design,
    ):
        assert slot["geometry_status"] == "STALE"
