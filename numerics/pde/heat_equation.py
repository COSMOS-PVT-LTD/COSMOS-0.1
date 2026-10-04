"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.heat_equation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.heat_equation foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference import explicit, implicit
from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_difference.second_order import operator
from numerics.finite_difference.stability import diffusion_limit, require_stable
from numerics.pde.pde_solver import PDESolution, equation_norm, finish, initial_state
from numerics.utilities.numerical_checks import count, invalid, positive
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(nodes: ArrayLike, initial: ArrayLike, boundary: DirichletBoundary, *,
          diffusivity: float, time_step: float, steps: int, method: str = "explicit",
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> PDESolution:
    """1D u_t=a u_xx, constant positive a and static Dirichlet endpoints."""
    x,u = initial_state(nodes,initial,boundary)
    a,dt,n = positive(diffusivity),positive(time_step),count(steps)
    if method not in {"explicit","implicit"}:
        invalid("Heat method must be explicit or implicit.")
    limit = diffusion_limit(a,float(x[1]-x[0]))
    if method=="explicit":
        require_stable(dt,limit)
    op = a*operator(x)
    source = np.zeros(len(x)-2)
    source[0] += a*boundary.left/(x[1]-x[0])**2
    source[-1] += a*boundary.right/(x[1]-x[0])**2
    states,history = [u.copy()],[]
    for _ in range(n):
        old = u[1:-1].copy()
        if method=="explicit":
            interior = explicit.update(old,op,source,dt,stability_limit=limit)
            residual = interior-old-dt*(op@old+source)
        else:
            interior = implicit.update(old,op,source,dt,tolerances=tolerances)
            residual = interior-old-dt*(op@interior+source)
        u = np.concatenate(([boundary.left],interior,[boundary.right]))
        states.append(u)
        history.append(equation_norm(residual))
    return finish(x,states,dt,"1d-heat-"+method,history,boundary,
                  tolerances.residual+tolerances.relative*max(1.,equation_norm(states[0])))
