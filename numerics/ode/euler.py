"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.euler
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.euler foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable

from numpy.typing import ArrayLike

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    finite,
    positive,
    vector,
)

RHSFunction = Callable[[float, FloatArray], FloatArray]

def _evaluate(function: RHSFunction, time: float, state: FloatArray) -> FloatArray:
    try:
        value = vector(function(time,state.copy()),"ODE derivative")
    except (InvalidInputError, ArithmeticError, TypeError, ValueError) as exc:
        raise SolverConvergenceError("Nonfinite/invalid ODE derivative.") from exc
    if value.shape != state.shape:
        failure("ODE derivative shape differs from state.")
    return value

def _input(time: float, state: ArrayLike, step_size: float) -> tuple[float, FloatArray, float]:
    return finite(time,"time"),vector(state),positive(step_size,"time step")

def _output(value: FloatArray) -> FloatArray:
    import numpy as np
    if not np.isfinite(value).all():
        failure("ODE update is nonfinite.")
    return value

def step(function: RHSFunction, time: float, state: ArrayLike, step_size: float) -> FloatArray:
    """Forward Euler; caller must qualify stability for the supplied RHS."""
    t,y,h = _input(time,state,step_size)
    return _output(y+h*_evaluate(function,t,y))
