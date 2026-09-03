"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.density
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Density evaluation routing (ideal gas or sourced liquid record).
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record
from physics.thermodynamics.ideal_gas import density as ideal_gas_density

__all__ = ("ideal_gas", "from_record")


def ideal_gas(
    pressure: Quantity,
    temperature: Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Ideal-gas density ρ = p / (R T)."""

    return ideal_gas_density(pressure, temperature, molar_mass)


def from_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate a sourced density record."""

    return evaluate_record(
        record,
        temperature,
        pressure,
        allow_extrapolation=allow_extrapolation,
    )
