"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.eigenvalues
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral eigenvalues foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.numerical_checks import FloatArray, failure, invalid, matrix
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


@dataclass(frozen=True, slots=True)
class EigenSystem:
    """Ascending real eigenvalues and corresponding column eigenvectors."""
    values: FloatArray
    vectors: FloatArray


def symmetric_eigensystem(values: ArrayLike, *,
                          policy: Tolerances = DEFAULT_TOLERANCES) -> NumericalResult[EigenSystem]:
    """Owned maximum-offdiagonal Jacobi rotations for small symmetric matrices.

    Symmetry is checked within policy then rounding noise is symmetrized.
    Original A V - V diag(lambda) is verified independently before success.
    This is not an industrial nonsymmetric or sparse eigen solver.
    """
    original = matrix(values, square=True)
    if not np.allclose(original, original.T, atol=policy.absolute, rtol=policy.relative):
        invalid("Jacobi eigen solver requires a symmetric matrix.")
    scale = float(np.max(np.abs(original)))
    if scale == 0:
        scale = 1.0
    a = original / scale
    a = a / 2 + a.T / 2
    n = a.shape[0]
    vectors: FloatArray = np.eye(n)
    history: list[float] = []
    for iteration in range(policy.max_iterations + 1):
        off = a - np.diag(np.diag(a))
        norm = float(np.max(np.abs(off))) * scale
        history.append(norm)
        if norm <= policy.threshold(scale):
            order = np.argsort(np.diag(a))
            eigenvalues: FloatArray = np.diag(a)[order] * scale
            eigenvectors: FloatArray = vectors[:, order]
            with np.errstate(over="ignore", invalid="ignore"):
                residual = original @ eigenvectors - eigenvectors * eigenvalues
            if not np.isfinite(residual).all():
                failure("Eigen residual is non-finite.")
            residual_norm = float(np.linalg.norm(residual))
            limit = policy.residual + policy.relative * float(np.linalg.norm(original))
            if residual_norm > limit:
                failure("Eigen residual exceeds tolerance.")
            eigenvalues.setflags(write=False)
            eigenvectors.setflags(write=False)
            return NumericalResult(EigenSystem(eigenvalues, eigenvectors), True, iteration,
                                   residual_norm, TerminationReason.CONVERGED_ABSOLUTE,
                                   "jacobi-symmetric", residual_history=tuple(history))
        if iteration == policy.max_iterations:
            break
        p, q = np.unravel_index(int(np.argmax(np.abs(off))), a.shape)
        delta = float((a[q, q] - a[p, p]) / 2)
        apq = float(a[p, q])
        denominator = delta + math.copysign(math.hypot(delta, apq), delta)
        t = apq / denominator
        c = 1 / math.sqrt(1 + t*t)
        s = t*c
        rotation: FloatArray = np.eye(n)
        rotation[p, p] = rotation[q, q] = c
        rotation[p, q], rotation[q, p] = s, -s
        a = rotation.T @ a @ rotation
        a[p, q] = a[q, p] = 0.0
        vectors = vectors @ rotation
    failure("MAX_ITERATIONS: symmetric Jacobi eigen solve exhausted.")


def eigenvalues(values: ArrayLike, *, policy: Tolerances = DEFAULT_TOLERANCES) -> FloatArray:
    """Ascending checked symmetric eigenvalues; full diagnostics via eigensystem."""
    return symmetric_eigensystem(values, policy=policy).value.values
