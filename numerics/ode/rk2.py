"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.rk2
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.rk2 foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.ode.euler import RHSFunction
from numerics.ode.midpoint import step as _midpoint
from numerics.utilities.numerical_checks import FloatArray


def step(function: RHSFunction, time: float, state: ArrayLike, step_size: float) -> FloatArray:
    """The RK2 family default is explicitly the midpoint tableau."""
    return _midpoint(function,time,state,step_size)
