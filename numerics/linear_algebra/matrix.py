"""
COSMOS Rocket Propulsion Platform

Module: numerics.linear_algebra.matrix
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral matrix foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, matrix


@dataclass(frozen=True, slots=True)
class Matrix:
    """Finite dense rank-two data; owned read-only copy, no unit semantics."""

    data: FloatArray

    def __post_init__(self) -> None:
        checked = matrix(self.data)
        checked.setflags(write=False)
        object.__setattr__(self, "data", checked)

    @classmethod
    def from_array(cls, values: ArrayLike) -> Matrix:
        """Validate a finite numeric matrix, preserving the caller's data."""
        return cls(matrix(values))
