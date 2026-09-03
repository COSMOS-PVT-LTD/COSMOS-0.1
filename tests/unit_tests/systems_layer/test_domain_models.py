"""Unit tests for propulsion design domain models."""

from __future__ import annotations

from core.quantity import Quantity
from core.unit import SI

from systems.cycle.models import CycleConfiguration, CycleImplementationStatus, CycleType
from systems.operating_point.models import OperatingPoint
from systems.projects.models import PropulsionDesign
from systems.propellants.models import PropellantConfiguration
from systems.requirements.models import DesignRequirements


def test_propulsion_design_identity_and_revision() -> None:
    design = PropulsionDesign(name="Demo Engine", engineer="TK NAYAK")
    assert design.design_id
    assert design.revision == 0
    design.bump_revision("name", "Demo Engine", "Demo Engine A")
    assert design.revision == 1
    assert design.change_log[-1].field == "name"


def test_requirements_optional_no_invented_defaults() -> None:
    req = DesignRequirements()
    assert req.target_thrust is None
    assert req.mixture_ratio is None
    payload = req.to_canonical_dict()
    assert payload["target_thrust"] is None


def test_propellant_configuration_round_trip() -> None:
    cfg = PropellantConfiguration(
        oxidizer_id="LOX",
        fuel_id="RP-1",
        mixture_ratio=2.3,
        oxidizer_temperature=Quantity(90.0, SI.get("K")),
    )
    restored = PropellantConfiguration.from_canonical_dict(cfg.to_canonical_dict())
    assert restored.oxidizer_id == "LOX"
    assert restored.mixture_ratio == 2.3
    assert restored.oxidizer_temperature is not None
    assert restored.oxidizer_temperature.to_si() == 90.0


def test_cycle_all_not_implemented_in_phase_2() -> None:
    for cycle in CycleType:
        cfg = CycleConfiguration.for_type(cycle)
        assert cfg.implementation_status is CycleImplementationStatus.NOT_IMPLEMENTED


def test_operating_point_uses_quantities() -> None:
    op = OperatingPoint(
        chamber_pressure=Quantity(7.0e6, SI.get("Pa")),
        gamma=1.2,
        gamma_is_assumption=True,
    )
    data = op.to_canonical_dict()
    assert data["gamma_is_assumption"] is True
    restored = OperatingPoint.from_canonical_dict(data)
    assert restored.chamber_pressure is not None
    assert restored.chamber_pressure.to_si() == 7.0e6


def test_design_canonical_round_trip() -> None:
    design = PropulsionDesign(name="Round Trip")
    design.requirements.target_chamber_pressure = Quantity(5.0e6, SI.get("Pa"))
    restored = PropulsionDesign.from_canonical_dict(design.to_canonical_dict())
    assert restored.name == "Round Trip"
    assert restored.requirements.target_chamber_pressure is not None
    assert len(restored.workflow.graph.nodes) == 17
