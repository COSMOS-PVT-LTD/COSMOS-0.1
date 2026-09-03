"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.conductivity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thermal conductivity from sourced records only.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record

__all__ = ("from_record",)


def from_record(
    record: PropertyRecord,
    temperature: Quantity,
    pressure: Quantity | None = None,
    *,
    allow_extrapolation: bool = False,
) -> PropertyEvaluation:
    """Evaluate sourced thermal conductivity. No unsourced correlation."""

    return evaluate_record(
        record,
        temperature,
        pressure,
        allow_extrapolation=allow_extrapolation,
    )
