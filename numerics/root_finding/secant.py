"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.secant
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified secant scalar root algorithm.
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
)
from numerics.utilities.tolerances import ROOT_TOLERANCES, Tolerances


def _secant_candidate(a: float, b: float, fa: float, fb: float) -> float:
    scale = max(abs(fa), abs(fb))
    if scale == 0:
        return b
    f, g = fa / scale, fb / scale
    if f == g:
        failure("STAGNATION: secant residuals are identical.")
    result = a * (g / (g - f)) - b * (f / (g - f))
    if not math.isfinite(result):
        failure("DIVERGENCE: secant candidate is non-finite.")
    return result


def solve(residual: ScalarFunction, x0: float, x1: float, *,
          policy: Tolerances = ROOT_TOLERANCES) -> NumericalResult[float]:
    """Unbracketed secant; distinct starts and locally regular residual required."""
    a, b = finite(x0, "x0"), finite(x1, "x1")
    if a == b:
        invalid("Secant requires distinct starting points.")
    fa, fb = evaluate(residual, a), evaluate(residual, b)
    history = [abs(fb)]
    if fa == 0 or fb == 0:
        return _result(a if fa == 0 else b, 0.0, 0, "secant", history, 0.0)
    for iteration in range(1, policy.max_iterations + 1):
        x = _secant_candidate(a, b, fa, fb)
        fx = evaluate(residual, x)
        history.append(abs(fx))
        if fx == 0:
            return _result(x, fx, iteration, "secant", history, 0.0)
        if abs(x - b) <= policy.threshold(x) and abs(fx) <= policy.residual:
            return _result(x, fx, iteration, "secant", history)
        if x == b or stagnated(tuple(history), policy):
            failure("STAGNATION: secant failed to improve the residual.")
        a, fa, b, fb = b, fb, x, fx
    failure("MAX_ITERATIONS: secant exhausted its iteration budget.")
