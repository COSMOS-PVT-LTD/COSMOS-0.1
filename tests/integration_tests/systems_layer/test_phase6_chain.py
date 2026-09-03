"""Phase 6 — summary, consistency, design review, export."""

from __future__ import annotations

from api.propulsion_workflow import (
    create_design,
    export_design,
    get_stage_result_payload,
    run_phase3,
    run_phase4,
    run_phase6,
    update_requirements,
)
from systems.contracts.results import ResultStatus


def _seeded_design():
    design = create_design(name="Phase6")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 5.0e6,
            "ambient_pressure": 101325.0,
            "mixture_ratio": 2.3,
            "expansion_ratio": 8.0,
            "propellant_selection": "LOX/RP-1",
        },
    )
    p3 = run_phase3(
        design,
        chamber_temperature_k=3000.0,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.01,
        expansion_ratio=8.0,
    )
    assert p3["ok"] is True
    p4 = run_phase4(
        design,
        characteristic_length_m=1.0,
        contraction_ratio=2.5,
        wall_thickness_m=0.006,
    )
    assert p4["ok"] is True
    return design


def test_phase6_summary_consistency_review() -> None:
    design = _seeded_design()
    p6 = run_phase6(design)
    assert p6["ok"] is True
    assert p6["stages"]["performance_summary"]["status"] == ResultStatus.CURRENT.value
    assert p6["stages"]["consistency"]["status"] == ResultStatus.CURRENT.value
    assert p6["stages"]["design_review"]["status"] == ResultStatus.CURRENT.value
    consolidated = p6["stages"]["performance_summary"]["outputs"]["consolidated"]
    assert "thrust" in consolidated
    assert "specific_impulse" in consolidated
    assert p6["stages"]["design_review"]["outputs"]["review_ready"] is True
    assert design.workflow.graph.get("design_review").implementation_status.value == (
        "IMPLEMENTED"
    )


def test_export_package_separates_current_results() -> None:
    design = _seeded_design()
    run_phase6(design)
    package = export_design(design)
    assert package["export_format"] == "cosmos.propulsion_design_package"
    assert "thrust" in package["current_results"]["performance"]["outputs"]
    assert "design_review" in package["current_results"]
    assert "NOT flight-certified" in package["disclaimer"]


def test_stale_result_not_displayable_as_current() -> None:
    design = _seeded_design()
    run_phase6(design)
    # Force stale on performance
    design.workflow.results["performance"].mark_stale()
    design.workflow.graph.get("performance").status = ResultStatus.STALE
    payload = get_stage_result_payload(design, "performance", allow_stale=False)
    assert payload["displayable_as_current"] is False
    assert payload["ok"] is False
    stale_payload = get_stage_result_payload(design, "performance", allow_stale=True)
    assert stale_payload["displayable_as_current"] is False
    assert stale_payload["result"]["status"] == ResultStatus.STALE.value
