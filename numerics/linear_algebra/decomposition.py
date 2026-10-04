"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.decomposition
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral decomposition foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, failure, matrix


@dataclass(frozen=True, slots=True)
class LUDecomposition:
    """Partial-pivot LU factors satisfying P A = L U."""
    permutation: FloatArray
    lower: FloatArray
    upper: FloatArray


@dataclass(frozen=True, slots=True)
class QRDecomposition:
    """Householder factors satisfying A = Q R, Q square orthogonal."""
    orthogonal: FloatArray
    upper: FloatArray


def lu(values: ArrayLike) -> LUDecomposition:
    """Owned partial-pivot Gaussian elimination; scaled machine-rank guard."""
    u = matrix(values, square=True)
    n = u.shape[0]
    p: FloatArray = np.eye(n)
    lower: FloatArray = np.eye(n)
    rank_floor = np.finfo(float).eps * n * float(np.max(np.abs(u)))
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for k in range(n):
            pivot = k + int(np.argmax(np.abs(u[k:, k])))
            if abs(u[pivot, k]) <= rank_floor:
                failure("SINGULAR_SYSTEM: LU pivot is below scaled machine resolution.")
            if pivot != k:
                u[[k, pivot], :] = u[[pivot, k], :]
                p[[k, pivot], :] = p[[pivot, k], :]
                if k:
                    lower[[k, pivot], :k] = lower[[pivot, k], :k]
            for i in range(k + 1, n):
                lower[i, k] = u[i, k] / u[k, k]
                u[i, k:] -= lower[i, k] * u[k, k:]
                u[i, k] = 0.0
            if not np.isfinite(u).all():
                failure("LU elimination produced non-finite factors.")
    for factor in (p, lower, u):
        factor.setflags(write=False)
    return LUDecomposition(p, lower, u)


def qr(values: ArrayLike) -> QRDecomposition:
    """Owned scaled Householder QR, including rectangular/rank-deficient matrices."""
    r = matrix(values)
    m, n = r.shape
    q: FloatArray = np.eye(m)
    for k in range(min(m, n)):
        x = r[k:, k].copy()
        scale = float(np.max(np.abs(x)))
        if scale == 0:
            continue
        v = x / scale
        norm = math.hypot(*(float(z) for z in v))
        v[0] += math.copysign(norm, float(v[0]))
        denominator = float(v @ v)
        with np.errstate(over="ignore", invalid="ignore"):
            r[k:, :] -= (2.0 / denominator) * np.outer(v, v @ r[k:, :])
            q[:, k:] -= (2.0 / denominator) * np.outer(q[:, k:] @ v, v)
        if not np.isfinite(r).all() or not np.isfinite(q).all():
            failure("QR factorization produced non-finite factors.")
    q.setflags(write=False)
    r.setflags(write=False)
    return QRDecomposition(q, r)
