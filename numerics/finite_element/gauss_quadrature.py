"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_element.gauss_quadrature
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_element.gauss_quadrature foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.finite_element.elements import LinearElement
from numerics.integration.gaussian import legendre_rule
from numerics.utilities.numerical_checks import FloatArray, finite_output


def points(element: LinearElement, *, order: int = 2) -> tuple[FloatArray, FloatArray]:
    """Physical-coordinate points and integration weights, including Jacobian."""
    xi, w = legendre_rule(order)
    x = xi * element.length / 2 + element.left / 2 + element.right / 2
    return finite_output(x), finite_output(w * element.length / 2)
