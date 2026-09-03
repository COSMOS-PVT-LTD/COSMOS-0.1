"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.strain
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Engineering strain definitions.
"""

from __future__ import annotations

from core.dimension import LENGTH
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity

__all__ = ("STRAIN", "engineering_strain")

STRAIN = ModelIdentity(
    model_id="PHYS-007.strain.engineering",
    model_name="Engineering strain",
    physical_domain="solid_mechanics",
    equations=("epsilon = Delta L / L0",),
    inputs=("delta_L [m]", "L0 [m]"),
    outputs=("epsilon [-]",),
    assumptions=("Small-deformation engineering strain.",),
    validity_range="L0 > 0",
    source="Shigley; continuum mechanics (engineering strain).",
    verification_status="analytical_verification: rigid-body ΔL=0 => ε=0",
    limitations=("Not Green-Lagrange strain.",),
)


def engineering_strain(delta_length: Quantity, original_length: Quantity) -> float:
    """Return ε = ΔL / L0."""

    dl = as_si(delta_length, LENGTH, "delta_length")
    l0 = validate_positive(as_si(original_length, LENGTH, "original_length"), "L0")
    if l0 == 0.0:
        raise InvalidInputError("original length must be positive.")
    return dl / l0


def as_quantity(strain: float) -> Quantity:
    """Wrap a strain as a dimensionless quantity."""

    return quantity(strain, SI.get("1"))
