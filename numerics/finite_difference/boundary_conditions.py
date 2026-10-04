"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_difference.boundary_conditions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_difference.boundary_conditions foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from numerics.utilities.numerical_checks import finite


@dataclass(frozen=True, slots=True)
class DirichletBoundary:
    """Explicit normalized endpoint values; no hidden extrapolated boundaries."""

    left: float
    right: float

    def __post_init__(self) -> None:
        finite(self.left, "left boundary")
        finite(self.right, "right boundary")
