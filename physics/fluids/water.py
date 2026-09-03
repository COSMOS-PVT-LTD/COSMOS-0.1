"""
COSMOS Rocket Propulsion Platform

Module: physics.fluids.water
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Water identity and Incropera 300 K liquid properties.
"""

from __future__ import annotations

from physics.fluids.records import (
    WATER_300K_CONDUCTIVITY,
    WATER_300K_CP,
    WATER_300K_DENSITY,
    WATER_300K_SURFACE_TENSION,
    WATER_300K_VISCOSITY,
    WATER_NBP_VAPOR_PRESSURE,
)
from physics.thermodynamics.ideal_gas import molar_mass_from_kg_per_kmol

__all__ = (
    "FLUID_ID",
    "MOLAR_MASS",
    "DENSITY_300K",
    "VISCOSITY_300K",
    "CONDUCTIVITY_300K",
    "CP_300K",
    "SURFACE_TENSION_300K",
    "NBP_VAPOR_PRESSURE",
)

FLUID_ID = "water"
MOLAR_MASS = molar_mass_from_kg_per_kmol(18.01528)
DENSITY_300K = WATER_300K_DENSITY
VISCOSITY_300K = WATER_300K_VISCOSITY
CONDUCTIVITY_300K = WATER_300K_CONDUCTIVITY
CP_300K = WATER_300K_CP
SURFACE_TENSION_300K = WATER_300K_SURFACE_TENSION
NBP_VAPOR_PRESSURE = WATER_NBP_VAPOR_PRESSURE
SOURCE = "Incropera et al., Fundamentals of Heat and Mass Transfer, Table A.6; water NBP definition."
