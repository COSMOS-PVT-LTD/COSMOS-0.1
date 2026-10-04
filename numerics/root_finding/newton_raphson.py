"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.newton_raphson
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified newton_raphson scalar root algorithm.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numerics.root_finding.bisection import _result
from numerics.utilities.convergence import NumericalResult, stagnated
from numerics.utilities.numerical_checks import (
    ScalarFunction,
    evaluate,
    failure,
    finite,
    invalid,
    positive,
)
from numerics.utilities.tolerances import ROOT_TOLERANCES, Tolerances


def numerical_derivative(residual: ScalarFunction, x: float, *, step: float) -> float:
    """Centered finite difference, explicitly named and caller-scaled, not AD."""
    h = positive(step, "numerical derivative step")
    point = finite(x)
    if point + h == point or point - h == point:
        invalid("Derivative step is below floating-point spacing.")
    value = (evaluate(residual, point + h) - evaluate(residual, point - h)) / (2 * h)
    if not math.isfinite(value):
        failure("Newton derivative is non-finite.")
    return value


def solve(residual: ScalarFunction, x0: float, *, derivative: ScalarFunction | None = None,
          numerical_step: float | None = None,
          policy: Tolerances = ROOT_TOLERANCES) -> NumericalResult[float]:
    """Newton iteration with an explicit analytic OR explicit finite-difference derivative.

    Requires a differentiable residual and suitable initial guess. This method
    does not silently bracket, line-search or switch algorithms.
    """
    if (derivative is None) == (numerical_step is None):
        invalid("Provide exactly one derivative callback or numerical_step.")
    if numerical_step is not None:
        positive(numerical_step, "numerical_step")
    x = finite(x0, "x0")
    fx = evaluate(residual, x)
    history = [abs(fx)]
    if fx == 0:
        return _result(x, fx, 0, "newton-raphson", history, 0.0)
    for iteration in range(1, policy.max_iterations + 1):
        if derivative is not None:
            df = evaluate(derivative, x)
        else:
            assert numerical_step is not None  # validated mutually exclusive mode
            df = numerical_derivative(residual, x, step=numerical_step)
        if df == 0:
            failure("Newton derivative is zero.")
        candidate = x - fx / df
        if not math.isfinite(candidate):
            failure("DIVERGENCE: Newton iterate is non-finite.")
        fc = evaluate(residual, candidate)
        history.append(abs(fc))
        if fc == 0:
            return _result(candidate, fc, iteration, "newton-raphson", history, 0.0)
        if abs(fc) <= policy.residual and abs(candidate - x) <= policy.threshold(candidate):
            return _result(candidate, fc, iteration, "newton-raphson", history)
        if candidate == x:
            failure("STAGNATION: Newton step cannot improve the residual.")
        if stagnated(tuple(history), policy):
            failure("STAGNATION: Newton residual is unchanged.")
        x, fx = candidate, fc
    failure("MAX_ITERATIONS: Newton exhausted its iteration budget.")
