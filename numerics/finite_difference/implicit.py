"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.implicit
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.implicit foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.linear_algebra.solvers import solve_linear
from numerics.utilities.numerical_checks import (
    FloatArray,
    invalid,
    matrix,
    positive,
    same_shape,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def update(
    state: ArrayLike,
    operator: ArrayLike,
    source: ArrayLike,
    time_step: float,
    *,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> FloatArray:
    """Real backward-Euler linear update; original discrete equation checked by LU."""
    y, a, s, dt = (
        vector(state),
        matrix(operator, square=True),
        vector(source),
        positive(time_step),
    )
    same_shape(y, s)
    if a.shape[0] != len(y):
        invalid("Linear update dimensions mismatch.")
    return solve_linear(np.eye(len(y)) - dt * a, y + dt * s, policy=tolerances).value
