"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.romberg
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.romberg foundation.
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
    """Trapezoid Richardson tableau, bounded to 20 levels to bound work."""
    a, b = _interval(lower, upper)
    row = [(b - a) * (evaluate(function, a) + evaluate(function, b)) / 2]
    history: list[float] = []
    for level in range(1, min(tolerances.max_iterations, 20) + 1):
        n, h = 2**level, (b - a) / 2**level
        new = [
            row[0] / 2 + h * sum(evaluate(function, a + i * h) for i in range(1, n, 2))
        ]
        for j in range(1, level + 1):
            new.append(new[-1] + (new[-1] - row[j - 1]) / (4**j - 1))
        error = abs(new[-1] - row[-1])
        history.append(error)
        if error <= tolerances.threshold(new[-1]):
            return NumericalResult(
                new[-1],
                True,
                level,
                error,
                TerminationReason.CONVERGED_ABSOLUTE,
                "romberg",
                absolute_error_estimate=error,
                residual_history=tuple(history),
            )
        row = new
    failure("Romberg exhausted refinement budget.")
