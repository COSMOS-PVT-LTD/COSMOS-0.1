"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.mach
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Mach number M = V / a.
"""

from __future__ import annotations

from core.dimension import VELOCITY
from core.exceptions import InvalidInputError
from core.quantity import Quantity

from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.thermodynamics.ideal_gas import speed_of_sound as ideal_speed_of_sound

__all__ = ("MACH", "mach_number", "ideal_gas_speed_of_sound")

MACH = ModelIdentity(
    model_id="PHYS-002.dimensionless.mach",
    model_name="Mach number",
    physical_domain="fluids",
    equations=("M = V / a",),
    inputs=("V [m/s]", "a [m/s]"),
    outputs=("M [-]",),
    assumptions=("Local thermodynamic speed of sound.",),
    validity_range="a > 0; V >= 0",
    source="Anderson, Modern Compressible Flow.",
    verification_status="dimensional_analysis: M is dimensionless",
    limitations=("Does not imply isentropic or frozen chemistry.",),
)


def mach_number(velocity: Quantity, speed_of_sound: Quantity) -> float:
    """Return M = V / a."""

    vel = as_si(velocity, VELOCITY, "velocity")
    a = as_si(speed_of_sound, VELOCITY, "speed_of_sound")
    if a <= 0.0:
        raise InvalidInputError("speed of sound must be positive.")
    if vel < 0.0:
        raise InvalidInputError("velocity must be non-negative.")
    return vel / a


def ideal_gas_speed_of_sound(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Ideal-gas speed of sound a = sqrt(γ R T)."""

    return ideal_speed_of_sound(temperature, gamma, molar_mass)
