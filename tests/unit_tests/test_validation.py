"""
Unit tests for core.validation.
"""

from __future__ import annotations

import math

import pytest

from core.exceptions import InvalidInputError
from core.validation import (
    validate_area,
    validate_diameter,
    validate_efficiency,
    validate_expansion_ratio,
    validate_finite,
    validate_gamma,
    validate_mixture_ratio,
    validate_non_negative,
    validate_positive,
    validate_radius,
)


def test_validate_positive_success() -> None:
    assert validate_positive(10.0, "pressure") == 10.0


def test_validate_positive_failure() -> None:
    with pytest.raises(InvalidInputError):
        validate_positive(0.0, "pressure")


def test_validate_non_negative_success() -> None:
    assert validate_non_negative(0.0, "mass") == 0.0


def test_validate_non_negative_failure() -> None:
    with pytest.raises(InvalidInputError):
        validate_non_negative(-1.0, "mass")


def test_validate_finite_nan() -> None:
    with pytest.raises(InvalidInputError):
        validate_finite(math.nan, "value")


def test_validate_finite_inf() -> None:
    with pytest.raises(InvalidInputError):
        validate_finite(math.inf, "value")


def test_validate_efficiency_success() -> None:
    assert validate_efficiency(0.95) == 0.95


def test_validate_efficiency_failure() -> None:
    with pytest.raises(InvalidInputError):
        validate_efficiency(1.2)


def test_validate_gamma_success() -> None:
    assert validate_gamma(1.4) == 1.4


def test_validate_gamma_at_one_rejected() -> None:
    with pytest.raises(InvalidInputError):
        validate_gamma(1.0)


def test_validate_gamma_failure() -> None:
    with pytest.raises(InvalidInputError):
        validate_gamma(0.9)


def test_validate_mixture_ratio_success() -> None:
    assert validate_mixture_ratio(3.5) == 3.5


def test_validate_area_success() -> None:
    assert validate_area(0.01) == 0.01


def test_validate_diameter_success() -> None:
    assert validate_diameter(0.1) == 0.1


def test_validate_radius_success() -> None:
    assert validate_radius(0.05) == 0.05


def test_validate_expansion_ratio_success() -> None:
    assert validate_expansion_ratio(40.0) == 40.0