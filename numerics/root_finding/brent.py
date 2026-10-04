"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.brent
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified brent scalar root algorithm.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

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


def solve(residual: ScalarFunction, lower: float, upper: float, *,
          policy: Tolerances = ROOT_TOLERANCES) -> NumericalResult[float]:
    """Safeguarded Brent-style inverse-quadratic/secant/bracket hybrid.

    Not an optimized canonical Brent transcription: every even iteration is a
    bracket midpoint; interpolation is accepted only in the inner 80% of the
    bracket. Interval and residual tolerances must both pass; a discontinuous
    jump is not accepted solely because its bracket collapses.
    Continuity and a sign-changing bracket are required.
    """
    a, b, fa, fb = _bracket(residual, lower, upper)
    c, fc = a, fa
    history = [min(abs(fa), abs(fb))]
    if fa == 0 or fb == 0:
        return _result(a if fa == 0 else b, 0.0, 0, "brent-style", history, 0.0, (a, b))
    for iteration in range(1, policy.max_iterations + 1):
        mid = _midpoint(a, b)
        error = _half_width(a, b)
        if error <= policy.threshold(mid):
            fm = evaluate(residual, mid)
            history.append(abs(fm))
            if abs(fm) <= policy.residual:
                return _result(mid, fm, iteration, "brent-style", history, error, (a, b))
        x = mid
        if iteration % 2:
            fscale = max(abs(fa), abs(fb), abs(fc))
            f, g, h = fa / fscale, fb / fscale, fc / fscale
            if len({f, g, h}) == 3:
                denominators = ((f - g) * (f - h), (g - f) * (g - h), (h - f) * (h - g))
                if all(denominators):
                    proposed = (a * (g * h / denominators[0]) +
                                b * (f * h / denominators[1]) +
                                c * (f * g / denominators[2]))
                else:
                    proposed = mid
            else:
                proposed = _secant_candidate(a, b, fa, fb)
            if math.isfinite(proposed) and .9 * a + .1 * b < proposed < .1 * a + .9 * b:
                x = proposed
        if x == a or x == b:
            failure("STAGNATION: Brent-style bracket reached floating-point spacing.")
        fx = evaluate(residual, x)
        history.append(abs(fx))
        if fx == 0:
            return _result(x, fx, iteration, "brent-style", history, 0.0, (a, b))
        if _same_sign(fa, fx):
            c, fc, a, fa = a, fa, x, fx
        else:
            c, fc, b, fb = b, fb, x, fx
    failure("MAX_ITERATIONS: Brent-style iteration exhausted.")
