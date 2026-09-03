"""
COSMOS Rocket Propulsion Platform

Module: physics.quantities
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Quantity construction and dimensional contracts for physics APIs.

Description:
    Physics public APIs consume Core ``Quantity`` objects. Internal
    evaluations use SI magnitudes after an explicit dimensional check.
"""

from __future__ import annotations

from core.dimension import Dimension
from core.exceptions import DimensionError, InvalidInputError
from core.quantity import Quantity
from core.unit import SI, Unit
from core.validation import validate_finite

__all__ = (
    "as_dimensionless",
    "as_si",
    "quantity",
    "require_gamma",
    "require_mach",
)


def quantity(magnitude: float, unit: Unit) -> Quantity:
    """Construct a Core quantity after confirming the magnitude is finite."""

    return Quantity(magnitude=validate_finite(magnitude, "magnitude"), unit=unit)


def as_si(value: Quantity, dimension: Dimension, name: str) -> float:
    """
    Return the SI magnitude of ``value`` after a dimension check.

    Raises
    ------
    DimensionError
        If ``value`` does not match ``dimension``.
    """

    if not value.dimension().is_compatible_with(dimension):
        raise DimensionError(
            f"{name} has incompatible dimension {value.dimension()!r}; "
            f"expected {dimension!r}."
        )
    return value.to_si()


def as_dimensionless(value: Quantity | float, name: str) -> float:
    """
    Return a finite dimensionless scalar.

    ``Quantity`` inputs must be dimensionless. Bare floats are accepted for
    inherently dimensionless relations (Mach, gamma, area ratio).
    """

    if isinstance(value, Quantity):
        if not value.is_dimensionless():
            raise DimensionError(
                f"{name} must be dimensionless. Received {value.dimension()!r}."
            )
        return validate_finite(value.to_si(), name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidInputError(f"{name} must be a real number.")
    return validate_finite(float(value), name)


def require_gamma(value: Quantity | float, name: str = "gamma") -> float:
    """
    Validate specific-heat ratio for calorically perfect gas relations.

    Core ``validate_gamma`` permits ``gamma == 1``, which is singular for
    isentropic and shock relations. Physics requires ``1 < gamma <= 3``.
    """

    gamma = as_dimensionless(value, name)
    if not 1.0 < gamma <= 3.0:
        raise InvalidInputError(
            f"{name} must satisfy 1 < gamma <= 3. Received {gamma}."
        )
    return gamma


def require_mach(
    value: Quantity | float,
    name: str = "mach",
    *,
    minimum: float = 0.0,
    exclusive_min: bool = False,
) -> float:
    """Validate a Mach number."""

    mach = as_dimensionless(value, name)
    if exclusive_min:
        if mach <= minimum:
            raise InvalidInputError(
                f"{name} must be greater than {minimum}. Received {mach}."
            )
    elif mach < minimum:
        raise InvalidInputError(
            f"{name} must be at least {minimum}. Received {mach}."
        )
    return mach


# Convenience constructors using the Core SI registry.
def kelvin(value: float) -> Quantity:
    """Temperature in kelvin."""

    return quantity(value, SI.get("K"))


def pascal(value: float) -> Quantity:
    """Pressure or stress in pascal."""

    return quantity(value, SI.get("Pa"))


def kilogram_per_cubic_metre(value: float) -> Quantity:
    """Density in kg/m^3."""

    return quantity(value, SI.get("kg/m3"))


def metre(value: float) -> Quantity:
    """Length in metre."""

    return quantity(value, SI.get("m"))


def metre_per_second(value: float) -> Quantity:
    """Velocity in m/s."""

    return quantity(value, SI.get("m/s"))


def watt(value: float) -> Quantity:
    """Power in watt."""

    return quantity(value, SI.get("W"))


def joule(value: float) -> Quantity:
    """Energy in joule."""

    return quantity(value, SI.get("J"))


def kilogram(value: float) -> Quantity:
    """Mass in kilogram."""

    return quantity(value, SI.get("kg"))


def second(value: float) -> Quantity:
    """Time in second."""

    return quantity(value, SI.get("s"))


def newton(value: float) -> Quantity:
    """Force in newton."""

    return quantity(value, SI.get("N"))


def square_metre(value: float) -> Quantity:
    """Area in m^2."""

    return quantity(value, SI.get("m2"))
