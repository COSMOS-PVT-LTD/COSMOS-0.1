"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.safety_factor
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Physical ratio n = allowable / actual.

Description:
    This is a definition, not a design code. Chamber structural design
    methodology belongs to engineering/structure.
"""

from __future__ import annotations

from core.exceptions import InvalidInputError

from physics.model import ModelIdentity

__all__ = ("SAFETY_FACTOR", "ratio")

SAFETY_FACTOR = ModelIdentity(
    model_id="PHYS-007.safety_factor.ratio",
    model_name="Allowable-to-actual ratio",
    physical_domain="solid_mechanics",
    equations=("n = allowable / actual",),
    inputs=("allowable [consistent]", "actual [consistent]"),
    outputs=("n [-]",),
    assumptions=("Same dimension for allowable and actual.",),
    validity_range="actual != 0",
    source="Shigley (definition of factor of safety).",
    verification_status="software_verification: n=1 when equal",
    limitations=("Not ASME, not a required-thickness calculation.",),
)


def ratio(allowable: float, actual: float) -> float:
    """Return n = allowable / actual."""

    if actual == 0.0:
        raise InvalidInputError("actual value is zero; safety factor is undefined.")
    return allowable / actual
