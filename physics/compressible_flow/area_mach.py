"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.area_mach
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Isentropic area–Mach relation and its inversion.

Description:
    A/A* = (1/M) * [(1 + ((γ-1)/2) M^2) / ((γ+1)/2)] ^ ((γ+1)/(2(γ-1)))

    M = 1 is handled as an identity (A/A* = 1). M = 0 is singular and
    rejected. Inverse Mach is two-valued (subsonic / supersonic).
"""

from __future__ import annotations

from core.exceptions import InvalidInputError

from physics.compressible_flow.isentropic import ISENTROPIC
from physics.contracts.numerics_port import bracketed_root
from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "AREA_MACH",
    "area_ratio",
    "mach_from_area_ratio",
)

AREA_MACH = ModelIdentity(
    model_id="PHYS-004.area_mach.isentropic",
    model_name="Isentropic area-Mach relation",
    physical_domain="compressible_flow",
    equations=(
        "A/A* = (1/M) * [(1 + ((gamma-1)/2) M^2) / ((gamma+1)/2)] "
        "^ ((gamma+1)/(2(gamma-1)))",
    ),
    inputs=("M [-]", "gamma [-]"),
    outputs=("A/A* [-]",),
    assumptions=("Isentropic, calorically perfect, quasi-1D flow.",),
    validity_range="M > 0; 1 < gamma <= 3; A/A* >= 1",
    numerical_method_dependency="scalar root for inverse Mach (NUM-CONTRACT-ISSUE)",
    source="Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: A/A*(M=1)=1; A/A* >= 1; two-branch inverse",
    limitations=("Sonic throat assumed; not a shocked nozzle solution.",),
)


def area_ratio(mach: float, gamma: float) -> float:
    """Return A/A* for M > 0."""

    m = require_mach(mach, exclusive_min=True)
    g = require_gamma(gamma)
    if abs(m - 1.0) <= 1.0e-15:
        return 1.0
    term = (1.0 + 0.5 * (g - 1.0) * m * m) / (0.5 * (g + 1.0))
    exponent = (g + 1.0) / (2.0 * (g - 1.0))
    return (1.0 / m) * term ** exponent


def mach_from_area_ratio(
    area_over_star: float,
    gamma: float,
    *,
    branch: str = "supersonic",
) -> float:
    """
    Invert A/A* for Mach number.

    Parameters
    ----------
    branch:
        ``"subsonic"`` for 0 < M <= 1 or ``"supersonic"`` for M >= 1.
    """

    g = require_gamma(gamma)
    if area_over_star < 1.0:
        raise InvalidInputError("A/A* must be >= 1 for isentropic 1D flow.")
    if abs(area_over_star - 1.0) <= 1.0e-14:
        return 1.0

    def residual(mach: float) -> float:
        return area_ratio(mach, g) - area_over_star

    if branch == "subsonic":
        return bracketed_root(residual, 1.0e-8, 1.0)
    if branch == "supersonic":
        # Large but finite search cap; extreme area ratios remain valid.
        upper = 50.0
        if residual(upper) > 0.0:
            # Still below the target at M=50; expand once.
            upper = 80.0
        return bracketed_root(residual, 1.0, upper)
    raise InvalidInputError("branch must be 'subsonic' or 'supersonic'.")


# Re-export isentropic identity for documentation coupling.
_ = ISENTROPIC
