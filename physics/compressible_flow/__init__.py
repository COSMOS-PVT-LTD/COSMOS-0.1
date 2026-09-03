"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Compressible-flow foundation public surface (PHYS-004).
"""

from __future__ import annotations

from physics.compressible_flow.area_mach import area_ratio, mach_from_area_ratio
from physics.compressible_flow.choked_flow import choked_mass_flow, is_choked
from physics.compressible_flow.expansion_fan import expanded_mach, prandtl_meyer
from physics.compressible_flow.isentropic import (
    mach_from_pressure_ratio,
    stagnation_pressure_ratio,
    stagnation_temperature_ratio,
)
from physics.compressible_flow.nozzle_1d import NozzleStation, station_from_area_ratio
from physics.compressible_flow.normal_shock import NormalShockState, evaluate_normal_shock
from physics.compressible_flow.thrust_relations import ideal_thrust_coefficient, thrust

__all__ = (
    "NozzleStation",
    "NormalShockState",
    "area_ratio",
    "choked_mass_flow",
    "evaluate_normal_shock",
    "expanded_mach",
    "ideal_thrust_coefficient",
    "is_choked",
    "mach_from_area_ratio",
    "mach_from_pressure_ratio",
    "prandtl_meyer",
    "stagnation_pressure_ratio",
    "stagnation_temperature_ratio",
    "station_from_area_ratio",
    "thrust",
)
