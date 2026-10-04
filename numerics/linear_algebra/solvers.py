"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.solvers
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral solvers foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike

from core.exceptions import SolverConvergenceError
from numerics.linear_algebra.decomposition import lu
from numerics.utilities.convergence import NumericalResult, TerminationReason
from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import (
    FloatArray,
    failure,
    invalid,
    matrix,
    positive,
    vector,
)
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def solve_linear(
    a: ArrayLike,
    b: ArrayLike,
    *,
    policy: Tolerances = DEFAULT_TOLERANCES,
    max_condition: float | None = None,
) -> NumericalResult[FloatArray]:
    """Solve A x=b by owned partial-pivot LU and verify the original residual.

    Condition number is a NumPy SVD diagnostic, not a forward-accuracy proof.
    A caller may enforce max_condition; singular/machine-rank failures always
    fail closed. Residual acceptance is residual_tol + rtol*||b||.
    """
    mat, rhs = matrix(a, square=True), vector(b)
    if mat.shape[0] != rhs.size:
        invalid("Linear system dimensions do not match.")
    if max_condition is not None:
        positive(max_condition, "max_condition")
    try:
        condition = float(np.linalg.cond(mat))
    except np.linalg.LinAlgError as exc:
        raise SolverConvergenceError("Condition estimate failed.") from exc
    if not math.isfinite(condition) or (
        max_condition is not None and condition > max_condition
    ):
        failure("SINGULAR_SYSTEM: condition number exceeds the accepted limit.")
    factors = lu(mat)
    pb = factors.permutation @ rhs
    y: FloatArray = np.zeros_like(rhs)
    x: FloatArray = np.zeros_like(rhs)
    n = rhs.size
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for i in range(n):
            y[i] = pb[i] - factors.lower[i, :i] @ y[:i]
        for i in range(n - 1, -1, -1):
            x[i] = (y[i] - factors.upper[i, i + 1 :] @ x[i + 1 :]) / factors.upper[i, i]
        residual = rhs - mat @ x
    if not np.isfinite(x).all() or not np.isfinite(residual).all():
        failure("Linear solve produced a non-finite solution/residual.")
    norm = l2(residual)
    limit = positive(policy.residual + policy.relative * l2(rhs), "residual limit")
    if norm > limit:
        failure(f"Linear residual {norm} exceeds tolerance {limit}.")
    x.setflags(write=False)
    warning = (
        "ill-conditioned; forward accuracy not guaranteed"
        if condition > 1 / math.sqrt(np.finfo(float).eps)
        else "none"
    )
    return NumericalResult(
        x,
        True,
        1,
        norm,
        TerminationReason.CONVERGED_ABSOLUTE,
        "partial-pivot-lu",
        residual_history=(norm,),
        diagnostics=(("condition_number", repr(condition)), ("warning", warning)),
    )
