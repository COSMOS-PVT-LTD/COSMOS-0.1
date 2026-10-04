"""
COSMOS Rocket Propulsion Platform

Module: numerics.random.distributions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral random.distributions foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.random.random_generators import generator
from numerics.utilities.numerical_checks import (
    FloatArray,
    count,
    finite,
    finite_output,
    invalid,
    positive,
)


def uniform(lower: float, upper: float, samples: int, *, seed: int) -> FloatArray:
    a,b,n=finite(lower),finite(upper),count(samples)
    if b<=a:
        invalid("Uniform endpoints must increase.")
    return finite_output(generator(seed).uniform(a,b,n))

def normal(mean: float, standard_deviation: float, samples: int, *, seed: int) -> FloatArray:
    mu,sigma,n=finite(mean),positive(standard_deviation),count(samples)
    return finite_output(generator(seed).normal(mu,sigma,n))
