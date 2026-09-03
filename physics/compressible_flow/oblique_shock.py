"""
COSMOS Rocket Propulsion Platform

Module: physics.compressible_flow.oblique_shock
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Oblique-shock θ-β-M relation and downstream state.

Description:
    tan θ = 2 cot β (M1^2 sin^2 β - 1) / (M1^2 (γ + cos 2β) + 2)

    The wave angle β is inverted numerically on the physical residual
    (NUM-CONTRACT-ISSUE). Weak and strong solutions are distinct brackets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.exceptions import InvalidInputError, SolverConvergenceError

from physics.compressible_flow.normal_shock import evaluate_normal_shock
from physics.contracts.numerics_port import bracketed_root
from physics.model import ModelIdentity
from physics.quantities import require_gamma, require_mach

__all__ = (
    "OBLIQUE_SHOCK",
    "ObliqueShockState",
    "deflection_from_wave_angle",
    "wave_angle",
    "evaluate_oblique_shock",
)

OBLIQUE_SHOCK = ModelIdentity(
    model_id="PHYS-004.shock.oblique",
    model_name="Oblique shock theta-beta-M",
    physical_domain="compressible_flow",
    equations=(
        "tan theta = 2 cot beta (M1^2 sin^2 beta - 1) "
        "/ (M1^2 (gamma + cos 2 beta) + 2)",
        "Mn1 = M1 sin beta",
    ),
    inputs=("M1 [-]", "theta [rad]", "gamma [-]"),
    outputs=("beta [rad]", "M2 [-]", "p2/p1 [-]"),
    assumptions=("Calorically perfect; attached planar oblique shock.",),
    validity_range="M1 > 1; 0 < theta < theta_max(M1, gamma); mu < beta < 90 deg",
    numerical_method_dependency="scalar root for beta (NUM-CONTRACT-ISSUE)",
    source="Anderson, Modern Compressible Flow, oblique-shock chapter.",
    verification_status="analytical_verification: theta=0 => beta = mu; normal-shock limit",
    limitations=("Detached shocks are not a θ-β-M solution.",),
)


@dataclass(frozen=True, slots=True)
class ObliqueShockState:
    """Attached oblique-shock solution."""

    mach_upstream: float
    deflection_rad: float
    wave_angle_rad: float
    mach_downstream: float
    pressure_ratio: float
    density_ratio: float
    temperature_ratio: float
    branch: str
    gamma: float
    identity: ModelIdentity = OBLIQUE_SHOCK


def deflection_from_wave_angle(mach: float, wave_angle_rad: float, gamma: float) -> float:
    """Return deflection θ [rad] for a given wave angle β."""

    m = require_mach(mach, minimum=1.0, exclusive_min=True)
    g = require_gamma(gamma)
    beta = wave_angle_rad
    if beta <= 0.0 or beta >= 0.5 * math.pi:
        raise InvalidInputError("wave angle must lie in (0, pi/2).")
    mu = math.asin(1.0 / m)
    if beta < mu:
        raise InvalidInputError("wave angle is below the Mach angle.")
    sin_b = math.sin(beta)
    mn_sq = m * m * sin_b * sin_b
    if mn_sq <= 1.0:
        return 0.0
    numerator = 2.0 * math.cos(beta) / math.sin(beta) * (mn_sq - 1.0)
    denominator = m * m * (g + math.cos(2.0 * beta)) + 2.0
    return math.atan(numerator / denominator)


def wave_angle(
    mach: float,
    deflection_rad: float,
    gamma: float,
    *,
    branch: str = "weak",
) -> float:
    """Invert θ-β-M for the wave angle β [rad]."""

    m = require_mach(mach, minimum=1.0, exclusive_min=True)
    g = require_gamma(gamma)
    if deflection_rad < 0.0:
        raise InvalidInputError("deflection angle must be non-negative.")
    mu = math.asin(1.0 / m)
    if deflection_rad == 0.0:
        return mu

    def residual(beta: float) -> float:
        return deflection_from_wave_angle(m, beta, g) - deflection_rad

    # Sample theta_max on a coarse beta grid to reject detached cases.
    samples = 80
    max_theta = 0.0
    beta_at_max = mu
    for i in range(samples + 1):
        beta = mu + (0.5 * math.pi - 1.0e-6 - mu) * i / samples
        try:
            theta = deflection_from_wave_angle(m, beta, g)
        except InvalidInputError:
            continue
        if theta > max_theta:
            max_theta = theta
            beta_at_max = beta
    if deflection_rad > max_theta:
        raise InvalidInputError(
            "deflection exceeds theta_max; shock is detached."
        )

    try:
        if branch == "weak":
            return bracketed_root(residual, mu + 1.0e-8, beta_at_max)
        if branch == "strong":
            return bracketed_root(residual, beta_at_max, 0.5 * math.pi - 1.0e-6)
    except SolverConvergenceError as exc:
        raise InvalidInputError("oblique-shock wave angle did not converge.") from exc
    raise InvalidInputError("branch must be 'weak' or 'strong'.")


def evaluate_oblique_shock(
    mach_upstream: float,
    deflection_rad: float,
    gamma: float,
    *,
    branch: str = "weak",
) -> ObliqueShockState:
    """Evaluate an attached oblique shock."""

    m1 = require_mach(mach_upstream, minimum=1.0, exclusive_min=True)
    g = require_gamma(gamma)
    beta = wave_angle(m1, deflection_rad, g, branch=branch)
    mn1 = m1 * math.sin(beta)
    if mn1 <= 1.0 + 1.0e-12:
        return ObliqueShockState(
            mach_upstream=m1,
            deflection_rad=deflection_rad,
            wave_angle_rad=beta,
            mach_downstream=m1,
            pressure_ratio=1.0,
            density_ratio=1.0,
            temperature_ratio=1.0,
            branch=branch,
            gamma=g,
        )
    normal = evaluate_normal_shock(mn1, g)
    m2 = normal.mach_downstream / math.sin(beta - deflection_rad)
    return ObliqueShockState(
        mach_upstream=m1,
        deflection_rad=deflection_rad,
        wave_angle_rad=beta,
        mach_downstream=m2,
        pressure_ratio=normal.pressure_ratio,
        density_ratio=normal.density_ratio,
        temperature_ratio=normal.temperature_ratio,
        branch=branch,
        gamma=g,
    )
