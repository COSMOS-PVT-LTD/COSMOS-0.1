"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fluid-property foundation public surface (PHYS-002).
"""

from __future__ import annotations

from physics.fluids.fluid_properties import PropertyEvaluation, PropertyRecord, evaluate_record
from physics.fluids.mach import mach_number
from physics.fluids.prandtl import prandtl_number
from physics.fluids.reynolds import reynolds_number
from physics.fluids.sutherland import evaluate_sutherland

__all__ = (
    "PropertyEvaluation",
    "PropertyRecord",
    "evaluate_record",
    "evaluate_sutherland",
    "mach_number",
    "prandtl_number",
    "reynolds_number",
)
