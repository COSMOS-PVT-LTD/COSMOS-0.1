"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.adaptive
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.adaptive foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.integration.trapezoidal import _interval
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.numerical_checks import ScalarFunction, evaluate, failure
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def integrate(
    function: ScalarFunction,
    lower: float,
    upper: float,
    *,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> NumericalResult[float]:
    """Adaptive Simpson; local error sums, explicit split budget; smooth integrands."""
    a, b = _interval(lower, upper)
    middle = (a + b) / 2
    fa, fm, fb = (
        evaluate(function, a),
        evaluate(function, middle),
        evaluate(function, b),
    )
    initial = (b - a) * (fa + 4 * fm + fb) / 6
    target = tolerances.threshold(initial)
    stack = [(a, b, fa, fm, fb, initial, target)]
    total = error_sum = 0.0
    history: list[float] = []
    iterations = 0
    while stack:
        if iterations >= tolerances.max_iterations:
            failure("Adaptive Simpson exhausted split budget.")
        lo, hi, fl, fc, fr, coarse, budget = stack.pop()
        mid = (lo + hi) / 2
        ql, qr = (lo + mid) / 2, (mid + hi) / 2
        if ql == lo or qr == hi:
            failure("Adaptive Simpson reached floating-point spacing.")
        fql, fqr = evaluate(function, ql), evaluate(function, qr)
        left, right = (
            (mid - lo) * (fl + 4 * fql + fc) / 6,
            (hi - mid) * (fc + 4 * fqr + fr) / 6,
        )
        error = abs(left + right - coarse) / 15
        iterations += 1
        history.append(error)
        if error <= budget:
            total += left + right + (left + right - coarse) / 15
            error_sum += error
        else:
            stack.extend(
                [
                    (mid, hi, fc, fqr, fr, right, budget / 2),
                    (lo, mid, fl, fql, fc, left, budget / 2),
                ]
            )
    if error_sum > tolerances.threshold(total):
        failure("Adaptive Simpson aggregate error exceeds final tolerance.")
    return NumericalResult(
        total,
        True,
        iterations,
        error_sum,
        TerminationReason.CONVERGED_ABSOLUTE,
        "adaptive-simpson",
        absolute_error_estimate=error_sum,
        residual_history=tuple(history),
        diagnostics=(
            (
                "error_semantics",
                "smooth-integrand asymptotic estimate, not rigorous bound",
            ),
        ),
    )
