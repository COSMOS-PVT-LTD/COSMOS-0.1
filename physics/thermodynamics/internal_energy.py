"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.internal_energy
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Internal energy definition and calorically perfect evaluation.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.model import ModelIdentity
from physics.thermodynamics.ideal_gas import (
    specific_internal_energy as ideal_specific_internal_energy,
)

__all__ = ("INTERNAL_ENERGY", "ideal_gas")

INTERNAL_ENERGY = ModelIdentity(
    model_id="PHYS-001.internal_energy.ideal_gas",
    model_name="Calorically perfect internal energy",
    physical_domain="thermodynamics",
    equations=("u - uref = Cv * (T - Tref)", "u = h - p / rho"),
    inputs=("temperature [K]", "gamma [-]", "molar_mass [kg/mol]"),
    outputs=("specific_internal_energy [J/kg]",),
    assumptions=("Calorically perfect ideal gas.",),
    validity_range="T > 0 K; 1 < gamma <= 3",
    source="Cengel & Boles; Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: h - u = R T for ideal gas",
    limitations=("Datum u(0 K)=0 is a modelling choice, not formation energy.",),
)


def ideal_gas(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
    *,
    reference_temperature: Quantity | None = None,
    reference_internal_energy: Quantity | None = None,
) -> Quantity:
    """Calorically perfect specific internal energy."""

    return ideal_specific_internal_energy(
        temperature,
        gamma,
        molar_mass,
        reference_temperature=reference_temperature,
        reference_internal_energy=reference_internal_energy,
    )
