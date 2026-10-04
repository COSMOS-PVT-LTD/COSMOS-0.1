"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.implicit
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.implicit foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.nonlinear_solver.nonlinear_system import solve
from numerics.ode.euler import RHSFunction, _evaluate, _input
from numerics.utilities.numerical_checks import FloatArray
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def step(
    function: RHSFunction,
    time: float,
    state: ArrayLike,
    step_size: float,
    *,
    numerical_step: float,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> FloatArray:
    """Real backward Euler via safeguarded Newton; explicit FD Jacobian perturbation."""
    t, y, h = _input(time, state, step_size)

    def residual(candidate: FloatArray) -> FloatArray:
        return candidate - y - h * _evaluate(function, t + h, candidate)

    return solve(
        residual, y, numerical_step=numerical_step, tolerances=tolerances
    ).value
