"""
COSMOS Rocket Propulsion Platform

Module: numerics.random.random_generators
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral random.random_generators foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.random.seeds import validate


def generator(seed: int) -> np.random.Generator:
    """Explicit PCG64, never a mutable global PRNG or wall-clock seed."""
    return np.random.Generator(np.random.PCG64(validate(seed)))
