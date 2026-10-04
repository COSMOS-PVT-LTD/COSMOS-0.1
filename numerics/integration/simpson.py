"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.simpson
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.simpson foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numerics.integration.trapezoidal import _interval
from numerics.utilities.numerical_checks import (
    ScalarFunction,
    count,
    evaluate,
    finite,
    invalid,
)


def integrate(function: ScalarFunction, lower: float, upper: float, *, intervals: int = 100) -> float:
    """Composite Simpson 1/3 requires a positive even number of intervals."""
    a, b = _interval(lower, upper)
    n = count(intervals, minimum=2)
    if n % 2:
        invalid("Simpson requires an even interval count.")
    h = (b-a)/n
    return finite(h/3*(evaluate(function,a)+evaluate(function,b)+
                      math.fsum((4 if i%2 else 2)*evaluate(function,a+i*h) for i in range(1,n))))
