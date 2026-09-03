"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.expansion_fan
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Prandtl–Meyer expansion relations.

Description:
    ν(M) = sqrt((γ+1)/(γ-1)) arctan(sqrt(((γ-1)/(γ+1))(M^2-1)))
           - arctan(sqrt(M^2-1))

    Across a centered expansion: ν2 = ν1 + |θ|.
"""

from __future__ import annotations

import math

from core.exceptions import InvalidInputError

from physics.contracts.numerics_port import bracketed_root
from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "PRANDTL_MEYER",
    "prandtl_meyer",
    "mach_from_prandtl_meyer",
    "expanded_mach",
)

PRANDTL_MEYER = ModelIdentity(
    model_id="PHYS-004.expansion.prandtl_meyer",
    model_name="Prandtl-Meyer expansion",
    physical_domain="compressible_flow",
    equations=(
        "nu(M) = sqrt((gamma+1)/(gamma-1)) * arctan(sqrt(((gamma-1)/(gamma+1))"
        "(M^2-1))) - arctan(sqrt(M^2-1))",
        "nu2 = nu1 + theta",
    ),
    inputs=("M [-]", "gamma [-]", "deflection [rad]"),
    outputs=("nu [rad]", "M2 [-]"),
    assumptions=("Isentropic centered expansion; calorically perfect.",),
    validity_range="M >= 1; 1 < gamma <= 3; nu < nu_max",
    numerical_method_dependency="scalar root for inverse nu(M) (NUM-CONTRACT-ISSUE)",
    source="Anderson, Modern Compressible Flow, Prandtl-Meyer chapter.",
    verification_status="analytical_verification: nu(1)=0; nu increasing in M",
    limitations=("Not a shock; not a method-of-characteristics mesh.",),
)


def prandtl_meyer(mach: float, gamma: float) -> float:
    """Return ν(M) in radians."""

    m = require_mach(mach, minimum=1.0)
    g = require_gamma(gamma)
    if m == 1.0:
        return 0.0
    root = math.sqrt(m * m - 1.0)
    return (
        math.sqrt((g + 1.0) / (g - 1.0))
        * math.atan(math.sqrt((g - 1.0) / (g + 1.0)) * root)
        - math.atan(root)
    )


def mach_from_prandtl_meyer(nu_rad: float, gamma: float) -> float:
    """Invert ν(M) for Mach number."""

    g = require_gamma(gamma)
    if nu_rad < 0.0:
        raise InvalidInputError("Prandtl-Meyer angle must be non-negative.")
    if nu_rad == 0.0:
        return 1.0
    nu_max = 0.5 * math.pi * (math.sqrt((g + 1.0) / (g - 1.0)) - 1.0)
    if nu_rad >= nu_max:
        raise InvalidInputError("Prandtl-Meyer angle exceeds nu_max.")

    def residual(mach: float) -> float:
        return prandtl_meyer(mach, g) - nu_rad

    return bracketed_root(residual, 1.0, 80.0)


def expanded_mach(
    mach_upstream: float,
    expansion_angle_rad: float,
    gamma: float,
) -> float:
    """Return downstream Mach after a turning expansion of ``expansion_angle_rad``."""

    if expansion_angle_rad < 0.0:
        raise InvalidInputError("expansion angle must be non-negative.")
    nu1 = prandtl_meyer(mach_upstream, gamma)
    return mach_from_prandtl_meyer(nu1 + expansion_angle_rad, gamma)
