"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.elements
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.elements foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from numerics.utilities.numerical_checks import finite, invalid


@dataclass(frozen=True, slots=True)
class LinearElement:
    """1D two-node element with positive orientation."""

    left: float
    right: float

    def __post_init__(self) -> None:
        if finite(self.right) <= finite(self.left):
            invalid("Element requires finite increasing endpoints.")

    @property
    def length(self) -> float:
        return finite(self.right - self.left, "element length")

    def map(self, coordinate: float) -> float:
        from numerics.finite_element.shape_functions import values

        n = values(coordinate)
        return float(n[0] * self.left + n[1] * self.right)
