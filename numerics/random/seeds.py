"""
COSMOS Rocket Propulsion Platform

Module: numerics.random.seeds
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral random.seeds foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.utilities.numerical_checks import count


def validate(seed: int) -> int:
    return count(seed,"seed",minimum=0)

def child_seeds(seed: int, jobs: int) -> tuple[int,...]:
    """Independent SeedSequence child streams; stable input job ordering."""
    sequence=np.random.SeedSequence(validate(seed))
    return tuple(int(child.generate_state(1,dtype=np.uint64)[0]) for child in sequence.spawn(count(jobs)))
