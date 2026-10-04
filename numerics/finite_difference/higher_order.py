"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.higher_order
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.higher_order foundation.
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
    invalid,
    positive,
    vector,
)


def first_derivative(values: ArrayLike, spacing: float) -> FloatArray:
    """Fourth-order centered first derivative; only nodes [2:-2] are returned."""
    y,h = vector(values),positive(spacing)
    if len(y)<5:
        invalid("Fourth-order stencil requires >=5 values.")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return finite_output((y[:-4]-8*y[1:-3]+8*y[3:-1]-y[4:])/(12*h))

def second_derivative(values: ArrayLike, spacing: float) -> FloatArray:
    """Fourth-order centered second derivative; no unqualified endpoint stencil."""
    y,h = vector(values),positive(spacing)
    if len(y)<5:
        invalid("Fourth-order stencil requires >=5 values.")
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return finite_output((-y[:-4]+16*y[1:-3]-30*y[2:-2]+16*y[3:-1]-y[4:])/(12*h*h))
