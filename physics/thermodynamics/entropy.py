"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.entropy
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Entropy change of a calorically perfect ideal gas.
"""

from __future__ import annotations

from core.quantity import Quantity

from physics.model import ModelIdentity
from physics.thermodynamics.ideal_gas import specific_entropy_change

__all__ = ("IDEAL_GAS_ENTROPY", "ideal_gas_change")

IDEAL_GAS_ENTROPY = ModelIdentity(
    model_id="PHYS-001.entropy.ideal_gas",
    model_name="Ideal-gas entropy change",
    physical_domain="thermodynamics",
    equations=("s2 - s1 = Cp * ln(T2/T1) - R * ln(p2/p1)",),
    inputs=(
        "T1 [K]",
        "T2 [K]",
        "p1 [Pa]",
        "p2 [Pa]",
        "gamma [-]",
        "molar_mass [kg/mol]",
    ),
    outputs=("delta_s [J/(kg K)]",),
    assumptions=("Calorically perfect ideal gas; reversible or irreversible Δs formula.",),
    validity_range="T > 0 K; p > 0 Pa",
    source="Cengel & Boles; Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: isentropic process Δs = 0",
    limitations=("Absolute entropy requires a reference such as NASA polynomials.",),
)


def ideal_gas_change(
    temperature_1: Quantity,
    temperature_2: Quantity,
    pressure_1: Quantity,
    pressure_2: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Return s2 - s1 for a calorically perfect ideal gas."""

    return specific_entropy_change(
        temperature_1,
        temperature_2,
        pressure_1,
        pressure_2,
        gamma,
        molar_mass,
    )
