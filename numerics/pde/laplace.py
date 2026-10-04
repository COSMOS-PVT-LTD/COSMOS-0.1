"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.laplace
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.laplace foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.pde.poisson import solve as _poisson
from numerics.utilities.convergence import NumericalResult
from numerics.utilities.numerical_checks import FloatArray, grid
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(
    nodes: ArrayLike,
    boundary: DirichletBoundary,
    *,
    tolerances: Tolerances = DEFAULT_TOLERANCES,
) -> NumericalResult[FloatArray]:
    """1D Laplace is the zero-source Poisson specialization."""
    x = grid(nodes, uniform=True)
    return _poisson(x, np.zeros_like(x), boundary, tolerances=tolerances)
