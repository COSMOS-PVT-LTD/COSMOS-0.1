"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.interpolation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.interpolation foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.numerical_checks import finite, invalid


def linear(left: float, right: float, weight: float = 0.5) -> float:
    """Face interpolation weight toward right, constrained to [0,1]."""
    l, r, w = finite(left), finite(right), finite(weight)
    if not 0 <= w <= 1:
        invalid("Face interpolation weight must lie in [0,1].")
    return finite((1 - w) * l + w * r)


def upwind(left: float, right: float, velocity: float) -> float:
    return finite(left) if finite(velocity) >= 0 else finite(right)
