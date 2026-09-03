"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.creep_models
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Creep interface without unsourced constants.
"""

from __future__ import annotations

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity

__all__ = ("CREEP", "norton_rate")

CREEP = ModelIdentity(
    model_id="PHYS-006.creep.norton_interface",
    model_name="Norton creep interface",
    physical_domain="materials",
    equations=("epsilon_dot = A * sigma^n * exp(-Q/(R T))",),
    inputs=("stress [Pa]", "T [K]", "A", "n", "Q"),
    outputs=("strain rate [1/s]",),
    assumptions=("Requires sourced A, n, Q for the alloy and condition.",),
    validity_range="Not executable without sourced constants.",
    source="OPEN SCIENTIFIC ISSUE: Norton constants are alloy-condition specific.",
    verification_status="interface_only",
    limitations=("Do not invent creep constants.",),
)


def norton_rate(*_args: object, **_kwargs: object) -> float:
    """Norton creep is not evaluated without sourced A, n, Q."""

    raise InsufficientDataError(
        "Norton creep constants are not sourced for COSMOS catalog materials. "
        "OPEN SCIENTIFIC ISSUE."
    )
