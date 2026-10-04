"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.matrix_operations
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral matrix_operations foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    invalid,
    matrix,
    vector,
)


def matrix_vector(a: ArrayLike, x: ArrayLike) -> FloatArray:
    """Finite matrix-vector product; incompatible shapes are invalid input."""
    mat, vec = matrix(a), vector(x)
    if mat.shape[1] != vec.size:
        invalid("Matrix-vector dimensions do not match.")
    with np.errstate(over="ignore", invalid="ignore"):
        result = mat @ vec
    if not np.isfinite(result).all():
        failure("Matrix-vector product overflowed.")
    return result


def matrix_matrix(a: ArrayLike, b: ArrayLike) -> FloatArray:
    """Finite matrix product without broadcasting or implicit reshaping."""
    left, right = matrix(a), matrix(b)
    if left.shape[1] != right.shape[0]:
        invalid("Matrix-matrix dimensions do not match.")
    with np.errstate(over="ignore", invalid="ignore"):
        result = left @ right
    if not np.isfinite(result).all():
        failure("Matrix-matrix product overflowed.")
    return result
