"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.frozen
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Frozen-composition interface (external-engine owned).
"""

from __future__ import annotations

from physics.thermochemistry.cea_interface import (
    CeaRequest,
    ThermochemicalResult,
    ThermochemistryEngine,
    run_thermochemistry,
)

__all__ = ("evaluate_frozen",)


def evaluate_frozen(
    request: CeaRequest,
    engine: ThermochemistryEngine | None = None,
) -> ThermochemicalResult:
    """Evaluate frozen composition via the external engine boundary."""

    frozen_request = CeaRequest(
        fuel_id=request.fuel_id,
        oxidizer_id=request.oxidizer_id,
        mixture_ratio=request.mixture_ratio,
        chamber_pressure=request.chamber_pressure,
        equilibrium=False,
        notes=request.notes,
    )
    return run_thermochemistry(frozen_request, engine)
