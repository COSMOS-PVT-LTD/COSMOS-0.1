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
from collections.abc import Collection, Mapping
from typing import Final, TypeVar

from core.contracts import ValidationIssue, ValidationResult, ValidationSeverity
from core.exceptions import InvalidInputError

__all__ = (
    "MIN_EFFICIENCY",
    "MAX_EFFICIENCY",
    "validate_finite",
    "validate_positive",
    "validate_non_negative",
    "validate_strictly_positive",
    "validate_not_none",
    "validate_type",
    "validate_range",
    "validate_collection_not_empty",
    "validate_mapping_keys",
    "validate_efficiency",
    "validate_gamma",
    "validate_mixture_ratio",
    "validate_area",
    "validate_diameter",
    "validate_radius",
    "validate_expansion_ratio",
    "collect_validation",
)

T = TypeVar("T")

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


def validate_strictly_positive(value: float, name: str) -> float:
    """
    Validate strictly positive value (excludes zero).

    Raises
    ------
    InvalidInputError
        If value is not strictly positive.
    """

    validate_finite(value, name)

    if value <= 0.0:
        raise InvalidInputError(
            f"{name} must be strictly positive. Received {value}."
        )

    return value


def validate_not_none(value: T | None, name: str) -> T:
    """
    Validate that a value is not ``None``.

    Raises
    ------
    InvalidInputError
        If value is ``None``.
    """

    if value is None:
        raise InvalidInputError(f"{name} must not be None.")

    return value


def validate_type(value: object, expected_type: type[T], name: str) -> T:
    """
    Validate runtime type.

    Raises
    ------
    InvalidInputError
        If value is not an instance of ``expected_type``.
    """

    if not isinstance(value, expected_type):
        raise InvalidInputError(
            f"{name} must be {expected_type.__name__}. "
            f"Received {type(value).__name__}."
        )

    return value


def validate_collection_not_empty(
    value: Collection[object],
    name: str,
) -> Collection[object]:
    """
    Validate that a collection contains at least one item.

    Raises
    ------
    InvalidInputError
        If the collection is empty.
    """

    if len(value) == 0:
        raise InvalidInputError(f"{name} must not be empty.")

    return value


def validate_mapping_keys(
    mapping: Mapping[str, object],
    required_keys: tuple[str, ...],
    name: str,
) -> Mapping[str, object]:
    """
    Validate required mapping keys exist.

    Raises
    ------
    InvalidInputError
        If any required key is missing.
    """

    missing = tuple(key for key in required_keys if key not in mapping)
    if missing:
        joined = ", ".join(missing)
        raise InvalidInputError(
            f"{name} missing required keys: {joined}."
        )

    return mapping


def collect_validation(*checks: ValidationResult) -> ValidationResult:
    """
    Merge multiple validation results deterministically.

    Returns
    -------
    ValidationResult
        Combined result preserving issue order.
    """

    issues: list[ValidationIssue] = []
    is_valid = True

    for check in checks:
        if not check.is_valid:
            is_valid = False
        issues.extend(check.issues)

    return ValidationResult(is_valid=is_valid, issues=tuple(issues))


def validation_issue(
    code: str,
    message: str,
    *,
    field: str | None = None,
    severity: str = ValidationSeverity.ERROR,
) -> ValidationIssue:
    """Construct a validation issue."""

    return ValidationIssue(
        code=code,
        message=message,
        field=field,
        severity=severity,
    )


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
    Validate specific heat ratio for compressible-flow relations.

    Isentropic and shock relations require ``gamma > 1``.
    """
    validate_finite(value, "gamma")
    if value <= 1.0:
        raise InvalidInputError(
            f"gamma must be greater than 1. Received {value}."
        )
    if value > 3.0:
        raise InvalidInputError(
            f"gamma must be between 1 and 3. Received {value}."
        )
    return value


def validate_mixture_ratio(value: float) -> float:
    """
    Validate oxidizer-to-fuel mixture ratio [-].

    .. deprecated::
        Prefer ``physics.propulsion_validation.validate_mixture_ratio`` for
        new propulsion-domain code. This Core wrapper is retained for
        backward compatibility and does **not** import Physics.
    """

    return validate_positive(value, "mixture_ratio")


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
    Validate nozzle expansion ratio [-].

    .. deprecated::
        Prefer ``physics.propulsion_validation.validate_expansion_ratio`` for
        new propulsion-domain code. This Core wrapper is retained for
        backward compatibility and does **not** import Physics.
    """

    return validate_positive(value, "expansion_ratio")