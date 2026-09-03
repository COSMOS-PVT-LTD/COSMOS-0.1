"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.plasticity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: von Mises yield check (onset of plasticity).
"""

from __future__ import annotations

from core.dimension import PRESSURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si
from physics.solid_mechanics.stress import von_mises

__all__ = ("YIELD_CHECK", "has_yielded")

YIELD_CHECK = ModelIdentity(
    model_id="PHYS-007.plasticity.von_mises_onset",
    model_name="von Mises yield onset",
    physical_domain="solid_mechanics",
    equations=("yielded if sigma_vm >= Sy",),
    inputs=("principal stresses [Pa]", "Sy [Pa]"),
    outputs=("boolean",),
    assumptions=("Isotropic von Mises criterion; rate-independent.",),
    validity_range="Sy > 0",
    source="Shigley (distortion-energy / von Mises criterion).",
    verification_status="analytical_verification: uniaxial yield at Sy",
    limitations=("Not a plastic-flow integration scheme.",),
)


def has_yielded(
    sigma_1: float,
    sigma_2: float,
    sigma_3: float,
    yield_strength: Quantity,
) -> bool:
    """Return True when von Mises stress reaches Sy."""

    sy = validate_positive(as_si(yield_strength, PRESSURE, "Sy"), "Sy")
    vm = von_mises(sigma_1, sigma_2, sigma_3).to_si()
    return vm >= sy
