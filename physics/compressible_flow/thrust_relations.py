"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.thrust_relations
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Rocket thrust and ideal thrust-coefficient relations.

Description:
    F = ṁ Ve + (pe - pa) Ae

    Ideal thrust coefficient (calorically perfect, isentropic):

        Cf = sqrt( (2 γ^2 /(γ-1)) * (2/(γ+1))^((γ+1)/(γ-1))
                   * (1 - (pe/p0)^((γ-1)/γ)) )
             + ((pe - pa)/p0) * ε

Sources
-------
    Sutton, G. P., and Biblarz, O., Rocket Propulsion Elements.
    Huzel & Huang, NASA SP-125.
    Anderson, Modern Compressible Flow (nozzle performance).
"""

from __future__ import annotations

import math

from core.dimension import AREA, FORCE, PRESSURE, VELOCITY
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_non_negative, validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma

__all__ = (
    "THRUST",
    "thrust",
    "ideal_thrust_coefficient",
)

THRUST = ModelIdentity(
    model_id="PHYS-004.thrust.momentum_pressure",
    model_name="Rocket thrust relation",
    physical_domain="compressible_flow",
    equations=(
        "F = mdot * Ve + (pe - pa) * Ae",
        "Cf = F / (p0 * At)",
    ),
    inputs=("mdot [kg/s]", "Ve [m/s]", "pe [Pa]", "pa [Pa]", "Ae [m2]"),
    outputs=("F [N]", "Cf [-]"),
    assumptions=("Steady 1D exit plane; ambient pressure uniform.",),
    validity_range="mdot >= 0; Ae > 0; pressures finite",
    source="Sutton & Biblarz; Huzel & Huang, NASA SP-125.",
    verification_status="analytical_verification: vacuum vs adapted; Cf dimensions",
    limitations=("Does not include time-dependent or three-dimensional losses.",),
)


def thrust(
    mass_flow: Quantity,
    exit_velocity: Quantity,
    exit_pressure: Quantity,
    ambient_pressure: Quantity,
    exit_area: Quantity,
) -> Quantity:
    """Return F = ṁ Ve + (pe - pa) Ae."""

    mdot = validate_non_negative(as_si(mass_flow, SI.get("kg/s").dimension, "mass_flow"), "mass_flow")
    ve = as_si(exit_velocity, VELOCITY, "exit_velocity")
    pe = as_si(exit_pressure, PRESSURE, "exit_pressure")
    pa = as_si(ambient_pressure, PRESSURE, "ambient_pressure")
    ae = validate_positive(as_si(exit_area, AREA, "exit_area"), "exit_area")
    if ve < 0.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("exit velocity must be non-negative.")
    if pe < 0.0 or pa < 0.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("pressures must be non-negative.")
    return quantity(mdot * ve + (pe - pa) * ae, SI.get("N"))


def ideal_thrust_coefficient(
    gamma: float,
    exit_pressure_ratio: float,
    ambient_pressure_ratio: float,
    expansion_ratio: float,
) -> float:
    """
    Return the ideal Cf.

    ``exit_pressure_ratio`` is pe/p0; ``ambient_pressure_ratio`` is pa/p0;
    ``expansion_ratio`` is Ae/At.
    """

    g = require_gamma(gamma)
    pe_p0 = exit_pressure_ratio
    pa_p0 = ambient_pressure_ratio
    eps = expansion_ratio
    if not 0.0 < pe_p0 <= 1.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("pe/p0 must satisfy 0 < pe/p0 <= 1.")
    if pa_p0 < 0.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("pa/p0 must be non-negative.")
    eps = validate_positive(eps, "expansion_ratio")
    term = (
        (2.0 * g * g / (g - 1.0))
        * ((2.0 / (g + 1.0)) ** ((g + 1.0) / (g - 1.0)))
        * (1.0 - pe_p0 ** ((g - 1.0) / g))
    )
    return math.sqrt(term) + (pe_p0 - pa_p0) * eps


def thrust_from_coefficient(
    thrust_coefficient: float,
    stagnation_pressure: Quantity,
    throat_area: Quantity,
) -> Quantity:
    """Return F = Cf p0 At."""

    p0 = validate_positive(
        as_si(stagnation_pressure, PRESSURE, "stagnation_pressure"),
        "stagnation_pressure",
    )
    at = validate_positive(as_si(throat_area, AREA, "throat_area"), "throat_area")
    return quantity(thrust_coefficient * p0 * at, SI.get("N"))


# FORCE imported for dimensional documentation of the newton.
_ = FORCE
