"""
COSMOS Rocket Propulsion Platform

Module: numerics.nonlinear_solver.trust_region
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral nonlinear_solver.trust_region foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.utilities.norms import l2
from numerics.utilities.numerical_checks import FloatArray, positive, vector


def bounded_step(step: ArrayLike, radius: float) -> FloatArray:
    """Euclidean Newton-step cap interface; not a dogleg/model-ratio trust-region solver."""
    p, r = vector(step), positive(radius, "trust radius")
    norm = l2(p)
    return p if norm <= r else p * (r / norm)
