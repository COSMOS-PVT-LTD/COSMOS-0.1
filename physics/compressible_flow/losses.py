"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.losses
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Explicit nozzle loss factors (not hidden inside performance functions).

Description:
    Discharge coefficient:
        Cd = mdot_actual / mdot_ideal
    Kinetic-energy efficiency:
        η_ke = V_actual^2 / V_ideal^2
    Thrust efficiency:
        η_F = F_actual / F_ideal

    These are definitions. Values must be supplied from test or a sourced
    correlation; they are not invented here.
"""

from __future__ import annotations

from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_efficiency, validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity

__all__ = (
    "DISCHARGE_COEFFICIENT",
    "apply_discharge_coefficient",
    "apply_kinetic_energy_efficiency",
)

DISCHARGE_COEFFICIENT = ModelIdentity(
    model_id="PHYS-004.losses.discharge_coefficient",
    model_name="Nozzle discharge coefficient",
    physical_domain="compressible_flow",
    equations=("mdot_actual = Cd * mdot_ideal",),
    inputs=("mdot_ideal [kg/s]", "Cd [-]"),
    outputs=("mdot_actual [kg/s]",),
    assumptions=("Cd is an empirical factor, not a derived gasdynamic identity.",),
    validity_range="0 < Cd <= 1",
    source="Sutton & Biblarz; Huzel & Huang, NASA SP-125 (definition).",
    verification_status="software_verification: Cd=1 identity",
    limitations=("Does not predict Cd from geometry.",),
)


def apply_discharge_coefficient(ideal_mass_flow: Quantity, discharge_coefficient: float) -> Quantity:
    """Return ṁ_actual = Cd ṁ_ideal."""

    cd = validate_efficiency(discharge_coefficient)
    if cd <= 0.0:
        raise InvalidInputError("discharge coefficient must be in (0, 1].")
    mdot = validate_positive(
        as_si(ideal_mass_flow, SI.get("kg/s").dimension, "ideal_mass_flow"),
        "ideal_mass_flow",
    )
    return quantity(cd * mdot, SI.get("kg/s"))


def apply_kinetic_energy_efficiency(ideal_velocity: Quantity, efficiency: float) -> Quantity:
    """Return V_actual = V_ideal * sqrt(η_ke)."""

    from core.dimension import VELOCITY

    eta = validate_efficiency(efficiency)
    if eta <= 0.0:
        raise InvalidInputError("kinetic-energy efficiency must be in (0, 1].")
    vel = as_si(ideal_velocity, VELOCITY, "ideal_velocity")
    if vel < 0.0:
        raise InvalidInputError("ideal velocity must be non-negative.")
    return quantity(vel * (eta ** 0.5), SI.get("m/s"))
