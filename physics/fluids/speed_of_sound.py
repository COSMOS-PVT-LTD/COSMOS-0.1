"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.speed_of_sound
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Speed-of-sound evaluation for ideal gases.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.thermodynamics.ideal_gas import speed_of_sound as ideal_gas_speed_of_sound

__all__ = ("ideal_gas",)


def ideal_gas(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Return a = sqrt(γ R T)."""

    return ideal_gas_speed_of_sound(temperature, gamma, molar_mass)
