"""
COSMOS Rocket Propulsion Platform

Module: numerics.optimization.bfgs
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral optimization.bfgs foundation.
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


def minimize(function: ObjectiveFunction, gradient: GradientFunction, initial: ArrayLike, *,
             step_size: float = 1., tolerances: Tolerances = DEFAULT_TOLERANCES) -> OptimizationResult:
    """Inverse BFGS, explicit curvature reset and Armijo descent; unconstrained only."""
    return _minimize(function,gradient,initial,method="bfgs",step_size=step_size,tolerances=tolerances)
