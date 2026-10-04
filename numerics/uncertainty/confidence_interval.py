"""
COSMOS Rocket Propulsion Platform

Module: numerics.uncertainty.confidence_interval
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral uncertainty.confidence_interval foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from numpy.typing import ArrayLike

from numerics.uncertainty.statistics import summarize
from numerics.utilities.numerical_checks import finite, invalid, positive


@dataclass(frozen=True, slots=True)
class ConfidenceInterval:
    lower: float
    upper: float
    confidence: float
    method: str


def mean_interval(
    values: ArrayLike,
    *,
    confidence: float = 0.95,
    known_normal_sigma: float | None = None,
) -> ConfidenceInterval:
    """IID mean interval: exact normal with known sigma, else large-sample normal approximation."""
    c = finite(confidence)
    if not 0 < c < 1:
        invalid("Confidence must be strictly between zero and one.")
    stats = summarize(values)
    if known_normal_sigma is None:
        if stats.samples < 30:
            invalid(
                "Estimated-sigma normal approximation requires >=30 IID samples; small-sample t is deferred."
            )
        error = stats.standard_error
        method = "large-sample-normal-approximation-IID"
    else:
        error = positive(known_normal_sigma) / math.sqrt(stats.samples)
        method = "known-sigma-normal-IID"
    radius = NormalDist().inv_cdf((1 + c) / 2) * error
    return ConfidenceInterval(
        finite(stats.mean - radius), finite(stats.mean + radius), c, method
    )
