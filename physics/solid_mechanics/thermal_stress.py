"""
COSMOS Rocket Propulsion Platform

Module: physics.solid_mechanics.thermal_stress
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fully constrained thermal stress σ = E α ΔT.
"""

from __future__ import annotations

from core.dimension import PRESSURE, TEMPERATURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import THERMAL_EXPANSION, UNIT_STRESS

__all__ = ("THERMAL_STRESS", "constrained_bar")

THERMAL_STRESS = ModelIdentity(
    model_id="PHYS-007.thermal.constrained_bar",
    model_name="Fully constrained thermal stress",
    physical_domain="solid_mechanics",
    equations=("sigma = E * alpha * Delta T",),
    inputs=("E [Pa]", "alpha [1/K]", "Delta T [K]"),
    outputs=("sigma [Pa]",),
    assumptions=("Fully constrained uniaxial bar; constant E and alpha.",),
    validity_range="E > 0",
    source="Shigley; Incropera (thermal strain ε_th = α ΔT).",
    verification_status="analytical_verification: ΔT=0 => σ=0",
    limitations=("Not a thermoelastic FEM.",),
)


def constrained_bar(
    youngs_modulus: Quantity,
    expansion_coefficient: Quantity,
    delta_temperature: Quantity,
) -> Quantity:
    """Return σ = E α ΔT for a fully constrained bar."""

    e = validate_positive(as_si(youngs_modulus, PRESSURE, "E"), "E")
    alpha = as_si(expansion_coefficient, THERMAL_EXPANSION, "alpha")
    dt = as_si(delta_temperature, TEMPERATURE, "delta_temperature")
    return quantity(e * alpha * dt, UNIT_STRESS)
