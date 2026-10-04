"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.shape_functions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.shape_functions foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.utilities.numerical_checks import FloatArray, finite, invalid


def values(coordinate: float) -> FloatArray:
    """Two-node reference element on [-1,1], partition of unity."""
    xi = finite(coordinate)
    if not -1 <= xi <= 1:
        invalid("Reference coordinate must lie in [-1,1].")
    return np.array([(1 - xi) / 2, (1 + xi) / 2])


def derivatives() -> FloatArray:
    """Reference-coordinate derivatives; physical derivative needs Jacobian."""
    return np.array([-0.5, 0.5])
