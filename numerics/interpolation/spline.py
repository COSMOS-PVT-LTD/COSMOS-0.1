"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.spline
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.spline foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.interpolation.cubic_spline import CubicSpline


def build(
    nodes: ArrayLike,
    values: ArrayLike,
    *,
    boundary: str = "natural",
    endpoint_slopes: tuple[float, float] | None = None,
    extrapolate: bool = False,
) -> CubicSpline:
    """Spline family foundation is explicitly natural/clamped piecewise cubic."""
    return CubicSpline.build(
        nodes,
        values,
        boundary=boundary,
        endpoint_slopes=endpoint_slopes,
        extrapolate=extrapolate,
    )
