"""
COSMOS Rocket Propulsion Platform

Module: numerics.uncertainty.uncertainty_propagation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral uncertainty.uncertainty_propagation foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from core.exceptions import InvalidInputError, SolverConvergenceError
from numerics.uncertainty.statistics import SampleStatistics, summarize
from numerics.utilities.numerical_checks import FloatArray, finite, matrix

ScalarModel = Callable[[FloatArray], float]


@dataclass(frozen=True, slots=True)
class PropagationResult:
    inputs: FloatArray
    outputs: FloatArray
    statistics: SampleStatistics
    seed: int | None


def propagate(
    model: ScalarModel, inputs: ArrayLike, *, seed: int | None = None
) -> PropagationResult:
    """Evaluate supplied normalized sample rows; no hidden stochastic sampling."""
    data = matrix(inputs)
    values = []
    for row in data:
        try:
            values.append(finite(model(row.copy()), "model output"))
        except (InvalidInputError, ArithmeticError, TypeError, ValueError) as exc:
            raise SolverConvergenceError("Invalid uncertainty model output.") from exc
    output = np.array(values)
    stats = summarize(output)
    data.setflags(write=False)
    output.setflags(write=False)
    return PropagationResult(data, output, stats, seed)
