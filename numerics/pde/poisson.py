"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.poisson
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.poisson foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_difference.second_order import operator
from numerics.linear_algebra.solvers import solve_linear
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.numerical_checks import FloatArray, grid, same_shape, vector
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(nodes: ArrayLike, source: ArrayLike, boundary: DirichletBoundary, *,
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> NumericalResult[FloatArray]:
    """1D u''=source, uniform nodes, explicit endpoint Dirichlet values."""
    x,f = grid(nodes,uniform=True),vector(source)
    same_shape(x,f)
    a = operator(x)
    rhs = f[1:-1].copy()
    h = float(x[1]-x[0])
    rhs[0] -= boundary.left/(h*h)
    rhs[-1] -= boundary.right/(h*h)
    solved = solve_linear(a,rhs,policy=tolerances)
    u = np.concatenate(([boundary.left],solved.value,[boundary.right]))
    u.setflags(write=False)
    return NumericalResult(u,True,1,solved.residual_norm,TerminationReason.CONVERGED_ABSOLUTE,
                           "1d-poisson-dirichlet",residual_history=solved.residual_history,
                           diagnostics=(("scope","normalized 1D representative equation, not CFD"),))
