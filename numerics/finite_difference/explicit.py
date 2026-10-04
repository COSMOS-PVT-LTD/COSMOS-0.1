"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.explicit
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.explicit foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.stability import require_stable
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    invalid,
    matrix,
    positive,
    same_shape,
    vector,
)


def update(state: ArrayLike, operator: ArrayLike, source: ArrayLike, time_step: float, *,
           stability_limit: float) -> FloatArray:
    """Real generic forward-Euler linear update; stability bound is mandatory."""
    y,a,s,dt = vector(state),matrix(operator,square=True),vector(source),positive(time_step)
    same_shape(y,s)
    if a.shape[0] != len(y):
        invalid("Linear update dimensions mismatch.")
    require_stable(dt,stability_limit)
    result = y+dt*(a@y+s)
    if not np.isfinite(result).all():
        failure("Explicit update is nonfinite.")
    return result
