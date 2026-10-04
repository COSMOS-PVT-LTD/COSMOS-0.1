"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.trapezoidal
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.trapezoidal foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numerics.utilities.numerical_checks import (
    ScalarFunction,
    count,
    evaluate,
    failure,
    finite,
    invalid,
    scalar_output,
)


def _interval(lower: float, upper: float) -> tuple[float, float]:
    a, b = finite(lower), finite(upper)
    if b <= a:
        invalid("Integration requires finite increasing endpoints.")
    return a, b


def integrate(
    function: ScalarFunction, lower: float, upper: float, *, intervals: int = 100
) -> float:
    """Composite trapezoid with explicit positive interval count."""
    a, b = _interval(lower, upper)
    n = count(intervals)
    h = (b - a) / n
    try:
        value = h * (
            0.5 * evaluate(function, a)
            + 0.5 * evaluate(function, b)
            + math.fsum(evaluate(function, a + i * h) for i in range(1, n))
        )
    except OverflowError:
        failure("Trapezoid accumulation overflowed; normalize integrand.")
    return scalar_output(value)
