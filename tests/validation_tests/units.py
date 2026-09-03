"""Validation tests for unit conversion reversibility."""

from __future__ import annotations

import pytest

from core.unit import SI


@pytest.mark.parametrize(
    ("symbol", "value"),
    (
        ("mm", 1234.5),
        ("cm", 42.0),
        ("km", 3.5),
        ("in", 12.0),
        ("ft", 100.0),
        ("lb", 150.0),
        ("psi", 14.7),
        ("bar", 2.0),
        ("atm", 1.0),
        ("degC", 25.0),
        ("deg", 90.0),
    ),
)
def test_unit_si_round_trip(symbol: str, value: float) -> None:
    unit = SI.get(symbol)
    si_value = unit.convert_to_si(value)
    round_trip = unit.convert_from_si(si_value)
    assert round_trip == pytest.approx(value)
