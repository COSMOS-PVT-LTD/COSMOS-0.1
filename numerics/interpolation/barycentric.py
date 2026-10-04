"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.barycentric
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.barycentric foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.interpolation.linear import _data, _query
from numerics.utilities.numerical_checks import failure, finite


def interpolate(
    nodes: ArrayLike, values: ArrayLike, query: float, *, extrapolate: bool = False
) -> float:
    """Barycentric Lagrange formula; modest well-scaled node sets only."""
    x, y = _data(nodes, values)
    q, _ = _query(x, query, extrapolate)
    exact = np.flatnonzero(x == q)
    if exact.size:
        return float(y[exact[0]])
    weights = np.empty(len(x))
    for i in range(len(x)):
        product = float(np.prod(x[i] - np.delete(x, i)))
        if product == 0 or not np.isfinite(product):
            failure("Barycentric weights are unrepresentable; rescale nodes.")
        weights[i] = 1 / product
    terms = weights / (q - x)
    denominator = float(np.sum(terms))
    if denominator == 0 or not np.isfinite(denominator):
        failure("Barycentric evaluation is ill-conditioned.")
    return finite(float(np.dot(terms, y) / denominator), "polynomial value")
