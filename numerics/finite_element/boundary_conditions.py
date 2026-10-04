"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.boundary_conditions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.boundary_conditions foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.utilities.numerical_checks import FloatArray, invalid, matrix, vector


def impose_dirichlet(
    stiffness: ArrayLike, load: ArrayLike, boundary: DirichletBoundary
) -> tuple[FloatArray, FloatArray]:
    """Symmetric elimination preserves interior equation and matrix symmetry."""
    a, b = matrix(stiffness, square=True), vector(load)
    if len(b) != a.shape[0] or len(b) < 2:
        invalid("FEM boundary dimensions require >=2 nodes.")
    for index, value in ((0, boundary.left), (len(b) - 1, boundary.right)):
        b -= a[:, index] * value
        a[:, index] = 0
        a[index, :] = 0
        a[index, index] = 1
        b[index] = value
    return a, b
