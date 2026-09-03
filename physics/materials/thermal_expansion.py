"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.thermal_expansion
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Linear thermal-expansion coefficient evaluation.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, evaluate_record
from physics.materials.catalog import MaterialRecord

__all__ = ("coefficient",)


def coefficient(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate α at ``temperature``."""

    return evaluate_record(
        material.thermal_expansion,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )
