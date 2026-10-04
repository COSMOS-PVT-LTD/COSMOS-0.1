"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.lagrange
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.lagrange foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.interpolation.barycentric import interpolate as _barycentric


def interpolate(nodes: ArrayLike, values: ArrayLike, query: float, *, extrapolate: bool = False) -> float:
    """Lagrange polynomial in its mathematically equivalent barycentric representation."""
    return _barycentric(nodes, values, query, extrapolate=extrapolate)
