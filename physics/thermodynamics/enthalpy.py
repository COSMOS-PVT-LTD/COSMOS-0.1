"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.enthalpy
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Enthalpy definition and calorically perfect evaluation.
"""

from __future__ import annotations

from core.dimension import PRESSURE, VOLUME
from core.quantity import Quantity
from core.unit import SI

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_ENERGY, UNIT_SPECIFIC_ENERGY
from physics.thermodynamics.ideal_gas import specific_enthalpy as ideal_specific_enthalpy

__all__ = (
    "ENTHALPY_DEFINITION",
    "from_internal_energy",
    "ideal_gas",
)

ENTHALPY_DEFINITION = ModelIdentity(
    model_id="PHYS-001.enthalpy.definition",
    model_name="Enthalpy definition",
    physical_domain="thermodynamics",
    equations=("H = U + p V", "h = u + p / rho"),
    inputs=("internal_energy [J]", "pressure [Pa]", "volume [m3]"),
    outputs=("enthalpy [J]",),
    assumptions=("Continuum thermodynamic state; equilibrium.",),
    validity_range="p finite; V > 0 for specific form via density.",
    source="Standard thermodynamic definition (Cengel & Boles).",
    verification_status="analytical_verification: ideal-gas h = u + R T",
    limitations=("Does not include formation enthalpy unless u does.",),
)


def from_internal_energy(
    internal_energy: Quantity,
    pressure: Quantity,
    volume: Quantity,
) -> Quantity:
    """Return H = U + p V."""

    from core.dimension import ENERGY

    u = as_si(internal_energy, ENERGY, "internal_energy")
    p = as_si(pressure, PRESSURE, "pressure")
    v = as_si(volume, VOLUME, "volume")
    return quantity(u + p * v, SI.get("J"))


def specific_from_internal_energy(
    specific_internal_energy: Quantity,
    pressure: Quantity,
    density: Quantity,
) -> Quantity:
    """Return h = u + p/ρ."""

    from core.dimension import DENSITY
    from core.validation import validate_positive

    u = as_si(specific_internal_energy, SPECIFIC_ENERGY, "specific_internal_energy")
    p = as_si(pressure, PRESSURE, "pressure")
    rho = validate_positive(as_si(density, DENSITY, "density"), "density")
    return quantity(u + p / rho, UNIT_SPECIFIC_ENERGY)


def ideal_gas(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
    *,
    reference_temperature: Quantity | None = None,
    reference_enthalpy: Quantity | None = None,
) -> Quantity:
    """Calorically perfect specific enthalpy."""

    return ideal_specific_enthalpy(
        temperature,
        gamma,
        molar_mass,
        reference_temperature=reference_temperature,
        reference_enthalpy=reference_enthalpy,
    )
