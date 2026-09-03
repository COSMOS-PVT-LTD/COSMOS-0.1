"""Unit tests for core.quantity dimensional safety."""

from __future__ import annotations

import math

import pytest

from core.dimension import MASS, TIME, VELOCITY
from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity, dimensionless
from core.unit import SI


def _q(magnitude: float, symbol: str) -> Quantity:
    return Quantity(magnitude=magnitude, unit=SI.get(symbol))


def test_length_addition_valid() -> None:
    total = _q(1.0, "m") + _q(2.0, "m")
    assert total.magnitude == pytest.approx(3.0)
    assert total.unit.symbol == "m"


def test_length_plus_time_invalid() -> None:
    with pytest.raises(DimensionError):
        _ = _q(1.0, "m") + _q(1.0, "s")


def test_pressure_over_density_yields_velocity_squared_dimension() -> None:
    pressure = _q(100_000.0, "Pa")
    density = _q(1.2, "kg/m3")
    ratio = pressure / density
    assert ratio.dimension().is_compatible_with(VELOCITY * VELOCITY)


def test_mass_over_time_is_mass_flow_rate() -> None:
    flow = _q(10.0, "kg") / _q(2.0, "s")
    assert flow.unit.dimension.is_compatible_with(MASS / TIME)


def test_dimensionless_times_quantity() -> None:
    scaled = 2.0 * _q(5.0, "m")
    assert scaled.magnitude == pytest.approx(10.0)


def test_explicit_conversion_mm_to_m() -> None:
    length_mm = _q(1000.0, "mm")
    length_m = length_mm.convert_to(SI.get("m"))
    assert length_m.magnitude == pytest.approx(1.0)


def test_incompatible_conversion_rejected() -> None:
    with pytest.raises(DimensionError):
        _q(1.0, "m").convert_to(SI.get("s"))


def test_nan_rejected() -> None:
    with pytest.raises(InvalidInputError):
        _ = Quantity(magnitude=float("nan"), unit=SI.get("m"))


def test_infinity_rejected() -> None:
    with pytest.raises(InvalidInputError):
        _ = Quantity(magnitude=float("inf"), unit=SI.get("m"))


def test_division_by_zero_quantity_rejected() -> None:
    with pytest.raises(InvalidInputError):
        _ = _q(1.0, "m") / _q(0.0, "s")


def test_quantity_canonical_hash_stable() -> None:
    from core.hashing import canonical_hash

    first = _q(42.0, "Pa")
    second = Quantity.from_canonical_dict(first.to_canonical_dict())
    assert canonical_hash(first) == canonical_hash(second)


def test_dimensionless_helper() -> None:
    value = dimensionless(0.95)
    assert value.is_dimensionless()


def test_convert_round_trip() -> None:
    original = _q(2500.0, "mm")
    round_trip = original.convert_to(SI.get("m")).convert_to(SI.get("mm"))
    assert round_trip.approx_equal(original)


@pytest.mark.parametrize("value", (-1.0e300, 0.0, 1.0e300))
def test_scalar_multiplication_finite(value: float) -> None:
    if not math.isfinite(value):
        pytest.skip("Platform may not preserve extreme values.")
    result = value * _q(2.0, "m")
    assert math.isfinite(result.magnitude)
