"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.stability
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.stability foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.numerical_checks import finite, invalid, positive


def cfl(speed: float, time_step: float, spacing: float) -> float:
    """Nonnegative advective Courant number; stability limit is scheme-specific."""
    v = finite(speed)
    if v<0:
        invalid("Speed must be nonnegative.")
    return v*positive(time_step)/positive(spacing)

def diffusion_limit(diffusivity: float, spacing: float) -> float:
    """1D central-difference forward-Euler sufficient limit dt<=h²/(2a)."""
    a,h = positive(diffusivity),positive(spacing)
    return h*h/(2*a)

def require_stable(time_step: float, limit: float) -> None:
    if positive(time_step)>positive(limit):
        invalid("Explicit step violates the supplied stability limit.")
