"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.failure_criteria
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Compare equivalent stress to a sourced yield strength.
"""

from __future__ import annotations

from core.dimension import PRESSURE
from core.quantity import Quantity

from physics.exceptions import InsufficientDataError
from physics.materials.catalog import MaterialRecord
from physics.materials.elastic_properties import yield_strength
from physics.quantities import as_si

__all__ = ("yield_ratio",)


def yield_ratio(
    equivalent_stress: Quantity,
    material: MaterialRecord,
    temperature: Quantity,
) -> float:
    """
    Return σ_eq / Sy.

    This is a physical ratio, not an ASME design check.
    """

    if material.yield_strength is None:
        raise InsufficientDataError(
            f"{material.material_id} has no sourced yield strength."
        )
    sy = yield_strength(material, temperature).require_valid()
    sigma = as_si(equivalent_stress, PRESSURE, "equivalent_stress")
    return sigma / sy.to_si()
