"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.cp
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Specific-heat evaluation (ideal-gas gamma path or sourced record).
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record
from physics.thermodynamics.ideal_gas import cp_from_gamma

__all__ = ("ideal_gas", "from_record")


def ideal_gas(
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Calorically perfect Cp = γ R / (γ - 1)."""

    return cp_from_gamma(gamma, molar_mass)


def from_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate a sourced Cp record."""

    return evaluate_record(
        record,
        temperature,
        pressure,
        allow_extrapolation=allow_extrapolation,
    )
