"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.residuals
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral residuals foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from numpy.typing import ArrayLike

from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import finite, invalid, same_shape, vector


@dataclass(frozen=True, slots=True)
class ResidualHistory:
    """Append-only immutable finite nonnegative residual norm sequence."""

    values: tuple[float, ...] = ()

    def append(self, value: float) -> ResidualHistory:
        """Return a new history; do not mutate another solver's diagnostics."""
        residual = finite(value, "residual norm")
        if residual < 0:
            invalid("Residual norm must be nonnegative.")
        return ResidualHistory((*self.values, residual))


def difference_norm(left: ArrayLike, right: ArrayLike) -> float:
    """Norm of equal-shaped vector differences, never broadcast mismatched data."""
    a, b = vector(left), vector(right)
    same_shape(a, b)
    return l2(a - b)
