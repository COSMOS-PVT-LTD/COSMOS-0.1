"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.assembly
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.assembly foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_element.elements import LinearElement
from numerics.finite_element.gauss_quadrature import points
from numerics.finite_element.shape_functions import values
from numerics.finite_element.stiffness_matrix import stiffness
from numerics.utilities.numerical_checks import (
    FloatArray,
    ScalarFunction,
    evaluate,
    finite_output,
    grid,
    positive,
)


def assemble(
    nodes: ArrayLike,
    source: ScalarFunction,
    *,
    coefficient: float = 1.0,
    quadrature_order: int = 4,
) -> tuple[FloatArray, FloatArray]:
    """Assemble weak -d(k u')/dx=f; element-local loads integrated by Gauss."""
    x = grid(nodes)
    k = positive(coefficient)
    a, b = np.zeros((len(x), len(x))), np.zeros(len(x))
    for i in range(len(x) - 1):
        element = LinearElement(float(x[i]), float(x[i + 1]))
        a[i : i + 2, i : i + 2] += stiffness(element, k)
        q, w = points(element, order=quadrature_order)
        for coordinate, weight in zip(q, w, strict=True):
            xi = 2 * (coordinate - element.left) / element.length - 1
            b[i : i + 2] += (
                float(weight) * evaluate(source, float(coordinate)) * values(float(xi))
            )
    return finite_output(a), finite_output(b)
