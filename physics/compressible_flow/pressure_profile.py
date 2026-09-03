"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.pressure_profile
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Isentropic nozzle pressure from a sequence of area ratios.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.compressible_flow.nozzle_1d import NozzleStation, station_from_area_ratio

__all__ = ("isentropic_pressure_profile",)


def isentropic_pressure_profile(
    area_ratios: tuple[float, ...],
    stagnation_pressure: Quantity,
    stagnation_temperature: Quantity,
    gamma: float,
    molar_mass: Quantity,
    *,
    branch: str = "supersonic",
) -> tuple[NozzleStation, ...]:
    """
    Return isentropic stations for a monotonic area-ratio schedule.

    Geometry generation (CAD) is out of scope.
    """

    return tuple(
        station_from_area_ratio(
            area_ratio,
            stagnation_pressure,
            stagnation_temperature,
            gamma,
            molar_mass,
            branch=branch,
        )
        for area_ratio in area_ratios
    )
