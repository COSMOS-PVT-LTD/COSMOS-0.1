"""
COSMOS Rocket Propulsion Platform

Module: core.validation
Author: COSMOS Development Team
Version: 0.1.0

Purpose
-------
Provide reusable validation utilities for COSMOS.

Description
-----------
Centralized validation functions used throughout COSMOS for
engineering inputs, numerical solvers, geometry generation,
thermochemistry, gas dynamics, structures, cooling analysis,
and performance calculations.

All validation failures raise COSMOS-specific exceptions.

Examples
--------
>>> validate_positive(20.0, "chamber_pressure")
20.0

>>> validate_efficiency(0.95)
0.95

>>> validate_expansion_ratio(40.0)
40.0
"""

from __future__ import annotations

import math
from typing import Final

from core.exceptions import InvalidInputError

__all__ = (
    "MIN_EFFICIENCY",
    "MAX_EFFICIENCY",
    "validate_finite",
    "validate_positive",
    "validate_non_negative",
    "validate_range",
    "validate_efficiency",
    "validate_gamma",
    "validate_mixture_ratio",
    "validate_area",
    "validate_diameter",
    "validate_radius",
    "validate_expansion_ratio",
)

MIN_EFFICIENCY: Final[float] = 0.0
"""Minimum allowable efficiency [-]."""

MAX_EFFICIENCY: Final[float] = 1.0
"""Maximum allowable efficiency [-]."""


def validate_finite(value: float, name: str) -> float:
    """
    Validate that a value is finite.

    Parameters
    ----------
    value : float
        Value to validate.
    name : str
        Parameter name.

    Returns
    -------
    float
        Validated value.

    Raises
    ------
    InvalidInputError
        If value is NaN or infinite.
    """
    if not math.isfinite(value):
        raise InvalidInputError(
            f"{name} must be finite. Received {value!r}."
        )

    return value


def validate_positive(value: float, name: str) -> float:
    """
    Validate positive value.

    Parameters
    ----------
    value : float
        Input value.
    name : str
        Parameter name.

    Returns
    -------
    float
        Validated value.
    """
    validate_finite(value, name)

    if value <= 0.0:
        raise InvalidInputError(
            f"{name} must be greater than zero. "
            f"Received {value}."
        )

    return value


def validate_non_negative(value: float, name: str) -> float:
    """
    Validate non-negative value.

    Parameters
    ----------
    value : float
        Input value.
    name : str
        Parameter name.

    Returns
    -------
    float
        Validated value.
    """
    validate_finite(value, name)

    if value < 0.0:
        raise InvalidInputError(
            f"{name} must be non-negative. "
            f"Received {value}."
        )

    return value


def validate_range(
    value: float,
    minimum: float,
    maximum: float,
    name: str,
) -> float:
    """
    Validate value within range.

    Parameters
    ----------
    value : float
        Value to validate.
    minimum : float
        Lower limit.
    maximum : float
        Upper limit.
    name : str
        Parameter name.

    Returns
    -------
    float
        Validated value.
    """
    validate_finite(value, name)

    if not minimum <= value <= maximum:
        raise InvalidInputError(
            f"{name} must be between "
            f"{minimum} and {maximum}. "
            f"Received {value}."
        )

    return value


def validate_efficiency(value: float) -> float:
    """
    Validate efficiency.

    Units
    -----
    Dimensionless [-]
    """
    return validate_range(
        value,
        MIN_EFFICIENCY,
        MAX_EFFICIENCY,
        "efficiency",
    )


def validate_gamma(value: float) -> float:
    """
    Validate specific heat ratio.

    Units
    -----
    Dimensionless [-]
    """
    return validate_range(
        value,
        1.0,
        3.0,
        "gamma",
    )


def validate_mixture_ratio(value: float) -> float:
    """
    Validate oxidizer-to-fuel ratio.

    Units
    -----
    Dimensionless [-]
    """
    return validate_positive(
        value,
        "mixture_ratio",
    )


def validate_area(value: float) -> float:
    """
    Validate area.

    Units
    -----
    m²
    """
    return validate_positive(
        value,
        "area",
    )


def validate_diameter(value: float) -> float:
    """
    Validate diameter.

    Units
    -----
    m
    """
    return validate_positive(
        value,
        "diameter",
    )


def validate_radius(value: float) -> float:
    """
    Validate radius.

    Units
    -----
    m
    """
    return validate_positive(
        value,
        "radius",
    )


def validate_expansion_ratio(value: float) -> float:
    """
    Validate nozzle expansion ratio.

    Units
    -----
    Dimensionless [-]
    """
    return validate_positive(
        value,
        "expansion_ratio",
    )