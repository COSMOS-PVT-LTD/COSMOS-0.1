"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.equilibrium
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Equilibrium-composition interface (external-engine owned).
"""

from __future__ import annotations

from physics.thermochemistry.cea_interface import (
    CeaRequest,
    ThermochemicalResult,
    ThermochemistryEngine,
    run_thermochemistry,
)

__all__ = ("evaluate_equilibrium",)


def evaluate_equilibrium(
    request: CeaRequest,
    engine: ThermochemistryEngine | None = None,
) -> ThermochemicalResult:
    """Evaluate chemical equilibrium via the external engine boundary."""

    equilibrium_request = CeaRequest(
        fuel_id=request.fuel_id,
        oxidizer_id=request.oxidizer_id,
        mixture_ratio=request.mixture_ratio,
        chamber_pressure=request.chamber_pressure,
        equilibrium=True,
        notes=request.notes,
    )
    return run_thermochemistry(equilibrium_request, engine)
