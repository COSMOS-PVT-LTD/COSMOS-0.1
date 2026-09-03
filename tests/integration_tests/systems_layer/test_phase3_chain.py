"""Phase 3 orchestration integration tests."""

from __future__ import annotations

from core.quantity import Quantity
from core.unit import SI

from api.propulsion_workflow import create_design, run_phase3, update_requirements
from systems.contracts.results import ResultStatus
from systems.workflow.orchestrator import run_phase3_chain


def test_phase3_chain_with_assumed_thermo() -> None:
    design = create_design(name="Phase3 Demo")
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
    outcome = run_phase3_chain(
        design,
        chamber_temperature_k=3000.0,
        gamma=1.2,
        molecular_weight_kg_per_mol=0.022,
        throat_area_m2=0.01,
        expansion_ratio=8.0,
    )
    assert outcome.stages["requirements"].status is ResultStatus.CURRENT
    assert outcome.stages["propellants"].status is ResultStatus.CURRENT
    assert outcome.stages["operating_point"].status is ResultStatus.CURRENT
    assert outcome.stages["thermochemistry"].status is ResultStatus.CURRENT
    assert "ASSUMED" in " ".join(outcome.stages["thermochemistry"].assumptions).upper() or any(
        "assum" in a.lower() for a in outcome.stages["thermochemistry"].assumptions
    )
    assert outcome.stages["performance"].status is ResultStatus.CURRENT
    thrust = outcome.stages["performance"].outputs["thrust"]["magnitude"]
    assert float(thrust) > 0.0
    assert outcome.ok is True


def test_phase3_cea_unbound_without_assumptions_is_honest() -> None:
    design = create_design(name="No Thermo")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 5.0e6,
            "propellant_selection": "LOX/RP-1",
            "mixture_ratio": 2.3,
        },
    )
    outcome = run_phase3_chain(design)
    assert outcome.stages["propellants"].status is ResultStatus.CURRENT
    assert outcome.stages["thermochemistry"].status is ResultStatus.NOT_IMPLEMENTED
    assert outcome.stages["performance"].status is ResultStatus.FAILED
    assert outcome.ok is False


def test_api_run_phase3_summary() -> None:
    design = create_design(name="API Phase3")
    update_requirements(
        design,
        {
            "target_chamber_pressure": 7.0e6,
            "expansion_ratio": 10.0,
            "propellant_selection": "LOX/LH2",
            "mixture_ratio": 6.0,
        },
    )
    summary = run_phase3(
        design,
        chamber_temperature_k=3200.0,
        gamma=1.25,
        molecular_weight_kg_per_mol=0.014,
        throat_area_m2=0.005,
        expansion_ratio=10.0,
    )
    assert summary["ok"] is True
    assert summary["stages"]["performance"]["status"] == "CURRENT"
