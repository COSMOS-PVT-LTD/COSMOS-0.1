"""Unit tests for core.unit."""

from __future__ import annotations

import pytest

from core.constants import CELSIUS_ZERO_IN_KELVIN
from core.exceptions import UnitError
from core.unit import SI, Unit, get_unit_registry


def test_registry_contains_si_base_units() -> None:
    registry = get_unit_registry()
    assert registry.get("m").symbol == "m"
    assert registry.get("kg").symbol == "kg"
    assert registry.get("s").symbol == "s"


def test_unit_convert_to_si_and_back() -> None:
    metre = SI.get("m")
    assert metre.convert_to_si(2.5) == pytest.approx(2.5)
    assert metre.convert_from_si(2.5) == pytest.approx(2.5)


def test_millimetre_conversion_round_trip() -> None:
    millimetre = SI.get("mm")
    value = 1250.0
    metres = millimetre.convert_to_si(value)
    assert millimetre.convert_from_si(metres) == pytest.approx(value)


def test_celsius_affine_conversion() -> None:
    celsius = SI.get("degC")
    assert celsius.convert_to_si(0.0) == pytest.approx(CELSIUS_ZERO_IN_KELVIN)
    assert celsius.convert_from_si(373.15) == pytest.approx(100.0)


def test_unknown_unit_raises() -> None:
    with pytest.raises(UnitError):
        SI.get("unknown")


def test_duplicate_registry_symbol_rejected() -> None:
    metre = SI.get("m")
    with pytest.raises(UnitError):
        _ = type(SI)(units=(metre, metre))


def test_unit_canonical_round_trip() -> None:
    unit = SI.get("Pa")
    restored = Unit.from_canonical_dict(unit.to_canonical_dict())
    assert restored.symbol == unit.symbol
    assert restored.dimension == unit.dimension
    assert restored.si_scale == unit.si_scale
