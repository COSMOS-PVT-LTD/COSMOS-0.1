"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.fanno
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Fanno-flow (adiabatic duct with wall friction) relations.

Description:
    T/T* = (γ+1) / (2 + (γ-1) M^2)
    p/p* = (1/M) sqrt(T/T*)
    4 f Lmax / D = ((γ+1)/(2γ)) ln[ ((γ+1) M^2) / (2+(γ-1)M^2) ]
                   + (1/γ) (1/M^2 - 1)

Sources
-------
    Anderson, Modern Compressible Flow, Fanno-flow chapter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.exceptions import InvalidInputError

from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = ("FANNO", "FannoState", "evaluate_fanno")

FANNO = ModelIdentity(
    model_id="PHYS-004.fanno.adiabatic_friction",
    model_name="Fanno flow",
    physical_domain="compressible_flow",
    equations=(
        "T/T* = (gamma+1) / (2 + (gamma-1) M^2)",
        "p/p* = (1/M) sqrt(T/T*)",
        "4fLmax/D = ((gamma+1)/(2 gamma)) ln[((gamma+1)M^2)/(2+(gamma-1)M^2)] "
        "+ (1/gamma)(1/M^2 - 1)",
    ),
    inputs=("M [-]", "gamma [-]"),
    outputs=("T/T* [-]", "p/p* [-]", "4fLmax/D [-]"),
    assumptions=("Adiabatic; calorically perfect; constant friction factor.",),
    validity_range="M > 0; 1 < gamma <= 3",
    source="Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: M=1 => T/T*=1, 4fLmax/D=0",
    limitations=("f is an input, not a wall-roughness model.",),
)


@dataclass(frozen=True, slots=True)
class FannoState:
    """Fanno reference-state ratios."""

    mach: float
    temperature_ratio: float
    pressure_ratio: float
    density_ratio: float
    friction_length_parameter: float
    gamma: float
    identity: ModelIdentity = FANNO


def evaluate_fanno(mach: float, gamma: float) -> FannoState:
    """Evaluate Fanno ratios relative to the sonic reference state."""

    m = require_mach(mach, exclusive_min=True)
    g = require_gamma(gamma)
    t_ratio = (g + 1.0) / (2.0 + (g - 1.0) * m * m)
    p_ratio = math.sqrt(t_ratio) / m
    rho_ratio = p_ratio / t_ratio
    if abs(m - 1.0) <= 1.0e-15:
        fl = 0.0
    else:
        fl = ((g + 1.0) / (2.0 * g)) * math.log(
            ((g + 1.0) * m * m) / (2.0 + (g - 1.0) * m * m)
        ) + (1.0 / g) * (1.0 / (m * m) - 1.0)
    if fl < -1.0e-12:
        raise InvalidInputError("Fanno 4fLmax/D evaluated negative.")
    return FannoState(
        mach=m,
        temperature_ratio=t_ratio,
        pressure_ratio=p_ratio,
        density_ratio=rho_ratio,
        friction_length_parameter=max(fl, 0.0),
        gamma=g,
    )
