"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.normal_shock
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Rankine–Hugoniot normal-shock relations.

Description:
    M2^2 = (1 + ((γ-1)/2) M1^2) / (γ M1^2 - (γ-1)/2)
    p2/p1 = 1 + (2γ/(γ+1)) (M1^2 - 1)
    ρ2/ρ1 = ((γ+1) M1^2) / ((γ-1) M1^2 + 2)
    T2/T1 = (p2/p1) / (ρ2/ρ1)

    M1 <= 1 is invalid (no compressive shock). M1 → 1 recovers identities.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.exceptions import InvalidInputError

from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "NORMAL_SHOCK",
    "NormalShockState",
    "evaluate_normal_shock",
)

NORMAL_SHOCK = ModelIdentity(
    model_id="PHYS-004.shock.normal",
    model_name="Normal shock relations",
    physical_domain="compressible_flow",
    equations=(
        "M2^2 = (1 + ((gamma-1)/2) M1^2) / (gamma M1^2 - (gamma-1)/2)",
        "p2/p1 = 1 + (2 gamma/(gamma+1)) (M1^2 - 1)",
        "rho2/rho1 = ((gamma+1) M1^2) / ((gamma-1) M1^2 + 2)",
        "T2/T1 = (p2/p1)*(rho1/rho2)",
    ),
    inputs=("M1 [-]", "gamma [-]"),
    outputs=("M2 [-]", "p2/p1 [-]", "T2/T1 [-]", "rho2/rho1 [-]", "p02/p01 [-]"),
    assumptions=("Calorically perfect; thin stationary normal shock; adiabatic.",),
    validity_range="M1 > 1; 1 < gamma <= 3",
    source="Anderson, Modern Compressible Flow, normal-shock chapter.",
    verification_status="analytical_verification: M1→1 identities; Rankine–Hugoniot; p02/p01 < 1",
    limitations=("Not an oblique or moving shock; constant gamma.",),
)


@dataclass(frozen=True, slots=True)
class NormalShockState:
    """Downstream state ratios across a normal shock."""

    mach_upstream: float
    mach_downstream: float
    pressure_ratio: float
    density_ratio: float
    temperature_ratio: float
    stagnation_pressure_ratio: float
    gamma: float
    identity: ModelIdentity = NORMAL_SHOCK


def evaluate_normal_shock(mach_upstream: float, gamma: float) -> NormalShockState:
    """Evaluate Rankine–Hugoniot ratios for M1 > 1."""

    m1 = require_mach(mach_upstream, minimum=1.0, exclusive_min=True)
    g = require_gamma(gamma)
    m1_sq = m1 * m1
    denom = g * m1_sq - 0.5 * (g - 1.0)
    if denom <= 0.0:
        raise InvalidInputError("normal-shock downstream Mach denominator is non-positive.")
    m2_sq = (1.0 + 0.5 * (g - 1.0) * m1_sq) / denom
    m2 = math_sqrt(m2_sq)
    p_ratio = 1.0 + (2.0 * g / (g + 1.0)) * (m1_sq - 1.0)
    rho_ratio = ((g + 1.0) * m1_sq) / ((g - 1.0) * m1_sq + 2.0)
    t_ratio = p_ratio / rho_ratio
    # Stagnation-pressure ratio (Rayleigh pitot / total-pressure loss).
    p02_p01 = (
        (
            ((g + 1.0) * m1_sq) / ((g - 1.0) * m1_sq + 2.0)
        ) ** (g / (g - 1.0))
        * ((g + 1.0) / (2.0 * g * m1_sq - (g - 1.0))) ** (1.0 / (g - 1.0))
    )
    return NormalShockState(
        mach_upstream=m1,
        mach_downstream=m2,
        pressure_ratio=p_ratio,
        density_ratio=rho_ratio,
        temperature_ratio=t_ratio,
        stagnation_pressure_ratio=p02_p01,
        gamma=g,
    )


def math_sqrt(value: float) -> float:
    """Positive square root with an explicit invalidity check."""

    if value < 0.0:
        raise InvalidInputError("normal-shock M2^2 is negative.")
    return value ** 0.5
