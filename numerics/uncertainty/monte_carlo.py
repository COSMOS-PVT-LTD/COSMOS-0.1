"""
COSMOS Rocket Propulsion Platform

Module: numerics.uncertainty.monte_carlo
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral uncertainty.monte_carlo foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.random.random_generators import generator
from numerics.random.seeds import validate
from numerics.uncertainty.uncertainty_propagation import (
    PropagationResult,
    ScalarModel,
    propagate,
)
from numerics.utilities.numerical_checks import count, invalid, same_shape, vector


def sample_and_propagate(
    model: ScalarModel, lower: ArrayLike, upper: ArrayLike, *, samples: int, seed: int
) -> PropagationResult:
    """Independent uniform marginal Monte Carlo; not a correlated-input model."""
    a, b = vector(lower), vector(upper)
    same_shape(a, b)
    if (b <= a).any():
        invalid("Every sampling bound must increase.")
    n, s = count(samples, minimum=2), validate(seed)
    data = generator(s).uniform(a, b, (n, len(a)))
    return propagate(model, data, seed=s)
