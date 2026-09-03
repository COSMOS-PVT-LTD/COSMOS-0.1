"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.equations_of_state
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Equation-of-state identities and compressibility factor.

Description:
    Defines the thermal EOS family used by COSMOS:

        Z = p / (ρ R T)

    Z = 1 is the ideal-gas closure. Real-fluid closures belong to
    ``real_gas`` and require sourced coefficients.
"""

from __future__ import annotations

from core.dimension import DENSITY, PRESSURE, TEMPERATURE
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity
from physics.si import SPECIFIC_HEAT
from physics.thermodynamics.ideal_gas import density as ideal_density
from physics.thermodynamics.ideal_gas import specific_gas_constant

__all__ = (
    "COMPRESSIBILITY_IDENTITY",
    "compressibility_factor",
    "ideal_gas_pressure",
)

COMPRESSIBILITY_IDENTITY = ModelIdentity(
    model_id="PHYS-001.eos.compressibility",
    model_name="Thermal equation of state with compressibility factor",
    physical_domain="thermodynamics",
    equations=("Z = p / (rho * R * T)", "p = Z * rho * R * T"),
    inputs=("pressure [Pa]", "density [kg/m3]", "temperature [K]", "R [J/(kg K)]"),
    outputs=("Z [-]",),
    assumptions=("Single-phase continuum; R is the specific gas constant.",),
    validity_range="T > 0 K; p > 0 Pa; rho > 0 kg/m3",
    source="Standard thermal EOS identity (Cengel & Boles; Moran & Shapiro).",
    verification_status="analytical_verification: Z=1 recovers p=rho R T",
    limitations=("Z is a definition, not a predictive real-gas model.",),
)


def compressibility_factor(
    pressure: Quantity,
    density: Quantity,
    temperature: Quantity,
    specific_gas_constant_value: Quantity,
) -> float:
    """Return Z = p / (ρ R T)."""

    p = validate_positive(as_si(pressure, PRESSURE, "pressure"), "pressure")
    rho = validate_positive(as_si(density, DENSITY, "density"), "density")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    r = validate_positive(
        as_si(specific_gas_constant_value, SPECIFIC_HEAT, "R"),
        "specific_gas_constant",
    )
    return p / (rho * r * t)


def ideal_gas_pressure(
    temperature: Quantity,
    density: Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Ideal-gas pressure p = ρ R T (Z = 1)."""

    from physics.thermodynamics.ideal_gas import pressure as ideal_pressure

    return ideal_pressure(density, temperature, molar_mass)


def density_ideal(
    pressure: Quantity,
    temperature: Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Ideal-gas density."""

    return ideal_density(pressure, temperature, molar_mass)


def specific_gas_constant_from_molar_mass(molar_mass: Quantity) -> Quantity:
    """R = R_univ / M."""

    return specific_gas_constant(molar_mass)


def pressure_from_z(
    compressibility: float,
    density: Quantity,
    temperature: Quantity,
    specific_gas_constant_value: Quantity,
) -> Quantity:
    """Return p = Z ρ R T."""

    if compressibility <= 0.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("compressibility Z must be positive.")
    rho = validate_positive(as_si(density, DENSITY, "density"), "density")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    r = validate_positive(
        as_si(specific_gas_constant_value, SPECIFIC_HEAT, "R"),
        "specific_gas_constant",
    )
    return quantity(compressibility * rho * r * t, SI.get("Pa"))
