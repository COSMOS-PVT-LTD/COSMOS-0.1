"""Phase 4 subsystem chain tests."""

from __future__ import annotations

from api.propulsion_workflow import create_design, run_phase3, run_phase4, update_requirements
from systems.contracts.results import ResultStatus


def test_phase3_then_phase4_subsystems() -> None:
    design = create_design(name="Phase4")
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
    assert p4["stages"]["injector"]["status"] == ResultStatus.NOT_IMPLEMENTED.value
    assert p4["stages"]["cooling"]["status"] == ResultStatus.NOT_IMPLEMENTED.value
    assert p4["stages"]["chamber"]["status"] == ResultStatus.CURRENT.value
    assert p4["stages"]["thermal"]["status"] == ResultStatus.CURRENT.value
    assert p4["stages"]["structure"]["status"] == ResultStatus.CURRENT.value
    assert design.chamber_design is not None
    assert design.thermal_design is not None
    assert float(design.structural_design["hoop_stress_pa"]) > 0.0
