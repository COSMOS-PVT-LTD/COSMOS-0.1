"""
COSMOS Rocket Propulsion Platform

Module: numerics.random.sampling
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral random.sampling foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.random.random_generators import generator
from numerics.utilities.numerical_checks import FloatArray, count, invalid, vector


def sample(
    values: ArrayLike, samples: int, *, seed: int, replace: bool = True
) -> FloatArray:
    """Numeric population sampling; explicit replacement and local seed."""
    data, n = vector(values), count(samples)
    if not replace and n > len(data):
        invalid("Cannot sample more than population without replacement.")
    indices = generator(seed).choice(len(data), size=n, replace=replace)
    return data[indices]
