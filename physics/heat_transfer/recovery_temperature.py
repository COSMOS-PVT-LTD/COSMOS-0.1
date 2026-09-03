"""
COSMOS Rocket Propulsion Platform

Module: physics.heat_transfer.recovery_temperature
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Adiabatic-wall / recovery temperature.

Description:
    T_aw = T_e * (1 + r * ((γ-1)/2) M_e^2)
    r ≈ Pr^{1/2}  (laminar) or Pr^{1/3} (turbulent)

Sources
-------
    Incropera et al.; Anderson, Modern Compressible Flow (recovery factor).
"""

from __future__ import annotations

from core.dimension import TEMPERATURE
from core.exceptions import InvalidInputError
from core.quantity import Quantity
from core.unit import SI
from core.validation import validate_positive

from physics.model import ModelIdentity
from physics.quantities import as_si, quantity, require_gamma, require_mach

__all__ = ("RECOVERY", "adiabatic_wall_temperature", "recovery_factor")

RECOVERY = ModelIdentity(
    model_id="PHYS-005.recovery.adiabatic_wall",
    model_name="Recovery / adiabatic-wall temperature",
    physical_domain="heat_transfer",
    equations=(
        "T_aw = T_e * (1 + r * ((gamma-1)/2) * M^2)",
        "r_lam = Pr**0.5",
        "r_turb = Pr**(1/3)",
    ),
    inputs=("T_e [K]", "M [-]", "gamma [-]", "Pr [-]", "regime"),
    outputs=("T_aw [K]",),
    assumptions=("Perfect gas; recovery factor from Prandtl scaling.",),
    validity_range="T_e > 0; M >= 0; Pr > 0",
    source="Incropera et al.; Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: M=0 => T_aw=T_e; r(Pr=1)=1",
    limitations=("Does not replace a boundary-layer energy solution.",),
)


def recovery_factor(prandtl: float, *, regime: str = "turbulent") -> float:
    """Return r(Pr) for laminar or turbulent flow."""

    if prandtl <= 0.0:
        raise InvalidInputError("Prandtl number must be positive.")
    if regime == "laminar":
        return prandtl ** 0.5
    if regime == "turbulent":
        return prandtl ** (1.0 / 3.0)
    raise InvalidInputError("regime must be 'laminar' or 'turbulent'.")


def adiabatic_wall_temperature(
    static_temperature: Quantity,
    mach: float,
    gamma: float,
    prandtl: float,
    *,
    regime: str = "turbulent",
) -> Quantity:
    """Return T_aw."""

    te = validate_positive(as_si(static_temperature, TEMPERATURE, "T_e"), "T_e")
    m = require_mach(mach)
    g = require_gamma(gamma)
    r = recovery_factor(prandtl, regime=regime)
    taw = te * (1.0 + r * 0.5 * (g - 1.0) * m * m)
    return quantity(taw, SI.get("K"))
