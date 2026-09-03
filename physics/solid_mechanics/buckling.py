"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.buckling
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Euler buckling load for a slender column.
"""

from __future__ import annotations

from core.constants import PI
from core.dimension import LENGTH, PRESSURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive, validate_range

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity

__all__ = ("EULER", "euler_load")

EULER = ModelIdentity(
    model_id="PHYS-007.buckling.euler",
    model_name="Euler buckling load",
    physical_domain="solid_mechanics",
    equations=("P_cr = pi^2 E I / (K L)^2",),
    inputs=("E [Pa]", "I [m4]", "L [m]", "K [-]"),
    outputs=("P_cr [N]",),
    assumptions=("Slender, initially straight, linearly elastic column.",),
    validity_range="E > 0; I > 0; L > 0; K > 0",
    source="Shigley, Mechanical Engineering Design (Euler column).",
    verification_status="analytical_verification: dimensions; pinned-pinned K=1",
    limitations=("Not a nonlinear collapse analysis; not valid for short columns.",),
)


def euler_load(
    youngs_modulus: Quantity,
    area_moment: Quantity,
    length: Quantity,
    effective_length_factor: float = 1.0,
) -> Quantity:
    """Return P_cr = π² E I / (K L)²."""

    e = validate_positive(as_si(youngs_modulus, PRESSURE, "E"), "E")
    inertia = validate_positive(
        as_si(area_moment, LENGTH**4, "area_moment"),
        "I",
    )
    length_si = validate_positive(as_si(length, LENGTH, "length"), "L")
    k = validate_range(effective_length_factor, 0.5, 2.1, "K")
    if k <= 0.0:
        raise InvalidInputError("effective length factor must be positive.")
    p_cr = (PI**2) * e * inertia / (k * length_si) ** 2
    return quantity(p_cr, SI.get("N"))
