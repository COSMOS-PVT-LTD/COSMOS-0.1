"""
COSMOS Rocket Propulsion Platform

Module: numerics.sensitivity.local
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral sensitivity.local foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.uncertainty.uncertainty_propagation import ScalarModel
from numerics.utilities.numerical_checks import FloatArray, finite, positive, vector


def _evaluate(model: ScalarModel, point: FloatArray) -> float:
    try:
        return finite(model(point), "sensitivity output")
    except (InvalidInputError, ArithmeticError, ValueError, TypeError) as exc:
        raise SolverConvergenceError("Invalid sensitivity model output.") from exc


def gradient(model: ScalarModel, state: ArrayLike, *, step: float) -> FloatArray:
    """Local centered finite-difference scalar gradient; not automatic differentiation."""
    x, h = vector(state), positive(step)
    result = np.empty(len(x))
    for j in range(len(x)):
        plus, minus = x.copy(), x.copy()
        plus[j] += h
        minus[j] -= h
        if plus[j] == x[j] or minus[j] == x[j]:
            from numerics.utilities.numerical_checks import failure

            failure("Sensitivity perturbation below floating-point spacing.")
        result[j] = (_evaluate(model, plus) - _evaluate(model, minus)) / (2 * h)
    from numerics.utilities.numerical_checks import finite_output

    return finite_output(result)
