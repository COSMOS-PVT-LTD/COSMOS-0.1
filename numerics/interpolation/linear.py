"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.linear
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.linear foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import (
    FloatArray,
    finite,
    grid,
    invalid,
    same_shape,
    vector,
)


def _data(nodes: ArrayLike, values: ArrayLike) -> tuple[FloatArray, FloatArray]:
    x, y = grid(nodes), vector(values)
    same_shape(x, y)
    return x, y

def _query(x: FloatArray, query: float, extrapolate: bool) -> tuple[float, int]:
    q = finite(query, "query")
    if not extrapolate and not x[0] <= q <= x[-1]:
        invalid("Extrapolation is disabled.")
    return q, int(np.clip(np.searchsorted(x, q) - 1, 0, len(x) - 2))

def interpolate(nodes: ArrayLike, values: ArrayLike, query: float, *, extrapolate: bool = False) -> float:
    """Piecewise linear; ordered unique nodes, explicit endpoint extrapolation."""
    x, y = _data(nodes, values)
    q, i = _query(x, query, extrapolate)
    w = (q - x[i]) / (x[i+1] - x[i])
    return finite(float((1-w)*y[i] + w*y[i+1]), "interpolated value")
