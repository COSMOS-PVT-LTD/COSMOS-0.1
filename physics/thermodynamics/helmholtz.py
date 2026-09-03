"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.helmholtz
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Helmholtz function definition a = u - T s.
"""

from __future__ import annotations

from core.dimension import TEMPERATURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_ENERGY, SPECIFIC_HEAT, UNIT_SPECIFIC_ENERGY

__all__ = ("HELMHOLTZ", "specific_helmholtz")

HELMHOLTZ = ModelIdentity(
    model_id="PHYS-001.helmholtz.definition",
    model_name="Specific Helmholtz function",
    physical_domain="thermodynamics",
    equations=("a = u - T * s",),
    inputs=("internal_energy [J/kg]", "temperature [K]", "entropy [J/(kg K)]"),
    outputs=("helmholtz [J/kg]",),
    assumptions=("Equilibrium thermodynamic state.",),
    validity_range="T > 0 K",
    source="Cengel & Boles; Moran & Shapiro.",
    verification_status="software_verification: dimensional identity",
    limitations=("Requires a consistent internal-energy/entropy datum.",),
)


def specific_helmholtz(
    specific_internal_energy: Quantity,
    temperature: Quantity,
    specific_entropy: Quantity,
) -> Quantity:
    """Return a = u - T s."""

    u = as_si(specific_internal_energy, SPECIFIC_ENERGY, "specific_internal_energy")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    s = as_si(specific_entropy, SPECIFIC_HEAT, "specific_entropy")
    return quantity(u - t * s, UNIT_SPECIFIC_ENERGY)
