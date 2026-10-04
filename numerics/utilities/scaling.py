"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.scaling
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral scaling foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, failure, same_shape, vector


def scale(values: ArrayLike, scales: ArrayLike) -> FloatArray:
    """Divide by caller-supplied positive scales of equal shape; no hidden scales."""
    x, factors = vector(values), vector(scales, "scales")
    same_shape(x, factors)
    if np.any(factors <= 0):
        from numerics.utilities.numerical_checks import invalid

        invalid("All scales must be strictly positive.")
    with np.errstate(over="ignore", invalid="ignore"):
        result = x / factors
    if not np.isfinite(result).all():
        failure("Scaling overflowed.")
    return result
