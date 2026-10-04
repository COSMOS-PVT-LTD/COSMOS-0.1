"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.line_search
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.line_search foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numerics.nonlinear_solver.jacobian import ResidualFunction, evaluate_residual
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import (
    FloatArray,
    count,
    failure,
    finite,
    invalid,
    same_shape,
)


def backtrack(
    function: ResidualFunction,
    state: FloatArray,
    direction: FloatArray,
    *,
    max_trials: int = 40,
    sufficient_decrease: float = 1e-4,
) -> tuple[FloatArray, FloatArray, float]:
    """Residual-norm merit backtracking; reject nonfinite trial rather than switch solvers."""
    same_shape(state, direction)
    c = finite(sufficient_decrease)
    if not 0 < c < 0.5:
        invalid("Sufficient decrease must be between zero and one half.")
    norm = l2(evaluate_residual(function, state))
    alpha = 1.0
    for _ in range(count(max_trials)):
        candidate = state + alpha * direction
        value = evaluate_residual(function, candidate)
        if l2(value) <= math.sqrt(1 - 2 * c * alpha) * norm:
            return candidate, value, alpha
        alpha *= 0.5
    failure("Residual line search failed sufficient decrease.")
