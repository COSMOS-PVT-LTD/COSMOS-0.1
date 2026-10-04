"""
COSMOS Rocket Propulsion Platform

Module: numerics.pde.elliptic
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral pde.elliptic foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.pde.poisson import solve as _poisson
from numerics.utilities.convergence import NumericalResult
from numerics.utilities.numerical_checks import FloatArray
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve(nodes: ArrayLike, source: ArrayLike, boundary: DirichletBoundary, *,
          tolerances: Tolerances = DEFAULT_TOLERANCES) -> NumericalResult[FloatArray]:
    """Elliptic family foundation is explicitly 1D scalar Poisson."""
    return _poisson(nodes,source,boundary,tolerances=tolerances)
