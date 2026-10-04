"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.hermite
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.hermite foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.interpolation.linear import _data, _query
from numerics.utilities.numerical_checks import finite, same_shape, vector


def interpolate(
    nodes: ArrayLike,
    values: ArrayLike,
    derivatives: ArrayLike,
    query: float,
    *,
    extrapolate: bool = False,
) -> float:
    """Piecewise cubic Hermite with explicit nodal first derivatives."""
    x, y = _data(nodes, values)
    d = vector(derivatives)
    same_shape(x, d)
    q, i = _query(x, query, extrapolate)
    h = x[i + 1] - x[i]
    t = (q - x[i]) / h
    return finite(
        float(
            (2 * t**3 - 3 * t * t + 1) * y[i]
            + (t**3 - 2 * t * t + t) * h * d[i]
            + (-2 * t**3 + 3 * t * t) * y[i + 1]
            + (t**3 - t * t) * h * d[i + 1]
        )
    )
