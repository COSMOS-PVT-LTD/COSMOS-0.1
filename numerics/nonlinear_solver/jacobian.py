"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.jacobian
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.jacobian foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    matrix,
    same_shape,
    vector,
)

ResidualFunction = Callable[[FloatArray], FloatArray]
JacobianFunction = Callable[[FloatArray], FloatArray]


def evaluate_residual(function: ResidualFunction, state: FloatArray) -> FloatArray:
    """Domain/arithmetic/nonfinite callback failures are solver failures."""
    try:
        value = vector(function(state.copy()), "residual")
    except (InvalidInputError, ArithmeticError, ValueError, TypeError) as exc:
        raise SolverConvergenceError("Invalid nonlinear residual evaluation.") from exc
    same_shape(value, state)
    return value


def evaluate_jacobian(function: JacobianFunction, state: FloatArray) -> FloatArray:
    try:
        value = matrix(function(state.copy()), "Jacobian", square=True)
    except (InvalidInputError, ArithmeticError, ValueError, TypeError) as exc:
        raise SolverConvergenceError("Invalid Jacobian evaluation.") from exc
    if value.shape != (len(state), len(state)):
        failure("Jacobian dimension does not match state.")
    return value
