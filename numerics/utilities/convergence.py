"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.convergence
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral convergence foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from core.logger import get_logger
from numerics.utilities.numerical_checks import finite, invalid
from numerics.utilities.tolerances import Tolerances

T = TypeVar("T")


class TerminationReason(str, Enum):
    """Machine-readable numerical termination; no physical validity semantics."""

    CONVERGED_ABSOLUTE = "CONVERGED_ABSOLUTE"
    CONVERGED_RELATIVE = "CONVERGED_RELATIVE"
    EXACT_ROOT = "EXACT_ROOT"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    INVALID_BRACKET = "INVALID_BRACKET"
    NONFINITE_RESIDUAL = "NONFINITE_RESIDUAL"
    STAGNATION = "STAGNATION"
    DIVERGENCE = "DIVERGENCE"
    SINGULAR_SYSTEM = "SINGULAR_SYSTEM"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True, slots=True)
class NumericalResult(Generic[T]):
    """Numerical-only result, explicit termination and immutable diagnostic history."""

    value: T
    converged: bool
    iterations: int
    residual_norm: float
    termination_reason: TerminationReason
    method: str
    absolute_error_estimate: float | None = None
    relative_error_estimate: float | None = None
    residual_history: tuple[float, ...] = ()
    diagnostics: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.iterations < 0 or finite(self.residual_norm, "residual_norm") < 0:
            invalid("Iterations and residual norm must be nonnegative.")
        success = {TerminationReason.CONVERGED_ABSOLUTE, TerminationReason.CONVERGED_RELATIVE,
                   TerminationReason.EXACT_ROOT}
        if self.converged != (self.termination_reason in success):
            invalid("Convergence flag and termination reason disagree.")
        for error in (self.absolute_error_estimate, self.relative_error_estimate):
            if error is not None and finite(error, "error estimate") < 0:
                invalid("Error estimates must be nonnegative.")
        get_logger("numerics").debug(
            "%s iterations=%d residual=%g reason=%s",
            self.method, self.iterations, self.residual_norm, self.termination_reason.value,
        )


def stagnated(history: tuple[float, ...], tolerances: Tolerances) -> bool:
    """Detect repeated residual norms without inventing convergence."""
    tail = history[-tolerances.stagnation_window:]
    return len(tail) == tolerances.stagnation_window and max(tail) == min(tail)


def observed_order(coarse: float, fine: float, ratio: float = 2.0) -> float:
    """Return log(error_coarse/error_fine)/log(refinement_ratio)."""
    import math

    from numerics.utilities.numerical_checks import positive

    a, b, r = positive(coarse, "coarse error"), positive(fine, "fine error"), positive(ratio, "ratio")
    if r <= 1:
        invalid("Refinement ratio must exceed one.")
    return math.log(a / b) / math.log(r)
