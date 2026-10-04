"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.norms
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral norms foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import failure, vector


def l1(values: ArrayLike) -> float:
    """Sum absolute values with compensated summation; finite rank-one input."""
    checked = vector(values)
    try:
        return math.fsum(abs(float(v)) for v in checked)
    except OverflowError:
        failure("L1 norm overflowed.")


def l2(values: ArrayLike) -> float:
    """Euclidean norm using overflow-resistant hypot accumulation."""
    result = math.hypot(*(float(v) for v in vector(values)))
    if not math.isfinite(result):
        failure("L2 norm overflowed.")
    return result


def linfinity(values: ArrayLike) -> float:
    """Maximum absolute entry of a nonempty finite vector."""
    return max(abs(float(v)) for v in vector(values))
