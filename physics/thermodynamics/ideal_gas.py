"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.ideal_gas
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Calorically perfect ideal-gas relations.

Description:
    Authoritative ideal-gas state and calorically perfect property relations
    used by compressible-flow and thermochemistry consumers.

    Equation of state (specific form):
        p = ρ R T
    where R = R_univ / M  (J/(kg K)).

    Calorically perfect:
        γ = Cp / Cv
        Cp - Cv = R
        a = sqrt(γ R T)
        h - href = Cp (T - Tref)
        u - uref = Cv (T - Tref)

Sources
-------
    Cengel, Y. A., and Boles, M. A., Thermodynamics: An Engineering
    Approach (ideal-gas chapter).
    Anderson, J. D., Modern Compressible Flow (calorically perfect gas).
    CODATA 2022 via ``core.constants.UNIVERSAL_GAS_CONSTANT``.

Assumptions
-----------
    Ideal gas; calorically perfect (constant Cp, Cv, gamma);
    equilibrium; no condensation; T > 0, p > 0, ρ > 0, M > 0.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.constants import UNIVERSAL_GAS_CONSTANT
from core.dimension import DENSITY, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_dimensionless, as_si, quantity, require_gamma
from physics.si import (
    MOLAR_MASS,
    SPECIFIC_ENERGY,
    SPECIFIC_HEAT,
    UNIT_MOLAR_MASS,
    UNIT_SPECIFIC_ENERGY,
    UNIT_SPECIFIC_HEAT,
)
from physics.validity import ValidityStatus

__all__ = (
    "IDEAL_GAS_EOS",
    "IdealGasState",
    "density",
    "pressure",
    "temperature_from_pressure_density",
    "specific_gas_constant",
    "cp_from_gamma",
    "cv_from_gamma",
    "gamma_from_specific_heats",
    "speed_of_sound",
    "specific_enthalpy",
    "specific_internal_energy",
    "specific_entropy_change",
)

IDEAL_GAS_EOS = ModelIdentity(
    model_id="PHYS-001.ideal_gas.eos",
    model_name="Calorically perfect ideal gas",
    physical_domain="thermodynamics",
    equations=(
        "p = rho * R * T",
        "R = R_univ / M",
        "Cp - Cv = R",
        "gamma = Cp / Cv",
        "a = sqrt(gamma * R * T)",
        "h - href = Cp * (T - Tref)",
        "u - uref = Cv * (T - Tref)",
        "s2 - s1 = Cp * ln(T2/T1) - R * ln(p2/p1)",
    ),
    inputs=(
        "pressure [Pa]",
        "temperature [K]",
        "molar_mass [kg/mol]",
        "gamma [-]",
    ),
    outputs=(
        "density [kg/m3]",
        "specific_gas_constant [J/(kg K)]",
        "speed_of_sound [m/s]",
        "enthalpy [J/kg]",
        "internal_energy [J/kg]",
    ),
    assumptions=(
        "Ideal-gas equation of state.",
        "Calorically perfect (constant specific heats).",
        "Single-phase gas; no condensation.",
        "Thermal equilibrium.",
    ),
    validity_range="T > 0 K; p > 0 Pa; 1 < gamma <= 3; M > 0 kg/mol",
    required_properties=("molar_mass", "gamma"),
    source=(
        "Anderson, Modern Compressible Flow; Cengel & Boles, "
        "Thermodynamics; CODATA 2022 R_univ."
    ),
    verification_status=(
        "analytical_verification: EOS identity, Cp-Cv=R, isentropic "
        "entropy change, sonic speed dimensions"
    ),
    limitations=(
        "Not a real-fluid EOS.",
        "Not valid near saturation or at supercritical densities "
        "without a compressibility correction.",
        "Constant-gamma model is not a substitute for NASA polynomials "
        "over wide temperature ranges.",
    ),
)


@dataclass(frozen=True, slots=True)
class IdealGasState:
    """Complete calorically perfect ideal-gas thermodynamic state in SI."""

    pressure: Quantity
    temperature: Quantity
    density: Quantity
    specific_gas_constant: Quantity
    gamma: float
    molar_mass: Quantity
    speed_of_sound: Quantity
    validity: ValidityStatus
    identity: ModelIdentity = IDEAL_GAS_EOS


def specific_gas_constant(molar_mass: Quantity) -> Quantity:
    """
    Return R = R_univ / M.

    Parameters
    ----------
    molar_mass:
        Molar mass [kg/mol].
    """

    mass = validate_positive(as_si(molar_mass, MOLAR_MASS, "molar_mass"), "molar_mass")
    return quantity(UNIVERSAL_GAS_CONSTANT / mass, UNIT_SPECIFIC_HEAT)


def density(pressure: Quantity, temperature: Quantity, molar_mass: Quantity) -> Quantity:
    """Return ρ = p / (R T)."""

    p = validate_positive(as_si(pressure, PRESSURE, "pressure"), "pressure")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(p / (r * t), SI.get("kg/m3"))


def pressure(density_value: Quantity, temperature: Quantity, molar_mass: Quantity) -> Quantity:
    """Return p = ρ R T."""

    rho = validate_positive(as_si(density_value, DENSITY, "density"), "density")
    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(rho * r * t, SI.get("Pa"))


def temperature_from_pressure_density(
    pressure_value: Quantity,
    density_value: Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Return T = p / (ρ R)."""

    p = validate_positive(as_si(pressure_value, PRESSURE, "pressure"), "pressure")
    rho = validate_positive(as_si(density_value, DENSITY, "density"), "density")
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(p / (rho * r), SI.get("K"))


def cv_from_gamma(gamma: float | Quantity, molar_mass: Quantity) -> Quantity:
    """Return Cv = R / (γ - 1)."""

    g = require_gamma(gamma)
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(r / (g - 1.0), UNIT_SPECIFIC_HEAT)


def cp_from_gamma(gamma: float | Quantity, molar_mass: Quantity) -> Quantity:
    """Return Cp = γ R / (γ - 1)."""

    g = require_gamma(gamma)
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(g * r / (g - 1.0), UNIT_SPECIFIC_HEAT)


def gamma_from_specific_heats(cp: Quantity, cv: Quantity) -> float:
    """Return γ = Cp / Cv."""

    cp_si = validate_positive(as_si(cp, SPECIFIC_HEAT, "cp"), "cp")
    cv_si = validate_positive(as_si(cv, SPECIFIC_HEAT, "cv"), "cv")
    gamma = cp_si / cv_si
    return require_gamma(gamma)


def speed_of_sound(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Return a = sqrt(γ R T)."""

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    g = require_gamma(gamma)
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    return quantity(math.sqrt(g * r * t), SI.get("m/s"))


def specific_enthalpy(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
    *,
    reference_temperature: Quantity | None = None,
    reference_enthalpy: Quantity | None = None,
) -> Quantity:
    """
    Return h = href + Cp (T - Tref).

    Default datum is h(0 K) = 0 for a calorically perfect gas, which is a
    modelling choice — not a formation enthalpy.
    """

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    t_ref = 0.0
    if reference_temperature is not None:
        t_ref = as_si(reference_temperature, TEMPERATURE, "reference_temperature")
        if t_ref < 0.0:
            raise InvalidInputError("reference_temperature must be non-negative.")
    h_ref = 0.0
    if reference_enthalpy is not None:
        h_ref = as_si(reference_enthalpy, SPECIFIC_ENERGY, "reference_enthalpy")
    cp = as_si(cp_from_gamma(gamma, molar_mass), SPECIFIC_HEAT, "cp")
    return quantity(h_ref + cp * (t - t_ref), UNIT_SPECIFIC_ENERGY)


def specific_internal_energy(
    temperature: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
    *,
    reference_temperature: Quantity | None = None,
    reference_internal_energy: Quantity | None = None,
) -> Quantity:
    """Return u = uref + Cv (T - Tref). Default datum u(0 K) = 0."""

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    t_ref = 0.0
    if reference_temperature is not None:
        t_ref = as_si(reference_temperature, TEMPERATURE, "reference_temperature")
        if t_ref < 0.0:
            raise InvalidInputError("reference_temperature must be non-negative.")
    u_ref = 0.0
    if reference_internal_energy is not None:
        u_ref = as_si(
            reference_internal_energy,
            SPECIFIC_ENERGY,
            "reference_internal_energy",
        )
    cv = as_si(cv_from_gamma(gamma, molar_mass), SPECIFIC_HEAT, "cv")
    return quantity(u_ref + cv * (t - t_ref), UNIT_SPECIFIC_ENERGY)


def specific_entropy_change(
    temperature_1: Quantity,
    temperature_2: Quantity,
    pressure_1: Quantity,
    pressure_2: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """
    Return s2 - s1 = Cp ln(T2/T1) - R ln(p2/p1).

    For an isentropic process the result is identically zero within
    floating-point tolerance when p2/p1 = (T2/T1)^(γ/(γ-1)).
    """

    t1 = validate_positive(as_si(temperature_1, TEMPERATURE, "temperature_1"), "T1")
    t2 = validate_positive(as_si(temperature_2, TEMPERATURE, "temperature_2"), "T2")
    p1 = validate_positive(as_si(pressure_1, PRESSURE, "pressure_1"), "p1")
    p2 = validate_positive(as_si(pressure_2, PRESSURE, "pressure_2"), "p2")
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    cp = as_si(cp_from_gamma(gamma, molar_mass), SPECIFIC_HEAT, "cp")
    ds = cp * math.log(t2 / t1) - r * math.log(p2 / p1)
    return quantity(ds, UNIT_SPECIFIC_HEAT)


def evaluate_state(
    pressure_value: Quantity,
    temperature_value: Quantity,
    molar_mass: Quantity,
    gamma: float | Quantity,
) -> IdealGasState:
    """Assemble a consistent ideal-gas state from p, T, M, γ."""

    g = require_gamma(gamma)
    rho = density(pressure_value, temperature_value, molar_mass)
    r = specific_gas_constant(molar_mass)
    a = speed_of_sound(temperature_value, g, molar_mass)
    return IdealGasState(
        pressure=pressure_value,
        temperature=temperature_value,
        density=rho,
        specific_gas_constant=r,
        gamma=g,
        molar_mass=molar_mass,
        speed_of_sound=a,
        validity=ValidityStatus.VALID,
    )


def molar_mass_from_kg_per_kmol(value: float) -> Quantity:
    """
    Convert a kg/kmol (g/mol) molecular weight to kg/mol.

    Rocket literature often reports M in g/mol. COSMOS SI uses kg/mol.
    """

    mw = as_dimensionless(value, "molecular_weight_g_per_mol")
    if mw <= 0.0:
        raise InvalidInputError("molecular weight must be positive.")
    return quantity(mw / 1000.0, UNIT_MOLAR_MASS)
