"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.second_order
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.second_order foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import (
    FloatArray,
    finite_output,
    grid,
    invalid,
    positive,
    vector,
)


def differentiate(values: ArrayLike, spacing: float) -> FloatArray:
    """Second-order central second derivative on interior nodes only."""
    y,h = vector(values),positive(spacing)
    if len(y)<3:
        invalid("Second derivative requires >=3 nodes.")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return finite_output((y[2:]-2*y[1:-1]+y[:-2])/(h*h))

def operator(nodes: ArrayLike) -> FloatArray:
    """Interior Dirichlet Laplacian; boundary RHS contribution remains explicit."""
    x = grid(nodes,uniform=True)
    n,h = len(x)-2,float(x[1]-x[0])
    if n<1:
        invalid("Laplacian requires an interior node.")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return finite_output((np.diag(np.full(n,-2.))+np.diag(np.ones(n-1),1)+np.diag(np.ones(n-1),-1))/(h*h))
