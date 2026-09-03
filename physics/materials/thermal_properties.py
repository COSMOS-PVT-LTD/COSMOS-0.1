"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.thermal_properties
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Temperature-windowed thermal property evaluation.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, evaluate_record
from physics.materials.catalog import MaterialRecord

__all__ = ("conductivity", "specific_heat")


def conductivity(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate thermal conductivity at ``temperature``."""

    return evaluate_record(
        material.conductivity,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )


def specific_heat(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate specific heat at ``temperature``."""

    return evaluate_record(
        material.specific_heat,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )
