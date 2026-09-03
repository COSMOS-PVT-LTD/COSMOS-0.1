"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.viscosity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Dynamic viscosity evaluation (Sutherland or sourced record).
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record
from physics.fluids.sutherland import SutherlandEvaluation, SutherlandLaw, evaluate_sutherland

__all__ = ("sutherland", "from_record")


def sutherland(
    law: SutherlandLaw,
    temperature: Quantity,
    *,
    allow_extrapolation: bool = False,
) -> SutherlandEvaluation:
    """Gas dynamic viscosity from a sourced Sutherland law."""

    return evaluate_sutherland(
        law,
        temperature,
        allow_extrapolation=allow_extrapolation,
    )


def from_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate a sourced liquid/reference viscosity record."""

    return evaluate_record(
        record,
        temperature,
        pressure,
        allow_extrapolation=allow_extrapolation,
    )
