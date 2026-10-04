"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.sparse_matrix
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral sparse_matrix foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import (
    FloatArray,
    count,
    failure,
    finite,
    invalid,
    vector,
)


@dataclass(frozen=True, slots=True)
class SparseMatrix:
    """COO storage; duplicate entries sum in supplied order, no sparse factorizer."""

    shape: tuple[int, int]
    rows: tuple[int, ...]
    columns: tuple[int, ...]
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.shape) != 2:
            invalid("Sparse shape must have two dimensions.")
        n, m = (count(v, "sparse dimension") for v in self.shape)
        if not len(self.rows) == len(self.columns) == len(self.values):
            invalid("COO coordinate/value lengths must agree.")
        for i, j, value in zip(self.rows, self.columns, self.values, strict=True):
            count(i, "row index", 0)
            count(j, "column index", 0)
            if i >= n or j >= m:
                invalid("COO index is out of bounds.")
            finite(value, "COO value")

    def to_dense(self) -> FloatArray:
        """Accumulate COO entries into checked dense storage."""
        result: FloatArray = np.zeros(self.shape, dtype=np.float64)
        with np.errstate(over="ignore", invalid="ignore"):
            for i, j, v in zip(self.rows, self.columns, self.values, strict=True):
                result[i, j] += v
        if not np.isfinite(result).all():
            failure("COO duplicate accumulation overflowed.")
        return result

    def matvec(self, values: ArrayLike) -> FloatArray:
        """O(nnz) matrix-vector product; preserves additive duplicate semantics."""
        x = vector(values)
        if x.size != self.shape[1]:
            invalid("Sparse matrix-vector dimensions do not match.")
        result: FloatArray = np.zeros(self.shape[0], dtype=np.float64)
        with np.errstate(over="ignore", invalid="ignore"):
            for i, j, v in zip(self.rows, self.columns, self.values, strict=True):
                result[i] += v * x[j]
        if not np.isfinite(result).all():
            failure("Sparse matrix-vector product overflowed.")
        return result
