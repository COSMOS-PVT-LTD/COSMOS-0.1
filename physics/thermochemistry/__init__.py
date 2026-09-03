"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thermochemistry foundation public surface (PHYS-003).
"""

from __future__ import annotations

from physics.thermochemistry.cea_interface import (
    CeaRequest,
    ThermochemicalResult,
    ThermochemistryEngine,
    run_thermochemistry,
)
from physics.thermochemistry.mixtures import Mixture, from_mass_fractions, from_mole_fractions
from physics.thermochemistry.nasa_polynomials import evaluate_nasa7
from physics.thermochemistry.species import Species, get_species, list_species

__all__ = (
    "CeaRequest",
    "Mixture",
    "Species",
    "ThermochemicalResult",
    "ThermochemistryEngine",
    "evaluate_nasa7",
    "from_mass_fractions",
    "from_mole_fractions",
    "get_species",
    "list_species",
    "run_thermochemistry",
)
