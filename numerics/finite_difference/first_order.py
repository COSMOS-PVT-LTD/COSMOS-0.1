"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.first_order
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.first_order foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, invalid, positive, vector


def differentiate(values: ArrayLike, spacing: float, *, scheme: str = "central") -> FloatArray:
    """Uniform-grid first derivative; central uses second-order one-sided endpoints."""
    y,h = vector(values),positive(spacing)
    if len(y)<3 or scheme not in {"forward","backward","central"}:
        invalid("Derivative requires >=3 values and forward/backward/central scheme.")
    result = np.empty_like(y)
    if scheme == "forward":
        result[:-1] = np.diff(y)/h
        result[-1] = (y[-1]-y[-2])/h
    elif scheme == "backward":
        result[1:] = np.diff(y)/h
        result[0] = (y[1]-y[0])/h
    else:
        result[1:-1] = (y[2:]-y[:-2])/(2*h)
        result[0] = (-3*y[0]+4*y[1]-y[2])/(2*h)
        result[-1] = (3*y[-1]-4*y[-2]+y[-3])/(2*h)
    from numerics.utilities.numerical_checks import finite_output
    return finite_output(result)
