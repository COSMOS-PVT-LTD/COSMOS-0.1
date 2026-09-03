"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.gibbs
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Gibbs function definition g = h - T s.
"""

from __future__ import annotations

from core.dimension import TEMPERATURE
from core.quantity import Quantity

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_ENERGY, SPECIFIC_HEAT, UNIT_SPECIFIC_ENERGY

__all__ = ("GIBBS", "specific_gibbs")

GIBBS = ModelIdentity(
    model_id="PHYS-001.gibbs.definition",
    model_name="Specific Gibbs function",
    physical_domain="thermodynamics",
    equations=("g = h - T * s",),
    inputs=("enthalpy [J/kg]", "temperature [K]", "entropy [J/(kg K)]"),
    outputs=("gibbs [J/kg]",),
    assumptions=("Equilibrium thermodynamic state.",),
    validity_range="T > 0 K",
    source="Cengel & Boles; Moran & Shapiro.",
    verification_status="software_verification: dimensional identity",
    limitations=("Requires a consistent enthalpy/entropy datum.",),
)


def specific_gibbs(
    specific_enthalpy: Quantity,
    temperature: Quantity,
    specific_entropy: Quantity,
) -> Quantity:
    """Return g = h - T s."""

    from core.validation import validate_positive

    h = as_si(specific_enthalpy, SPECIFIC_ENERGY, "specific_enthalpy")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    s = as_si(specific_entropy, SPECIFIC_HEAT, "specific_entropy")
    return quantity(h - t * s, UNIT_SPECIFIC_ENERGY)
