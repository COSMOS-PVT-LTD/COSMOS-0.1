"""
COSMOS Rocket Propulsion Platform

Module: numerics.utilities.tolerances
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral tolerances foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.exceptions import InvalidInputError
from numerics.utilities.numerical_checks import finite


@dataclass(frozen=True, slots=True)
class Tolerances:
    """Explicit normalized tolerance policy; no physical engineering defaults."""

    absolute: float = 1.0e-10
    relative: float = 1.0e-10
    residual: float = 1.0e-10
    max_iterations: int = 100
    stagnation_window: int = 4

    def __post_init__(self) -> None:
        for name in ("absolute", "relative", "residual"):
            value = getattr(self, name)
            if finite(value, f"{name} tolerance") < 0:
                raise InvalidInputError(f"{name} tolerance must be finite and nonnegative.")
        if self.absolute == 0 and self.relative == 0:
            raise InvalidInputError("At least one solution tolerance must be positive.")
        if self.residual == 0:
            raise InvalidInputError("Residual tolerance must be positive.")
        for name, minimum in (("max_iterations", 1), ("stagnation_window", 2)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise InvalidInputError(f"{name} must be an integer >= {minimum}.")

    def threshold(self, scale: float = 0.0) -> float:
        """Return atol + rtol*|scale|, rejecting nonfinite scales."""
        scale = finite(scale, "Tolerance scale")
        result = self.absolute + self.relative * abs(scale)
        if not math.isfinite(result):
            raise InvalidInputError("Tolerance threshold overflowed; normalize input/scales.")
        return result


DEFAULT_TOLERANCES = Tolerances()

# Existing Physics scalar port contract: xtol=1e-12, max_iter=80.
ROOT_TOLERANCES = Tolerances(absolute=1.0e-12, relative=0.0, residual=1.0e-12, max_iterations=80)
