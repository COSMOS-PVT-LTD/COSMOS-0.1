"""
COSMOS Rocket Propulsion Platform

Module: numerics.interpolation.cubic_spline
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral interpolation.cubic_spline foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.interpolation.linear import _data, _query
from numerics.linear_algebra.solvers import solve_linear
from numerics.utilities.numerical_checks import FloatArray, finite, invalid


@dataclass(frozen=True, slots=True)
class CubicSpline:
    """Natural or clamped C2 interpolant; no periodic/not-a-knot claim."""
    nodes: FloatArray
    values: FloatArray
    second_derivatives: FloatArray
    extrapolate: bool = False

    @classmethod
    def build(cls, nodes: ArrayLike, values: ArrayLike, *, boundary: str = "natural",
              endpoint_slopes: tuple[float, float] | None = None, extrapolate: bool = False) -> CubicSpline:
        x, y = _data(nodes, values)
        n, h = len(x), np.diff(x)
        a, rhs = np.zeros((n, n)), np.zeros(n)
        for i in range(1, n-1):
            a[i, i-1:i+2] = [h[i-1], 2*(h[i-1]+h[i]), h[i]]
            rhs[i] = 6*((y[i+1]-y[i])/h[i] - (y[i]-y[i-1])/h[i-1])
        if boundary == "natural" and endpoint_slopes is None:
            a[0, 0] = a[-1, -1] = 1
        elif boundary == "clamped" and endpoint_slopes is not None:
            left, right = (finite(v, "endpoint slope") for v in endpoint_slopes)
            a[0, :2], a[-1, -2:] = [2*h[0], h[0]], [h[-1], 2*h[-1]]
            rhs[0] = 6*((y[1]-y[0])/h[0]-left)
            rhs[-1] = 6*(right-(y[-1]-y[-2])/h[-1])
        else:
            invalid("Use natural boundary without slopes or clamped boundary with two slopes.")
        second = solve_linear(a, rhs).value
        for data in (x, y, second):
            data.setflags(write=False)
        return cls(x, y, second, extrapolate)

    def __call__(self, query: float) -> float:
        q, i = _query(self.nodes, query, self.extrapolate)
        h = self.nodes[i+1]-self.nodes[i]
        a, b = (self.nodes[i+1]-q)/h, (q-self.nodes[i])/h
        y, m = self.values, self.second_derivatives
        return finite(float(a*y[i]+b*y[i+1]+((a**3-a)*m[i]+(b**3-b)*m[i+1])*h*h/6))
