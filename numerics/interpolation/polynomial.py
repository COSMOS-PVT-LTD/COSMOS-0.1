"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.polynomial
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.polynomial foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.interpolation.linear import _data, _query
from numerics.utilities.numerical_checks import finite


def interpolate(
    nodes: ArrayLike, values: ArrayLike, query: float, *, extrapolate: bool = False
) -> float:
    """Newton divided differences; increasing unique nodes, no silent extrapolation."""
    x, c = _data(nodes, values)
    q, _ = _query(x, query, extrapolate)
    for order in range(1, len(x)):
        c[order:] = (c[order:] - c[order - 1 : -1]) / (x[order:] - x[:-order])
    result = float(c[-1])
    for i in range(len(x) - 2, -1, -1):
        result = result * (q - x[i]) + c[i]
    return finite(result, "polynomial value")
