"""
COSMOS Rocket Propulsion Platform

Module: numerics.optimization.gradient_descent
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral optimization.gradient_descent foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    finite,
    invalid,
    positive,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances

ObjectiveFunction = Callable[[FloatArray], float]
GradientFunction = Callable[[FloatArray], FloatArray]


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    """Stationary-point result, never a proof of global optimality."""

    solution: NumericalResult[FloatArray]
    objective: float
    objective_history: tuple[float, ...]


def _objective(function: ObjectiveFunction, point: FloatArray) -> float:
    try:
        return finite(function(point.copy()), "objective")
    except (InvalidInputError, ArithmeticError, TypeError, ValueError) as exc:
        raise SolverConvergenceError("Invalid optimization objective.") from exc


def _gradient(function: GradientFunction, point: FloatArray) -> FloatArray:
    try:
        result = vector(function(point.copy()), "gradient")
    except (InvalidInputError, ArithmeticError, TypeError, ValueError) as exc:
        raise SolverConvergenceError("Invalid optimization gradient.") from exc
    if result.shape != point.shape:
        failure("Optimization gradient dimension mismatch.")
    return result


def _minimize(
    function: ObjectiveFunction,
    gradient: GradientFunction,
    initial: ArrayLike,
    *,
    method: str,
    step_size: float,
    tolerances: Tolerances,
) -> OptimizationResult:
    x = vector(initial)
    initial_step = positive(step_size)
    if method not in {"gradient-descent", "polak-ribiere-plus", "bfgs"}:
        invalid("Unknown deterministic optimization method.")
    f, g = _objective(function, x), _gradient(gradient, x)
    direction = -g
    inverse = np.eye(len(x))
    objectives, history = [f], [l2(g)]
    restarts = 0
    for iteration in range(tolerances.max_iterations + 1):
        if history[-1] <= tolerances.residual:
            x.setflags(write=False)
            result = NumericalResult(
                x,
                True,
                iteration,
                history[-1],
                TerminationReason.CONVERGED_ABSOLUTE,
                method,
                residual_history=tuple(history),
                diagnostics=(
                    (
                        "residual_semantics",
                        "gradient norm; stationary, not global optimum",
                    ),
                    ("direction_restarts", str(restarts)),
                ),
            )
            return OptimizationResult(result, f, tuple(objectives))
        if iteration == tolerances.max_iterations:
            break
        if method == "gradient-descent":
            direction = -g
        elif method == "bfgs":
            direction = -(inverse @ g)
        slope = float(g @ direction)
        if not np.isfinite(slope):
            failure("Optimization direction is nonfinite.")
        if slope >= 0:
            direction = -g
            slope = -float(g @ g)
            inverse = np.eye(len(x))
            restarts += 1
        alpha = initial_step
        for _ in range(50):
            candidate = x + alpha * direction
            candidate_f = _objective(function, candidate)
            if candidate_f <= f + 1e-4 * alpha * slope:
                break
            alpha *= 0.5
        else:
            failure("Optimization Armijo line search exhausted trial budget.")
        if np.array_equal(candidate, x):
            failure("Optimization stagnated before gradient convergence.")
        new_g = _gradient(gradient, candidate)
        if method == "polak-ribiere-plus":
            beta = max(0.0, float(new_g @ (new_g - g)) / float(g @ g))
            direction = -new_g + beta * direction
        elif method == "bfgs":
            s, y = candidate - x, new_g - g
            curvature = float(y @ s)
            if curvature > 1e-12 * l2(s) * l2(y):
                rho = 1 / curvature
                left = np.eye(len(x)) - rho * np.outer(s, y)
                inverse = left @ inverse @ left.T + rho * np.outer(s, s)
            else:
                inverse = np.eye(len(x))
                restarts += 1
            if not np.isfinite(inverse).all():
                failure("BFGS inverse update is nonfinite.")
        x, f, g = candidate, candidate_f, new_g
        objectives.append(f)
        history.append(l2(g))
    failure("Optimization exhausted iterations without gradient convergence.")


def minimize(
    function: ObjectiveFunction,
    gradient: GradientFunction,
    initial: ArrayLike,
    *,
    step_size: float = 1.0,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> OptimizationResult:
    """Gradient descent with mandatory Armijo descent; explicit analytic/AD gradient."""
    return _minimize(
        function,
        gradient,
        initial,
        method="gradient-descent",
        step_size=step_size,
        tolerances=tolerances,
    )
