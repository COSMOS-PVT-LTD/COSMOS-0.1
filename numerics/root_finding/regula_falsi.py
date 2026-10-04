"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.regula_falsi
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified regula_falsi scalar root algorithm.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.root_finding.bisection import (
    _bracket,
    _half_width,
    _midpoint,
    _result,
    _same_sign,
)
from numerics.root_finding.secant import _secant_candidate
from numerics.utilities.convergence import NumericalResult
from numerics.utilities.numerical_checks import ScalarFunction, evaluate, failure
from numerics.utilities.tolerances import ROOT_TOLERANCES, Tolerances


def solve(
    residual: ScalarFunction,
    lower: float,
    upper: float,
    *,
    policy: Tolerances = ROOT_TOLERANCES,
) -> NumericalResult[float]:
    """Classical false position for continuous bracketed residuals; may stagnate.

    No Illinois weighting or hidden method switching. Success requires an
    exact root, a small bracket, or small step AND residual. In the latter
    case no root-location error bound is claimed.
    """
    a, b, fa, fb = _bracket(residual, lower, upper)
    history = [min(abs(fa), abs(fb))]
    previous: float | None = None
    if fa == 0 or fb == 0:
        return _result(
            a if fa == 0 else b, 0.0, 0, "regula-falsi", history, 0.0, (a, b)
        )
    for iteration in range(1, policy.max_iterations + 1):
        mid = _midpoint(a, b)
        error = _half_width(a, b)
        if error <= policy.threshold(mid):
            fm = evaluate(residual, mid)
            history.append(abs(fm))
            return _result(mid, fm, iteration, "regula-falsi", history, error, (a, b))
        x = _secant_candidate(a, b, fa, fb)
        fx = evaluate(residual, x)
        history.append(abs(fx))
        if fx == 0:
            return _result(x, fx, iteration, "regula-falsi", history, 0.0, (a, b))
        if not a < x < b or x == previous:
            failure(
                "STAGNATION: false-position endpoint is fixed at floating-point resolution."
            )
        if (
            previous is not None
            and abs(x - previous) <= policy.threshold(x)
            and abs(fx) <= policy.residual
        ):
            return _result(x, fx, iteration, "regula-falsi", history, bracket=(a, b))
        previous = x
        if _same_sign(fa, fx):
            a, fa = x, fx
        else:
            b, fb = x, fx
    failure("MAX_ITERATIONS: false position exhausted its iteration budget.")
