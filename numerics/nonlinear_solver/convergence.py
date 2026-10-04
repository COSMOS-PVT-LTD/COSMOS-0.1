"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.convergence
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.convergence foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import FloatArray
from numerics.utilities.tolerances import Tolerances


def residual_converged(residual: FloatArray, tolerances: Tolerances) -> bool:
    """Only the actual nonlinear equation residual certifies convergence."""
    return l2(residual) <= tolerances.residual
