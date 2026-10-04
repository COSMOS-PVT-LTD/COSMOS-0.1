"""
COSMOS Rocket Propulsion Platform

Module: numerics.uncertainty.latin_hypercube
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral uncertainty.latin_hypercube foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.random.random_generators import generator
from numerics.utilities.numerical_checks import FloatArray, count


def sample(samples: int, dimensions: int, *, seed: int) -> FloatArray:
    """Randomized LHS on [0,1)^d: exactly one observation per marginal stratum."""
    n, d = count(samples), count(dimensions)
    rng = generator(seed)
    result = np.empty((n, d))
    for j in range(d):
        result[:, j] = (rng.permutation(n) + rng.random(n)) / n
    return result
