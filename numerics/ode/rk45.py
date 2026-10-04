"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.rk45
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.rk45 foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.ode.euler import RHSFunction, _evaluate, _input, _output
from numerics.utilities.numerical_checks import FloatArray

# Dormand-Prince 5(4) tableau, mathematical coefficients, independently coded.
# Provenance: Ketcheson's Numipedia DP5, linked in the V&V report.
STAGES = (
    (),
    (1/5,),
    (3/40,9/40),
    (44/45,-56/15,32/9),
    (19372/6561,-25360/2187,64448/6561,-212/729),
    (9017/3168,-355/33,46732/5247,49/176,-5103/18656),
    (35/384,0,500/1113,125/192,-2187/6784,11/84),
)
TIMES = (0.,1/5,3/10,4/5,8/9,1.,1.)
FIFTH = (35/384,0.,500/1113,125/192,-2187/6784,11/84,0.)
FOURTH = (5179/57600,0.,7571/16695,393/640,-92097/339200,187/2100,1/40)

def step(function: RHSFunction, time: float, state: ArrayLike, step_size: float) -> tuple[FloatArray, FloatArray]:
    """Return fifth-order state and embedded fifth-minus-fourth local error."""
    t,y,h = _input(time,state,step_size)
    stages: list[FloatArray] = []
    for c,row in zip(TIMES,STAGES,strict=True):
        increment = np.zeros_like(y)
        for coefficient,k in zip(row,stages,strict=True):
            increment += coefficient*k
        stages.append(_evaluate(function,t+c*h,_output(y+h*increment)))
    high,low = y.copy(),y.copy()
    for hi,lo,k in zip(FIFTH,FOURTH,stages,strict=True):
        high += h*hi*k
        low += h*lo*k
    return _output(high),_output(high-low)
