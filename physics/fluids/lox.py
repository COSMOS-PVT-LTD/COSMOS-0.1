"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.lox
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Liquid-oxygen identity and sourced NBP density.
"""

from __future__ import annotations

from physics.fluids.records import LOX_NBP_DENSITY
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS", "GAS_GAMMA", "NBP_DENSITY")

FLUID_ID = "lox"
MOLAR_MASS = molar_mass_from_kg_per_kmol(31.9988)  # NIST / IUPAC O2
GAS_GAMMA = 1.40  # calorically perfect diatomic oxygen, room-temperature model
NBP_DENSITY = LOX_NBP_DENSITY
NBP_TEMPERATURE_K = 90.188
NBP_PRESSURE_PA = 101325.0
SOURCE = (
    "O2 molar mass: NIST Chemistry WebBook / IUPAC. "
    "Liquid NBP density: NIST Chemistry WebBook. "
    "Gas gamma=1.40 is a calorically perfect model, not a liquid property."
)
