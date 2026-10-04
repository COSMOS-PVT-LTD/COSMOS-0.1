"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.wave_equation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.wave_equation foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_difference.second_order import operator
from numerics.finite_difference.stability import cfl, require_stable
from numerics.pde.pde_solver import PDESolution, equation_norm, finish, initial_state
from numerics.utilities.numerical_checks import (
    count,
    invalid,
    positive,
    same_shape,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(nodes: ArrayLike, initial: ArrayLike, velocity: ArrayLike, boundary: DirichletBoundary, *,
          wave_speed: float, time_step: float, steps: int,
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> PDESolution:
    """1D u_tt=c²u_xx, leapfrog and consistent second-order initial step."""
    x,u = initial_state(nodes,initial,boundary)
    v = vector(velocity)
    same_shape(x,v)
    if v[0]!=0 or v[-1]!=0:
        invalid("Static Dirichlet endpoints require zero endpoint velocity.")
    c,dt,n = positive(wave_speed),positive(time_step),count(steps)
    require_stable(cfl(c,dt,float(x[1]-x[0])),1.)
    op = c*c*operator(x)
    source = np.zeros(len(x)-2)
    source[0] += c*c*boundary.left/(x[1]-x[0])**2
    source[-1] += c*c*boundary.right/(x[1]-x[0])**2
    interior = u[1:-1]+dt*v[1:-1]+.5*dt*dt*(op@u[1:-1]+source)
    new = np.concatenate(([boundary.left],interior,[boundary.right]))
    history = [equation_norm(interior-u[1:-1]-dt*v[1:-1]-.5*dt*dt*(op@u[1:-1]+source))]
    states = [u.copy(),new]
    for _ in range(1,n):
        previous,current = states[-2],states[-1]
        interior = 2*current[1:-1]-previous[1:-1]+dt*dt*(op@current[1:-1]+source)
        history.append(equation_norm(interior-2*current[1:-1]+previous[1:-1]-dt*dt*(op@current[1:-1]+source)))
        states.append(np.concatenate(([boundary.left],interior,[boundary.right])))
    return finish(x,states,dt,"1d-wave-leapfrog",history,boundary,
                  tolerances.residual+tolerances.relative*max(1.,equation_norm(states[0])))
