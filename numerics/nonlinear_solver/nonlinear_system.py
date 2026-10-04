"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.nonlinear_system
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.nonlinear_system foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.linear_algebra.solvers import solve_linear
from numerics.nonlinear_solver.convergence import residual_converged
from numerics.nonlinear_solver.jacobian import (
    JacobianFunction,
    ResidualFunction,
    evaluate_jacobian,
    evaluate_residual,
)
from numerics.nonlinear_solver.line_search import backtrack
from numerics.nonlinear_solver.numerical_jacobian import jacobian as numerical_jacobian
from numerics.nonlinear_solver.trust_region import bounded_step
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    invalid,
    positive,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(function: ResidualFunction, initial: ArrayLike, *, jacobian: JacobianFunction | None = None,
          numerical_step: float | None = None, trust_radius: float | None = None,
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> NumericalResult[FloatArray]:
    """Newton plus mandatory residual backtracking; optional explicit norm cap."""
    if (jacobian is None) == (numerical_step is None):
        invalid("Provide exactly one analytic Jacobian or explicit numerical step.")
    if numerical_step is not None:
        positive(numerical_step)
    if trust_radius is not None:
        positive(trust_radius)
    x = vector(initial)
    value = evaluate_residual(function,x)
    history = [l2(value)]
    for iteration in range(tolerances.max_iterations+1):
        if residual_converged(value,tolerances):
            x.setflags(write=False)
            return NumericalResult(x,True,iteration,history[-1],TerminationReason.CONVERGED_ABSOLUTE,
                                   "newton-system-backtracking",residual_history=tuple(history))
        if iteration == tolerances.max_iterations:
            break
        if jacobian is not None:
            j = evaluate_jacobian(jacobian,x)
        else:
            assert numerical_step is not None
            j = numerical_jacobian(function,x,step=numerical_step)
        direction = solve_linear(j,-value,policy=tolerances).value
        if trust_radius is not None:
            direction = bounded_step(direction,trust_radius)
        candidate, value, _ = backtrack(function,x,direction)
        if np.array_equal(candidate,x):
            failure("Nonlinear solve stagnated without satisfying residual tolerance.")
        x = candidate
        history.append(l2(value))
    failure("Nonlinear Newton solve exhausted iteration budget.")
