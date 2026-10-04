"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.midpoint
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.midpoint foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.ode.euler import RHSFunction, _evaluate, _input, _output
from numerics.utilities.numerical_checks import FloatArray


def step(function: RHSFunction, time: float, state: ArrayLike, step_size: float) -> FloatArray:
    """Explicit midpoint two-stage RK2."""
    t,y,h = _input(time,state,step_size)
    k1 = _evaluate(function,t,y)
    return _output(y+h*_evaluate(function,t+h/2,y+h*k1/2))
