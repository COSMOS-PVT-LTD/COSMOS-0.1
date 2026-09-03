"""
Independent tests for affine temperature semantics (CORE-002-AFFINE-001).

These tests encode the mathematical contract, not merely the implementation.
"""

from __future__ import annotations

import math

import pytest

from core.constants import CELSIUS_ZERO_IN_KELVIN
from core.exceptions import UnitError
from core.hashing import canonical_hash
from core.quantity import Quantity, QuantityKind, temperature_interval
from core.unit import SI


def _c(value: float) -> Quantity:
    return Quantity(value, SI.get("degC"))


def _k(value: float) -> Quantity:
    return Quantity(value, SI.get("K"))


def test_celsius_to_kelvin_conversion() -> None:
    assert _c(0.0).to_si() == pytest.approx(273.15)
    assert _c(100.0).to_si() == pytest.approx(373.15)


def test_kelvin_to_celsius_conversion() -> None:
    assert _k(273.15).convert_to(SI.get("degC")).magnitude == pytest.approx(0.0)
    assert _k(373.15).convert_to(SI.get("degC")).magnitude == pytest.approx(100.0)


def test_absolute_celsius_addition_is_invalid() -> None:
    with pytest.raises(UnitError):
        _ = _c(0.0) + _c(100.0)


def test_absolute_kelvin_addition_is_invalid() -> None:
    with pytest.raises(UnitError):
        _ = _k(273.15) + _k(100.0)


def test_celsius_subtraction_yields_kelvin_interval() -> None:
    delta = _c(100.0) - _c(0.0)
    assert delta.kind is QuantityKind.INTERVAL
    assert delta.to_si() == pytest.approx(100.0)
    assert delta.unit.symbol == "K"


def test_celsius_plus_kelvin_interval() -> None:
    result = _c(20.0) + temperature_interval(10.0)
    assert result.kind is QuantityKind.ABSOLUTE
    assert result.to_si() == pytest.approx(303.15)
    assert result.convert_to(SI.get("degC")).magnitude == pytest.approx(30.0)


def test_celsius_minus_interval() -> None:
    result = _c(30.0) - temperature_interval(10.0)
    assert result.to_si() == pytest.approx(293.15)
    assert result.convert_to(SI.get("degC")).magnitude == pytest.approx(20.0)


def test_celsius_scalar_multiplication_scales_native_magnitude() -> None:
    doubled = _c(20.0) * 2.0
    assert doubled.magnitude == pytest.approx(40.0)
    assert doubled.unit.symbol == "degC"


def test_celsius_times_time_uses_thermodynamic_si() -> None:
    from core.quantity import Quantity as Q

    product = _c(25.0) * Q(3600.0, SI.get("s"))
    assert product.to_si() == pytest.approx(298.15 * 3600.0, rel=1.0e-12)


def test_interval_serialization_and_hash_stable() -> None:
    delta = _c(100.0) - _c(0.0)
    restored = type(delta).from_canonical_dict(delta.to_canonical_dict())
    assert restored.to_si() == pytest.approx(100.0)
    assert canonical_hash(delta) == canonical_hash(restored)


@pytest.mark.parametrize("bad", (float("nan"), float("inf"), float("-inf")))
def test_affine_quantity_rejects_non_finite(bad: float) -> None:
    with pytest.raises(Exception):
        _ = Quantity(bad, SI.get("degC"))


def test_negative_celsius_absolute_allowed() -> None:
    assert _c(-40.0).to_si() == pytest.approx(CELSIUS_ZERO_IN_KELVIN - 40.0)


def test_regression_cases_from_audit() -> None:
    with pytest.raises(UnitError):
        (_c(0.0) + _c(100.0)).to_si()

    delta = _c(100.0) - _c(0.0)
    assert delta.to_si() == pytest.approx(100.0)
    assert not math.isclose(delta.magnitude, -173.15)

    product = _c(25.0) * Quantity(3600.0, SI.get("s"))
    assert product.to_si() == pytest.approx(298.15 * 3600.0)
