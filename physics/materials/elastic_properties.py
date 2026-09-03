"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.elastic_properties
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Temperature-windowed elastic property evaluation.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.exceptions import InsufficientDataError
from physics.fluids.fluid_properties import PropertyEvaluation, evaluate_record
from physics.materials.catalog import MaterialRecord

__all__ = ("youngs_modulus", "poisson_ratio", "yield_strength")


def youngs_modulus(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate Young's modulus at ``temperature``."""

    return evaluate_record(
        material.youngs_modulus,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )


def poisson_ratio(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate Poisson's ratio at ``temperature``."""

    return evaluate_record(
        material.poisson_ratio,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )


def yield_strength(
    material: MaterialRecord,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate yield strength when a sourced record exists."""

    if material.yield_strength is None:
        raise InsufficientDataError(
            f"{material.material_id} has no sourced yield strength."
        )
    return evaluate_record(
        material.yield_strength,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )
