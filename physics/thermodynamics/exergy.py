"""
COSMOS Rocket Propulsion Platform

Module: physics.thermodynamics.exergy
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Flow availability (stream exergy) for an ideal gas.

Description:
    Physical exergy of a flowing stream relative to an environment (T0, p0),
    neglecting kinetic, potential, and chemical contributions:

        ψ = (h - h0) - T0 (s - s0)

    For a calorically perfect ideal gas this becomes:

        ψ = Cp (T - T0) - T0 [Cp ln(T/T0) - R ln(p/p0)]

Sources
-------
    Moran & Shapiro, Fundamentals of Engineering Thermodynamics.
    Cengel & Boles, Thermodynamics (availability / exergy chapter).
"""

from __future__ import annotations

import math

from core.dimension import PRESSURE, TEMPERATURE
from core.quantity import Quantity
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma
from physics.si import SPECIFIC_HEAT, UNIT_SPECIFIC_ENERGY
from physics.thermodynamics.ideal_gas import cp_from_gamma, specific_gas_constant

__all__ = ("FLOW_EXERGY", "ideal_gas_flow_exergy")

FLOW_EXERGY = ModelIdentity(
    model_id="PHYS-001.exergy.flow_ideal_gas",
    model_name="Ideal-gas flow exergy (thermo-mechanical)",
    physical_domain="thermodynamics",
    equations=(
        "psi = (h - h0) - T0 * (s - s0)",
        "psi = Cp*(T-T0) - T0*(Cp*ln(T/T0) - R*ln(p/p0))",
    ),
    inputs=("T [K]", "p [Pa]", "T0 [K]", "p0 [Pa]", "gamma [-]", "M [kg/mol]"),
    outputs=("flow_exergy [J/kg]",),
    assumptions=(
        "Calorically perfect ideal gas.",
        "No kinetic or potential contribution.",
        "No chemical exergy (species match the environment).",
    ),
    validity_range="T > 0 K; p > 0 Pa; T0 > 0 K; p0 > 0 Pa",
    source="Moran & Shapiro; Cengel & Boles (flow availability).",
    verification_status="analytical_verification: ψ(T0,p0)=0; isentropic expansion identity",
    limitations=(
        "Chemical exergy is an OPEN SCIENTIFIC ISSUE pending thermochemistry coupling.",
    ),
)


def ideal_gas_flow_exergy(
    temperature: Quantity,
    pressure: Quantity,
    environment_temperature: Quantity,
    environment_pressure: Quantity,
    gamma: float | Quantity,
    molar_mass: Quantity,
) -> Quantity:
    """Return thermo-mechanical flow exergy of a calorically perfect gas."""

    t = validate_positive(as_si(temperature, TEMPERATURE, "temperature"), "temperature")
    p = validate_positive(as_si(pressure, PRESSURE, "pressure"), "pressure")
    t0 = validate_positive(
        as_si(environment_temperature, TEMPERATURE, "environment_temperature"),
        "environment_temperature",
    )
    p0 = validate_positive(
        as_si(environment_pressure, PRESSURE, "environment_pressure"),
        "environment_pressure",
    )
    g = require_gamma(gamma)
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    cp = as_si(cp_from_gamma(g, molar_mass), SPECIFIC_HEAT, "cp")
    psi = cp * (t - t0) - t0 * (cp * math.log(t / t0) - r * math.log(p / p0))
    return quantity(psi, UNIT_SPECIFIC_ENERGY)
