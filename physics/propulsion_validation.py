"""
Propulsion-domain validation helpers.

These validators were relocated from ``core.validation`` because mixture
ratio and nozzle expansion ratio are rocket-propulsion concepts, not
domain-independent Core primitives.
"""

from __future__ import annotations

from core.validation import validate_positive

__all__ = (
    "validate_expansion_ratio",
    "validate_mixture_ratio",
)


def validate_mixture_ratio(value: float) -> float:
    """Validate oxidizer-to-fuel mixture ratio [-]."""

    return validate_positive(value, "mixture_ratio")


def validate_expansion_ratio(value: float) -> float:
    """Validate nozzle expansion ratio [-]."""

    return validate_positive(value, "expansion_ratio")
