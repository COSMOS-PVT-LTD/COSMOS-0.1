"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.fixed_point
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified fixed_point scalar root algorithm.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numerics.root_finding.bisection import _result
from numerics.utilities.convergence import NumericalResult
from numerics.utilities.numerical_checks import (
    ScalarFunction,
    evaluate,
    failure,
    finite,
    invalid,
)
from numerics.utilities.tolerances import ROOT_TOLERANCES, Tolerances


def solve(
    mapping: ScalarFunction,
    x0: float,
    *,
    contraction_bound: float,
    policy: Tolerances = ROOT_TOLERANCES,
) -> NumericalResult[float]:
    """Iterate a caller-qualified contraction g, |g'|<=q<1 on the invariant domain.

    A posteriori error is |g(x)-x|/(1-q). Observed violations of the
    declared contraction are rejected; this local check is not a proof of q.
    """
    q = finite(contraction_bound, "contraction_bound")
    if not 0 <= q < 1:
        invalid("A contraction_bound in [0, 1) is required.")
    x = finite(x0, "x0")
    history: list[float] = []
    for iteration in range(1, policy.max_iterations + 1):
        candidate = evaluate(mapping, x)
        g_next = evaluate(mapping, candidate)
        residual = g_next - candidate
        step = abs(candidate - x)
        if not math.isfinite(residual) or not math.isfinite(step):
            failure("DIVERGENCE: fixed-point residual/step is non-finite.")
        history.append(abs(residual))
        if abs(residual) > q * step + 2 * math.ulp(candidate):
            failure("DIVERGENCE: observed mapping violates contraction_bound.")
        error = abs(residual) / (1 - q)
        if abs(residual) <= policy.residual and error <= policy.threshold(candidate):
            return _result(
                candidate, residual, iteration, "fixed-point", history, error
            )
        if candidate == x:
            failure("STAGNATION: fixed-point iteration cannot progress.")
        x = candidate
    failure("MAX_ITERATIONS: fixed-point iteration exhausted.")
