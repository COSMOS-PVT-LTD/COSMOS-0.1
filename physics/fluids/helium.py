"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.helium
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Helium identity, monatomic gamma, and NBP liquid density.
"""

from __future__ import annotations

from physics.fluids.records import LHE_NBP_DENSITY
from physics.fluids.sutherland import HELIUM_SUTHERLAND
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS", "GAS_GAMMA", "NBP_DENSITY", "SUTHERLAND")

FLUID_ID = "helium"
MOLAR_MASS = molar_mass_from_kg_per_kmol(4.0026)
GAS_GAMMA = 5.0 / 3.0  # monatomic ideal gas, kinetic theory
NBP_DENSITY = LHE_NBP_DENSITY
SUTHERLAND = HELIUM_SUTHERLAND
NBP_TEMPERATURE_K = 4.22
SOURCE = (
    "He molar mass: NIST Chemistry WebBook. "
    "gamma = 5/3 from monatomic kinetic theory. "
    "Liquid NBP density: NIST Chemistry WebBook, helium-4."
)
