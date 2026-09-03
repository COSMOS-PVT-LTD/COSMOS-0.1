"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.choked_flow
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Choked isentropic mass-flow relations.

Description:
    For a choked sonic throat:

        ṁ = p0 A* / sqrt(T0) * sqrt(γ/R)
            * ((γ+1)/2) ^ (-(γ+1)/(2(γ-1)))

    Choking requires the back-pressure ratio to be at or below the
    isentropic sonic value p*/p0.
"""

from __future__ import annotations

import math

from core.dimension import AREA, PRESSURE, TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.compressible_flow.isentropic import static_pressure_ratio
from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma
from physics.si import SPECIFIC_HEAT
from physics.thermodynamics.ideal_gas import specific_gas_constant

__all__ = (
    "CHOKED_FLOW",
    "mass_flow_parameter",
    "choked_mass_flow",
    "is_choked",
)

CHOKED_FLOW = ModelIdentity(
    model_id="PHYS-004.choked.mass_flow",
    model_name="Isentropic choked mass flow",
    physical_domain="compressible_flow",
    equations=(
        "mdot = p0 * A_star / sqrt(T0) * sqrt(gamma/R) "
        "* ((gamma+1)/2)^(-(gamma+1)/(2(gamma-1)))",
    ),
    inputs=("p0 [Pa]", "T0 [K]", "A* [m2]", "gamma [-]", "R [J/(kg K)]"),
    outputs=("mdot [kg/s]",),
    assumptions=("Sonic throat; isentropic; calorically perfect.",),
    validity_range="p0 > 0; T0 > 0; A* > 0; 1 < gamma <= 3",
    source="Anderson, Modern Compressible Flow; Sutton & Biblarz.",
    verification_status="analytical_verification: dimensions; gamma=1.4 parameter",
    limitations=("Does not include discharge coefficient; see losses.py.",),
)


def mass_flow_parameter(gamma: float, specific_gas_constant_si: float) -> float:
    """Return Γ = sqrt(γ/R) * ((γ+1)/2)^(-(γ+1)/(2(γ-1)))."""

    g = require_gamma(gamma)
    if specific_gas_constant_si <= 0.0:
        raise InvalidInputError("specific gas constant must be positive.")
    return math.sqrt(g / specific_gas_constant_si) * (
        (g + 1.0) / 2.0
    ) ** (-(g + 1.0) / (2.0 * (g - 1.0)))


def choked_mass_flow(
    stagnation_pressure: Quantity,
    stagnation_temperature: Quantity,
    throat_area: Quantity,
    gamma: float,
    molar_mass: Quantity,
) -> Quantity:
    """Return choked mass-flow rate [kg/s]."""

    p0 = validate_positive(
        as_si(stagnation_pressure, PRESSURE, "stagnation_pressure"),
        "stagnation_pressure",
    )
    t0 = validate_positive(
        as_si(stagnation_temperature, TEMPERATURE, "stagnation_temperature"),
        "stagnation_temperature",
    )
    area = validate_positive(as_si(throat_area, AREA, "throat_area"), "throat_area")
    r = as_si(specific_gas_constant(molar_mass), SPECIFIC_HEAT, "R")
    mdot = p0 * area / math.sqrt(t0) * mass_flow_parameter(gamma, r)
    return quantity(mdot, SI.get("kg/s"))


def is_choked(back_pressure_ratio: float, gamma: float) -> bool:
    """
    Return True when pb/p0 is at or below the sonic static pressure ratio.

    ``back_pressure_ratio`` is pb/p0.
    """

    if back_pressure_ratio <= 0.0 or back_pressure_ratio > 1.0:
        raise InvalidInputError("back_pressure_ratio must satisfy 0 < pb/p0 <= 1.")
    sonic = static_pressure_ratio(1.0, gamma)
    return back_pressure_ratio <= sonic
