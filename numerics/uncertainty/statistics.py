"""
COSMOS Rocket Propulsion Platform

Module: numerics.uncertainty.statistics
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral uncertainty.statistics foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import failure, invalid, vector


@dataclass(frozen=True, slots=True)
class SampleStatistics:
    samples: int
    mean: float
    variance: float
    standard_error: float

def summarize(values: ArrayLike) -> SampleStatistics:
    """Unbiased sample variance; requires >=2 finite real observations."""
    data=vector(values)
    if len(data)<2:
        invalid("Sample variance requires >=2 observations.")
    with np.errstate(over="ignore",invalid="ignore"):
        mean,variance=float(data.mean()),float(data.var(ddof=1))
    if not math.isfinite(mean) or not math.isfinite(variance):
        failure("Sample statistics are unrepresentable; rescale data.")
    return SampleStatistics(len(data),mean,variance,math.sqrt(variance/len(data)))
