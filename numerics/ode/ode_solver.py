"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.ode_solver
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.ode_solver foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.ode import euler, heun, midpoint, rk2, rk4, rk45
from numerics.ode.adaptive_step import next_step
from numerics.ode.euler import RHSFunction
from numerics.utilities.numerical_checks import (
    FloatArray,
    count,
    failure,
    finite,
    invalid,
    positive,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


@dataclass(frozen=True, slots=True)
class Trajectory:
    """Final time reached, not a proof of global error or RHS stability."""
    times: FloatArray
    states: FloatArray
    method: str
    accepted_steps: int
    rejected_steps: int
    local_error_ratios: tuple[float,...] = ()
    termination_reason: str = "FINAL_TIME_REACHED"

def _finish(times: list[float], states: list[FloatArray], method: str, rejected: int = 0,
            errors: tuple[float,...] = ()) -> Trajectory:
    t,y = np.array(times),np.array(states)
    t.setflags(write=False)
    y.setflags(write=False)
    return Trajectory(t,y,method,len(times)-1,rejected,errors)

def fixed(function: RHSFunction, initial: ArrayLike, start: float, stop: float, *,
          step_size: float, method: str = "rk4", max_steps: int = 10000) -> Trajectory:
    """Explicit fixed steps with truncated final step; forward time only."""
    t,end,h = finite(start),finite(stop),positive(step_size)
    methods = {"euler":euler.step,"heun":heun.step,"midpoint":midpoint.step,"rk2":rk2.step,"rk4":rk4.step}
    if end <= t or method not in methods:
        invalid("Invalid time interval or fixed-step method.")
    limit = count(max_steps)
    times,states = [t],[vector(initial)]
    while t < end:
        if len(times)-1 >= limit:
            failure("ODE exhausted step budget.")
        dt = min(h,end-t)
        if t+dt == t:
            failure("ODE time step stagnated.")
        states.append(methods[method](function,t,states[-1],dt))
        t = end if dt == end-t else t+dt
        times.append(t)
    return _finish(times,states,method)

def adaptive(function: RHSFunction, initial: ArrayLike, start: float, stop: float, *,
             first_step: float, min_step: float = 1e-12, max_step: float = 1.0,
             max_steps: int = 10000, tolerances: Tolerances = DEFAULT_TOLERANCES) -> Trajectory:
    """Dormand-Prince RK45; componentwise local error control, bounded attempts."""
    t,end = finite(start),finite(stop)
    h,lo,hi = positive(first_step),positive(min_step),positive(max_step)
    if end <= t or not lo <= h <= hi:
        invalid("Invalid time interval or step bounds.")
    limit = count(max_steps)
    y = vector(initial)
    times,states,errors = [t],[y.copy()],[]
    rejected = attempts = 0
    while t < end:
        if attempts >= limit:
            failure("Adaptive ODE exhausted attempted-step budget.")
        dt = min(h,end-t)
        if t+dt == t:
            failure("Adaptive time step stagnated.")
        new,error = rk45.step(function,t,y,dt)
        scale = tolerances.absolute+tolerances.relative*np.maximum(np.abs(y),np.abs(new))
        if np.any(scale <= 0):
            invalid("Adaptive error scale must be positive in every component.")
        ratio = float(np.max(np.abs(error)/scale))
        if not np.isfinite(ratio):
            failure("Adaptive error ratio is nonfinite.")
        errors.append(ratio)
        attempts += 1
        if ratio <= 1:
            t = end if dt == end-t else t+dt
            y = new
            times.append(t)
            states.append(y.copy())
        else:
            rejected += 1
            if dt <= lo:
                failure("Adaptive error cannot be controlled above minimum step.")
        h = next_step(dt,ratio,minimum=lo,maximum=hi)
    return _finish(times,states,"dormand-prince-5(4)",rejected,tuple(errors))
