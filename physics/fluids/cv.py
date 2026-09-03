"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.cv
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Specific-heat at constant volume.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record
from physics.thermodynamics.ideal_gas import cv_from_gamma

__all__ = ("ideal_gas", "from_record")


def ideal_gas(
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Calorically perfect Cv = R / (γ - 1)."""

    return cv_from_gamma(gamma, molar_mass)


def from_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate a sourced Cv record."""

    return evaluate_record(
        record,
        temperature,
        pressure,
        allow_extrapolation=allow_extrapolation,
    )
