"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.numerical_jacobian
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.numerical_jacobian foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.nonlinear_solver.jacobian import ResidualFunction, evaluate_residual
from numerics.utilities.numerical_checks import FloatArray, failure, positive, vector


def jacobian(function: ResidualFunction, state: ArrayLike, *, step: float) -> FloatArray:
    """Centered finite differences with explicit absolute perturbation; this is not AD."""
    x, h = vector(state), positive(step,"Jacobian perturbation")
    result = np.empty((len(x),len(x)))
    for j in range(len(x)):
        plus, minus = x.copy(), x.copy()
        plus[j] += h
        minus[j] -= h
        if plus[j] == x[j] or minus[j] == x[j]:
            failure("Jacobian perturbation is below floating-point spacing.")
        result[:,j] = (evaluate_residual(function,plus)-evaluate_residual(function,minus))/(2*h)
    if not np.isfinite(result).all():
        failure("Numerical Jacobian is nonfinite.")
    return result
