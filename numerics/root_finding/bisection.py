"""
COSMOS Rocket Propulsion Platform

Module: numerics.root_finding.bisection
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Qualified bisection scalar root algorithm.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.numerical_checks import (
    ScalarFunction,
    evaluate,
    failure,
    finite,
    invalid,
)
from numerics.utilities.tolerances import ROOT_TOLERANCES, Tolerances


def _same_sign(left: float, right: float) -> bool:
    return (left > 0) == (right > 0)


def _midpoint(left: float, right: float) -> float:
    return left / 2.0 + right / 2.0


def _half_width(left: float, right: float) -> float:
    return abs(right / 2.0 - left / 2.0)


def _bracket(
    residual: ScalarFunction, lower: float, upper: float
) -> tuple[float, float, float, float]:
    a, b = finite(lower, "lower"), finite(upper, "upper")
    if a >= b:
        invalid("Root bracket requires lower < upper.")
    fa, fb = evaluate(residual, a), evaluate(residual, b)
    if fa != 0 and fb != 0 and _same_sign(fa, fb):
        invalid("Residual does not change sign on the supplied bracket.")
    return a, b, fa, fb


def _result(
    x: float,
    fx: float,
    iterations: int,
    method: str,
    history: list[float],
    error: float | None = None,
    bracket: tuple[float, float] | None = None,
) -> NumericalResult[float]:
    reason = (
        TerminationReason.EXACT_ROOT
        if fx == 0
        else TerminationReason.CONVERGED_ABSOLUTE
    )
    diagnostics = (
        ()
        if bracket is None
        else (
            ("bracket_lower", repr(min(bracket))),
            ("bracket_upper", repr(max(bracket))),
        )
    )
    return NumericalResult(
        x,
        True,
        iterations,
        abs(fx),
        reason,
        method,
        absolute_error_estimate=error,
        residual_history=tuple(history),
        diagnostics=diagnostics,
    )


def solve(
    residual: ScalarFunction,
    lower: float,
    upper: float,
    *,
    policy: Tolerances = ROOT_TOLERANCES,
) -> NumericalResult[float]:
    """Bisect a continuous finite residual on a sign-changing closed bracket.

    Convergence means an exact residual zero or a bracket midpoint whose
    half-width meets the solution tolerance. No derivative/residual scaling
    assumption is made; residual history is reported independently.
    """
    a, b, fa, fb = _bracket(residual, lower, upper)
    history = [min(abs(fa), abs(fb))]
    if fa == 0 or fb == 0:
        return _result(a if fa == 0 else b, 0.0, 0, "bisection", history, 0.0, (a, b))
    for iteration in range(1, policy.max_iterations + 1):
        mid = _midpoint(a, b)
        fm = evaluate(residual, mid)
        history.append(abs(fm))
        error = _half_width(a, b)
        if fm == 0 or error <= policy.threshold(mid):
            return _result(
                mid,
                fm,
                iteration,
                "bisection",
                history,
                0.0 if fm == 0 else error,
                (a, b),
            )
        if mid == a or mid == b:
            failure("STAGNATION: bracket resolution is below floating-point spacing.")
        if _same_sign(fa, fm):
            a, fa = mid, fm
        else:
            b = mid
    failure(
        f"MAX_ITERATIONS: bisection did not converge in {policy.max_iterations} iterations."
    )


def find_root(
    residual: ScalarFunction,
    lower: float,
    upper: float,
    *,
    xtol: float = ROOT_TOLERANCES.absolute,
    max_iter: int = ROOT_TOLERANCES.max_iterations,
) -> float:
    """Existing Physics scalar compatibility contract; typed failures propagate."""
    policy = Tolerances(
        absolute=xtol,
        relative=0.0,
        residual=ROOT_TOLERANCES.residual,
        max_iterations=max_iter,
    )
    return solve(residual, lower, upper, policy=policy).value
