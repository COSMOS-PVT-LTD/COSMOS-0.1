"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.pde_solver
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.pde_solver foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    grid,
    invalid,
    same_shape,
    vector,
)


@dataclass(frozen=True, slots=True)
class PDESolution:
    """Representative normalized PDE trajectory; history is discrete equation residual."""
    nodes: FloatArray
    times: FloatArray
    states: FloatArray
    method: str
    residual_history: tuple[float,...]
    boundary: DirichletBoundary

def initial_state(nodes: ArrayLike, initial: ArrayLike, boundary: DirichletBoundary) -> tuple[FloatArray, FloatArray]:
    x,u = grid(nodes,uniform=True),vector(initial)
    same_shape(x,u)
    if len(x)<3:
        invalid("PDE grid requires an interior node.")
    if u[0]!=boundary.left or u[-1]!=boundary.right:
        invalid("Initial endpoint values must satisfy explicit Dirichlet boundaries.")
    return x,u

def finish(nodes: FloatArray, states: list[FloatArray], dt: float, method: str, history: list[float],
           boundary: DirichletBoundary, residual_limit: float) -> PDESolution:
    if history and max(history)>residual_limit:
        failure("PDE discrete-equation residual exceeds tolerance.")
    data,times = np.array(states),np.arange(len(states),dtype=float)*dt
    if not np.isfinite(data).all() or not np.isfinite(times).all():
        failure("PDE trajectory is nonfinite.")
    for value in (nodes,data,times):
        value.setflags(write=False)
    return PDESolution(nodes,times,data,method,tuple(history),boundary)

def equation_norm(residual: FloatArray) -> float:
    return l2(residual)
