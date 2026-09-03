"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.isentropic
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Isentropic calorically perfect gas relations.

Description:
    T0/T = 1 + ((γ-1)/2) M^2
    p0/p = (T0/T)^(γ/(γ-1))
    ρ0/ρ = (T0/T)^(1/(γ-1))

Sources
-------
    Anderson, J. D., Modern Compressible Flow, isentropic-flow chapter.
"""

from __future__ import annotations

from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "ISENTROPIC",
    "stagnation_temperature_ratio",
    "stagnation_pressure_ratio",
    "stagnation_density_ratio",
    "static_temperature_ratio",
    "static_pressure_ratio",
    "mach_from_pressure_ratio",
)

ISENTROPIC = ModelIdentity(
    model_id="PHYS-004.isentropic.stagnation",
    model_name="Isentropic stagnation relations",
    physical_domain="compressible_flow",
    equations=(
        "T0/T = 1 + ((gamma-1)/2) M^2",
        "p0/p = (T0/T)^(gamma/(gamma-1))",
        "rho0/rho = (T0/T)^(1/(gamma-1))",
    ),
    inputs=("M [-]", "gamma [-]"),
    outputs=("T0/T [-]", "p0/p [-]", "rho0/rho [-]"),
    assumptions=(
        "Calorically perfect ideal gas.",
        "Reversible adiabatic (isentropic) process.",
        "Frozen composition / constant gamma.",
    ),
    validity_range="M >= 0; 1 < gamma <= 3",
    source="Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: M=0 ratios=1; M=1 known values; isentropic Δs=0",
    limitations=("Not valid through shocks; not a real-gas isentropic model.",),
)


def stagnation_temperature_ratio(mach: float, gamma: float) -> float:
    """Return T0/T."""

    m = require_mach(mach)
    g = require_gamma(gamma)
    return 1.0 + 0.5 * (g - 1.0) * m * m


def stagnation_pressure_ratio(mach: float, gamma: float) -> float:
    """Return p0/p."""

    g = require_gamma(gamma)
    tt = stagnation_temperature_ratio(mach, g)
    return tt ** (g / (g - 1.0))


def stagnation_density_ratio(mach: float, gamma: float) -> float:
    """Return ρ0/ρ."""

    g = require_gamma(gamma)
    tt = stagnation_temperature_ratio(mach, g)
    return tt ** (1.0 / (g - 1.0))


def static_temperature_ratio(mach: float, gamma: float) -> float:
    """Return T/T0."""

    return 1.0 / stagnation_temperature_ratio(mach, gamma)


def static_pressure_ratio(mach: float, gamma: float) -> float:
    """Return p/p0."""

    return 1.0 / stagnation_pressure_ratio(mach, gamma)


def mach_from_pressure_ratio(p_over_p0: float, gamma: float) -> float:
    """
    Return M from an isentropic static-to-stagnation pressure ratio.

    Requires 0 < p/p0 <= 1. M=0 when p/p0 = 1.
    """

    g = require_gamma(gamma)
    if p_over_p0 <= 0.0 or p_over_p0 > 1.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("isentropic p/p0 must satisfy 0 < p/p0 <= 1.")
    if p_over_p0 == 1.0:
        return 0.0
    exponent = (g - 1.0) / g
    t_over_t0 = p_over_p0 ** exponent
    mach_sq = (2.0 / (g - 1.0)) * (1.0 / t_over_t0 - 1.0)
    if mach_sq < 0.0:
        from core.exceptions import InvalidInputError

        raise InvalidInputError("pressure ratio implies negative M^2.")
    return mach_sq ** 0.5
