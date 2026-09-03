"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.methane
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Methane identity and sourced NBP liquid density.
"""

from __future__ import annotations

from physics.fluids.records import LCH4_NBP_DENSITY
from physics.fluids.sutherland import METHANE_SUTHERLAND
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS", "GAS_GAMMA", "NBP_DENSITY", "SUTHERLAND")

FLUID_ID = "methane"
MOLAR_MASS = molar_mass_from_kg_per_kmol(16.0425)
GAS_GAMMA = 1.32  # typical calorically perfect CH4 near 300 K
NBP_DENSITY = LCH4_NBP_DENSITY
SUTHERLAND = METHANE_SUTHERLAND
NBP_TEMPERATURE_K = 111.67
SOURCE = (
    "CH4 molar mass: NIST Chemistry WebBook. "
    "Liquid NBP density: NIST Chemistry WebBook. "
    "Gas gamma is a calorically perfect modelling value near 300 K."
)
