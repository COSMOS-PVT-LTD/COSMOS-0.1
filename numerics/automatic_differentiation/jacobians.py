"""
COSMOS Rocket Propulsion Platform

Module: numerics.automatic_differentiation.jacobians
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral automatic_differentiation.jacobians foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from numpy.typing import ArrayLike

from numerics.automatic_differentiation.forward_mode import Dual
from numerics.automatic_differentiation.gradients import variables
from numerics.utilities.numerical_checks import FloatArray, failure, finite

ADVectorFunction = Callable[[tuple[Dual,...]],Sequence[Dual | float]]

def jacobian(function: ADVectorFunction, point: ArrayLike) -> FloatArray:
    """Forward-mode Jacobian, arbitrary positive output dimension."""
    inputs=variables(point)
    outputs=function(inputs)
    if len(outputs)==0:
        failure("AD vector output must be nonempty.")
    rows=[]
    for value in outputs:
        if isinstance(value,Dual):
            if len(value.tangent)!=len(inputs):
                failure("AD Jacobian callback changed tangent dimension.")
            rows.append(value.tangent)
        else:
            finite(value,"constant AD output")
            rows.append(np.zeros(len(inputs)))
    return np.array(rows)
