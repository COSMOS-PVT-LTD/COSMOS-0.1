"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.monte_carlo
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.monte_carlo foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from numerics.integration.trapezoidal import _interval
from numerics.random.random_generators import generator
from numerics.utilities.numerical_checks import (
    ScalarFunction,
    count,
    evaluate,
    scalar_output,
)


@dataclass(frozen=True, slots=True)
class MonteCarloEstimate:
    """Fixed budget estimate: standard error is statistical, not a certified bound."""

    value: float
    standard_error: float
    samples: int
    seed: int


def integrate(
    function: ScalarFunction, lower: float, upper: float, *, samples: int, seed: int
) -> MonteCarloEstimate:
    a, b = _interval(lower, upper)
    n, s = count(samples, minimum=2), count(seed, "seed", minimum=0)
    points = generator(s).uniform(a, b, n)
    values = np.array([evaluate(function, float(x)) for x in points])
    with np.errstate(over="ignore", invalid="ignore"):
        value = scalar_output(float((b - a) * values.mean()))
        error = scalar_output(float((b - a) * values.std(ddof=1) / math.sqrt(n)))
    return MonteCarloEstimate(value, error, n, s)
