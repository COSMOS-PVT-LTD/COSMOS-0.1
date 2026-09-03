"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.compressibility
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fluid compressibility factor Z = p / (ρ R T).
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.thermodynamics.equations_of_state import compressibility_factor as eos_z

__all__ = ("factor",)


def factor(
    pressure: Quantity,
    density: Quantity,
    temperature: Quantity,
    specific_gas_constant: Quantity,
) -> float:
    """Return Z = p / (ρ R T)."""

    return eos_z(pressure, density, temperature, specific_gas_constant)
