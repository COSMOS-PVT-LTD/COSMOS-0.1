"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.rp1
Author: COSMOS Development Team
Version: 0.1.0
Purpose: RP-1 identity and typical ambient density.

Description:
    RP-1 is a kerosene blend. Density is blend-dependent. The catalog value
    is a typical engineering figure, not a unique specification property.
    A C12H26 formula is a common surrogate used in CEA, not a unique molecule.
"""

from __future__ import annotations

from physics.fluids.records import RP1_DENSITY
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = ("FLUID_ID", "MOLAR_MASS_SURROGATE", "AMBIENT_DENSITY")

FLUID_ID = "rp1"
# C12H26 surrogate molar mass (CEA-style), not a unique RP-1 molecule.
MOLAR_MASS_SURROGATE = molar_mass_from_kg_per_kmol(170.33)
AMBIENT_DENSITY = RP1_DENSITY
FORMULA_SURROGATE = "C12H26"
SOURCE = (
    "Typical density: Huzel & Huang, NASA SP-125 / MIL-DTL-25576 band. "
    "C12H26 is a thermochemical surrogate, not a unique chemical identity. "
    "OPEN SCIENTIFIC ISSUE: blend-specific RP-1 assays."
)
