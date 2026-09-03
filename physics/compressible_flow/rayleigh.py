"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.rayleigh
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Rayleigh-flow (frictionless duct with heat addition) relations.

Description:
    T/T* = M^2 (1+γ)^2 / (1 + γ M^2)^2
    p/p* = (1+γ) / (1 + γ M^2)
    T0/T0* = [2(γ+1) M^2 (1 + ((γ-1)/2) M^2)] / (1 + γ M^2)^2

Sources
-------
    Anderson, Modern Compressible Flow, Rayleigh-flow chapter.
"""

from __future__ import annotations

from dataclasses import dataclass

from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = ("RAYLEIGH", "RayleighState", "evaluate_rayleigh")

RAYLEIGH = ModelIdentity(
    model_id="PHYS-004.rayleigh.heat_addition",
    model_name="Rayleigh flow",
    physical_domain="compressible_flow",
    equations=(
        "T/T* = M^2 (1+gamma)^2 / (1 + gamma M^2)^2",
        "p/p* = (1+gamma) / (1 + gamma M^2)",
        "T0/T0* = 2(gamma+1) M^2 (1+((gamma-1)/2) M^2) / (1 + gamma M^2)^2",
    ),
    inputs=("M [-]", "gamma [-]"),
    outputs=("T/T* [-]", "p/p* [-]", "T0/T0* [-]"),
    assumptions=("Frictionless; calorically perfect; heat addition as a bulk source.",),
    validity_range="M > 0; 1 < gamma <= 3",
    source="Anderson, Modern Compressible Flow.",
    verification_status="analytical_verification: M=1 identities T/T*=p/p*=T0/T0*=1",
    limitations=("Not a finite-rate combustion model.",),
)


@dataclass(frozen=True, slots=True)
class RayleighState:
    """Rayleigh reference-state ratios."""

    mach: float
    temperature_ratio: float
    pressure_ratio: float
    stagnation_temperature_ratio: float
    gamma: float
    identity: ModelIdentity = RAYLEIGH


def evaluate_rayleigh(mach: float, gamma: float) -> RayleighState:
    """Evaluate Rayleigh ratios relative to the sonic reference state."""

    m = require_mach(mach, exclusive_min=True)
    g = require_gamma(gamma)
    denom = (1.0 + g * m * m) ** 2
    t_ratio = (m * m) * (1.0 + g) ** 2 / denom
    p_ratio = (1.0 + g) / (1.0 + g * m * m)
    t0_ratio = (
        2.0 * (g + 1.0) * m * m * (1.0 + 0.5 * (g - 1.0) * m * m) / denom
    )
    return RayleighState(
        mach=m,
        temperature_ratio=t_ratio,
        pressure_ratio=p_ratio,
        stagnation_temperature_ratio=t0_ratio,
        gamma=g,
    )
