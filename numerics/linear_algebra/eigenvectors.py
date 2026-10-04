"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.eigenvectors
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral eigenvectors foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.linear_algebra.eigenvalues import symmetric_eigensystem
from numerics.utilities.numerical_checks import FloatArray
from numerics.utilities.tolerances import DEFAULT_TOLERANCES, Tolerances


def eigenvectors(values: ArrayLike, *, policy: Tolerances = DEFAULT_TOLERANCES) -> FloatArray:
    """Checked symmetric eigenvectors in ascending eigenvalue column order."""
    return symmetric_eigensystem(values, policy=policy).value.vectors
