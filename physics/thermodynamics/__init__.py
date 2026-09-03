"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Thermodynamics foundation public surface (PHYS-001).
"""

from __future__ import annotations

from physics.thermodynamics.enthalpy import from_internal_energy as enthalpy_from_u
from physics.thermodynamics.equations_of_state import compressibility_factor
from physics.thermodynamics.exergy import ideal_gas_flow_exergy
from physics.thermodynamics.first_law import closed_system_delta_u
from physics.thermodynamics.ideal_gas import (
    IdealGasState,
    cp_from_gamma,
    cv_from_gamma,
    density,
    evaluate_state,
    pressure,
    specific_enthalpy,
    specific_entropy_change,
    specific_gas_constant,
    specific_internal_energy,
    speed_of_sound,
)
from physics.thermodynamics.second_law import entropy_production_closed

__all__ = (
    "IdealGasState",
    "closed_system_delta_u",
    "compressibility_factor",
    "cp_from_gamma",
    "cv_from_gamma",
    "density",
    "enthalpy_from_u",
    "entropy_production_closed",
    "evaluate_state",
    "ideal_gas_flow_exergy",
    "pressure",
    "specific_enthalpy",
    "specific_entropy_change",
    "specific_gas_constant",
    "specific_internal_energy",
    "speed_of_sound",
)
