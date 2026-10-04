"""
COSMOS Rocket Propulsion Platform

Module: physics.contracts.numerics_port
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Mandatory qualified Numerics consumption boundary for Physics inverses.

Description:
    Physics owns physical residuals; Numerics owns algorithms.
    Missing Numerics fails import. No alternate or temporary solver is present.
    See NUM-CONTRACT-ISSUE.md for retirement evidence and release acceptance.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from numerics.root_finding.bisection import find_root

__all__ = ("ScalarRootFinder", "bracketed_root")


class ScalarRootFinder(Protocol):
    """Scalar compatibility contract; invalid input and solver errors propagate."""

    def __call__(
        self,
        residual: Callable[[float], float],
        lower: float,
        upper: float,
        *,
        xtol: float = 1.0e-12,
        max_iter: int = 80,
    ) -> float: ...


bracketed_root: ScalarRootFinder = find_root
