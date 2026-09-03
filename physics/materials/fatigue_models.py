"""
COSMOS Rocket Propulsion Platform

Module: physics.materials.fatigue_models
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fatigue interface without unsourced S-N or Paris constants.
"""

from __future__ import annotations

from physics.exceptions import InsufficientDataError
from physics.model import ModelIdentity

__all__ = ("FATIGUE", "cycles_to_failure")

FATIGUE = ModelIdentity(
    model_id="PHYS-006.fatigue.interface",
    model_name="High-cycle fatigue interface",
    physical_domain="materials",
    equations=("S-N / Basquin / Paris relations require sourced constants",),
    inputs=("stress amplitude [Pa]",),
    outputs=("N_f [-]",),
    assumptions=("No universal fatigue constants.",),
    validity_range="Not executable without sourced S-N data.",
    source="OPEN SCIENTIFIC ISSUE: MMPDS/NASA fatigue datasets not ingested.",
    verification_status="interface_only",
    limitations=("Do not invent fatigue lives.",),
)


def cycles_to_failure(*_args: object, **_kwargs: object) -> float:
    """Fatigue life is not evaluated without sourced S-N data."""

    raise InsufficientDataError(
        "Fatigue S-N or Paris constants are not sourced. OPEN SCIENTIFIC ISSUE."
    )
