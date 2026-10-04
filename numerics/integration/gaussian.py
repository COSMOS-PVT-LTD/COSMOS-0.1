"""
COSMOS Rocket Propulsion Platform

Module: numerics.integration.gaussian
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral integration.gaussian foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

import numpy as np

from numerics.integration.trapezoidal import _interval
from numerics.utilities.numerical_checks import (
    FloatArray,
    ScalarFunction,
    count,
    evaluate,
    failure,
    finite,
    invalid,
)


def legendre_rule(order: int) -> tuple[FloatArray, FloatArray]:
    """Owned Legendre recurrence/Newton symmetric nodes; orders 1..64."""
    n = count(order)
    if n > 64:
        invalid("Gaussian foundation supports orders <=64.")
    nodes, weights = np.zeros(n), np.zeros(n)
    for i in range((n+1)//2):
        z = math.cos(math.pi*(i+0.75)/(n+0.5))
        derivative = 0.0
        for _ in range(80):
            p, previous = 1.0, 0.0
            for degree in range(1,n+1):
                old = previous
                previous = p
                p = ((2*degree-1)*z*previous-(degree-1)*old)/degree
            derivative = n*(z*p-previous)/(z*z-1)
            updated = z-p/derivative
            if abs(updated-z) <= 4*math.ulp(1.0):
                z = updated
                break
            z = updated
        else:
            failure("Legendre node Newton solve did not converge.")
        p, previous = 1.0, 0.0
        for degree in range(1,n+1):
            old, previous = previous, p
            p = ((2*degree-1)*z*previous-(degree-1)*old)/degree
        derivative = n*(z*p-previous)/(z*z-1)
        weight = 2/((1-z*z)*derivative*derivative)
        nodes[i], nodes[n-1-i] = -z, z
        weights[i] = weights[n-1-i] = weight
    return nodes, weights

def integrate(function: ScalarFunction, lower: float, upper: float, *, order: int = 8) -> float:
    """Gauss-Legendre on finite increasing interval, exact through degree 2n-1."""
    a, b = _interval(lower,upper)
    x, w = legendre_rule(order)
    return finite((b-a)/2*sum(float(weight)*evaluate(function,(a+b)/2+(b-a)*float(node)/2)
                             for node,weight in zip(x,w,strict=True)))
