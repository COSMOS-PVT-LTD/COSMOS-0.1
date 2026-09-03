"""
COSMOS Rocket Propulsion Platform

Module: physics.contracts.numerics_port
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Numerics consumption port for physics inverses.

Description:
    Physics owns residual equations. Numerics owns root finding.
    When ``numerics.root_finding`` is not yet delivered, this port
    provides a *temporary* scalar bracketed root used only to invert
    already-posed physical residuals.

    See NUM-CONTRACT-ISSUE.md. This is not a numerics framework.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Protocol

from core.exceptions import InvalidInputError, SolverConvergenceError
from core.validation import validate_finite

__all__ = (
    "ScalarRootFinder",
    "bracketed_root",
)


class ScalarRootFinder(Protocol):
    """Numerics contract: find a root of a scalar residual on [a, b]."""

    def __call__(
        self,
        residual: Callable[[float], float],
        lower: float,
        upper: float,
        *,
        xtol: float = 1.0e-12,
        max_iter: int = 80,
    ) -> float:
        ...


def _fallback_bisection(
    residual: Callable[[float], float],
    lower: float,
    upper: float,
    *,
    xtol: float = 1.0e-12,
    max_iter: int = 80,
) -> float:
    """
    Temporary scalar bisection pending numerics delivery.

    NUM-CONTRACT-ISSUE: replace with ``numerics.root_finding.bisection``.
    """

    a = validate_finite(lower, "lower")
    b = validate_finite(upper, "upper")
    if a >= b:
        raise InvalidInputError("Root bracket requires lower < upper.")

    fa = residual(a)
    fb = residual(b)
    if not math.isfinite(fa) or not math.isfinite(fb):
        raise SolverConvergenceError("Residual is non-finite on the bracket.")
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    if fa * fb > 0.0:
        raise SolverConvergenceError(
            "Residual does not change sign on the supplied bracket."
        )

    left, right = a, b
    f_left = fa
    for _ in range(max_iter):
        mid = 0.5 * (left + right)
        f_mid = residual(mid)
        if not math.isfinite(f_mid):
            raise SolverConvergenceError("Residual became non-finite.")
        if f_mid == 0.0 or abs(right - left) <= xtol:
            return mid
        if f_left * f_mid < 0.0:
            right = mid
        else:
            left = mid
            f_left = f_mid

    raise SolverConvergenceError(
        f"Scalar root did not converge in {max_iter} iterations."
    )


def _load_numerics_finder() -> ScalarRootFinder:
    """Prefer numerics/ when present; otherwise use the documented fallback."""

    try:
        from numerics.root_finding.bisection import (  # type: ignore[import-not-found]
            find_root as numerics_root,
        )
    except ImportError:
        return _fallback_bisection
    return numerics_root


bracketed_root: ScalarRootFinder = _load_numerics_finder()
