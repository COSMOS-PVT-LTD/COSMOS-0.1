"""
COSMOS Rocket Propulsion Platform

Module: numerics.ode.adaptive_step
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral ode.adaptive_step foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.numerical_checks import finite, invalid, positive


def next_step(step: float, error_ratio: float, *, minimum: float, maximum: float) -> float:
    """Safety-scaled local fourth-order error controller, bounded factor [0.2,5]."""
    h,e = positive(step),finite(error_ratio)
    lo,hi = positive(minimum),positive(maximum)
    if lo > hi or e < 0:
        invalid("Invalid adaptive bounds/error ratio.")
    factor = 5.0 if e == 0 else min(5.,max(.2,.9*e**(-.2)))
    return min(hi,max(lo,h*factor))
