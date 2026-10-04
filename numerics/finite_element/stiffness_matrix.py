"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.stiffness_matrix
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.stiffness_matrix foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.finite_element.elements import LinearElement
from numerics.utilities.numerical_checks import FloatArray, finite_output, positive


def stiffness(element: LinearElement, coefficient: float = 1.) -> FloatArray:
    """Exact integral of constant k B^T B for a normalized scalar equation."""
    k=positive(coefficient)
    return finite_output(k/element.length*np.array([[1.,-1.],[-1.,1.]]))
