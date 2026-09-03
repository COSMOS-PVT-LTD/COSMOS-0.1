"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Heat-transfer foundation public surface (PHYS-005).
"""

from __future__ import annotations

from physics.heat_transfer.bartz import BartzEvaluation, bartz_heat_transfer_coefficient
from physics.heat_transfer.conduction import plane_wall_heat_rate
from physics.heat_transfer.convection import newtons_law
from physics.heat_transfer.heat_flux import convective_heat_flux
from physics.heat_transfer.radiation import net_heat_rate
from physics.heat_transfer.recovery_temperature import adiabatic_wall_temperature

__all__ = (
    "BartzEvaluation",
    "adiabatic_wall_temperature",
    "bartz_heat_transfer_coefficient",
    "convective_heat_flux",
    "net_heat_rate",
    "newtons_law",
    "plane_wall_heat_rate",
)
