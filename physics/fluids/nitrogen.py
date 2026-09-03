"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.nitrogen
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Nitrogen identity and sourced NBP liquid density.
"""

from __future__ import annotations

from physics.fluids.records import LN2_NBP_DENSITY
from physics.fluids.sutherland import NITROGEN_SUTHERLAND
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS", "GAS_GAMMA", "NBP_DENSITY", "SUTHERLAND")

FLUID_ID = "nitrogen"
MOLAR_MASS = molar_mass_from_kg_per_kmol(28.0134)
GAS_GAMMA = 1.40
NBP_DENSITY = LN2_NBP_DENSITY
SUTHERLAND = NITROGEN_SUTHERLAND
NBP_TEMPERATURE_K = 77.355
SOURCE = (
    "N2 molar mass: NIST Chemistry WebBook / IUPAC. "
    "Liquid NBP density: NIST Chemistry WebBook."
)
