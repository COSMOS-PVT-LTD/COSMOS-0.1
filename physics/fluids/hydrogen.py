"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.hydrogen
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Hydrogen identity and sourced NBP liquid density.
"""

from __future__ import annotations

from physics.fluids.records import LH2_NBP_DENSITY
from physics.fluids.sutherland import HYDROGEN_SUTHERLAND
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS", "GAS_GAMMA", "NBP_DENSITY", "SUTHERLAND")

FLUID_ID = "hydrogen"
MOLAR_MASS = molar_mass_from_kg_per_kmol(2.01588)
GAS_GAMMA = 1.41  # typical calorically perfect H2 near 300 K
NBP_DENSITY = LH2_NBP_DENSITY
SUTHERLAND = HYDROGEN_SUTHERLAND
NBP_TEMPERATURE_K = 20.369
SOURCE = (
    "H2 molar mass: NIST Chemistry WebBook. "
    "Liquid NBP density: NIST Chemistry WebBook (parahydrogen). "
    "Ortho/para composition is an OPEN SCIENTIFIC ISSUE for detailed cryogenic work."
)
