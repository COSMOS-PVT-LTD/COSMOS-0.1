"""
COSMOS Rocket Propulsion Platform

Module: numerics.optimization.conjugate_gradient
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral optimization.conjugate_gradient foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.optimization.gradient_descent import (
    GradientFunction,
    ObjectiveFunction,
    OptimizationResult,
    _minimize,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def minimize(
    function: ObjectiveFunction,
    gradient: GradientFunction,
    initial: ArrayLike,
    *,
    step_size: float = 1.0,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> OptimizationResult:
    """Nonlinear Polak-Ribiere+ CG with explicit non-descent restart and Armijo."""
    return _minimize(
        function,
        gradient,
        initial,
        method="polak-ribiere-plus",
        step_size=step_size,
        tolerances=tolerances,
    )
