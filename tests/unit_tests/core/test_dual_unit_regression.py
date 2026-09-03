"""Regression: legacy core.units factors must match core.unit SI registry."""

from __future__ import annotations

import pytest

from core import units as legacy_units
from core.constants import PSI_TO_PASCAL
from core.unit import SI


@pytest.mark.parametrize(
    ("legacy_fn", "registry_symbol", "value"),
    (
        (legacy_units.psi_to_pascals, "psi", 1.0),
        (legacy_units.bar_to_pascals, "bar", 1.0),
        (legacy_units.celsius_to_kelvin, "degC", 0.0),
        (legacy_units.millimeters_to_meters, "mm", 1000.0),
    ),
)
def test_legacy_scalar_matches_unit_registry(
    legacy_fn,
    registry_symbol: str,
    value: float,
) -> None:
    registry = SI.get(registry_symbol)
    assert legacy_fn(value) == pytest.approx(registry.convert_to_si(value))


def test_psi_constant_matches_registry() -> None:
    assert SI.get("psi").si_scale == pytest.approx(PSI_TO_PASCAL)
