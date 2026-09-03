"""Unit tests for core.dimension."""

from __future__ import annotations

import pytest

from core.dimension import (
    DIMENSIONLESS,
    LENGTH,
    MASS,
    PRESSURE,
    TIME,
    VELOCITY,
    Dimension,
)
from core.exceptions import DimensionError


def test_dimensionless_is_all_zero_exponents() -> None:
    assert DIMENSIONLESS.is_dimensionless()
    assert DIMENSIONLESS.exponents == (0, 0, 0, 0, 0, 0, 0)


def test_velocity_dimension_from_length_over_time() -> None:
    assert (LENGTH / TIME).is_compatible_with(VELOCITY)


def test_pressure_dimension_from_force_over_area() -> None:
    derived = (MASS * LENGTH / (TIME**2)) / (LENGTH**2)
    assert derived.is_compatible_with(PRESSURE)


def test_incompatible_dimensions_detected() -> None:
    assert not LENGTH.is_compatible_with(TIME)


def test_dimension_multiplication_and_division() -> None:
    assert (LENGTH * TIME).exponents == (
        1,
        0,
        1,
        0,
        0,
        0,
        0,
    )
    assert (LENGTH / TIME).is_compatible_with(VELOCITY)


def test_dimension_power() -> None:
    assert (LENGTH**3).exponents == (3, 0, 0, 0, 0, 0, 0)


def test_dimension_power_requires_integer() -> None:
    with pytest.raises(DimensionError):
        _ = LENGTH**1.5  # type: ignore[operator]


def test_canonical_round_trip() -> None:
    original = Dimension(length=2, mass=-1, time=-2)
    restored = Dimension.from_canonical_dict(original.to_canonical_dict())
    assert restored == original
