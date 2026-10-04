"""
COSMOS Rocket Propulsion Platform

Module: numerics.automatic_differentiation.gradients
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral automatic_differentiation.gradients foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike

from numerics.automatic_differentiation.forward_mode import Dual
from numerics.utilities.numerical_checks import FloatArray, failure, finite, vector

ADFunction = Callable[[tuple[Dual,...]],Dual | float]

def variables(point: ArrayLike) -> tuple[Dual,...]:
    x=vector(point)
    eye=np.eye(len(x))
    return tuple(Dual(float(value),eye[i]) for i,value in enumerate(x))

def gradient(function: ADFunction, point: ArrayLike) -> FloatArray:
    """One multivariate dual evaluation with basis-seeded tangents."""
    inputs=variables(point)
    result=function(inputs)
    if isinstance(result,Dual):
        if len(result.tangent)!=len(inputs):
            failure("AD gradient callback changed tangent dimension.")
        return result.tangent.copy()
    finite(result,"constant AD output")
    return np.zeros(len(inputs))
