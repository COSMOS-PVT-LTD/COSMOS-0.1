"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.diffusion
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.diffusion foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.utilities.numerical_checks import finite, positive


def flux(left: float, right: float, distance: float, diffusivity: float) -> float:
    """Signed diffusive flux -k du/dx; positive k and center/boundary distance."""
    l, r, d, k = finite(left), finite(right), positive(distance), positive(diffusivity)
    return finite(-k * (r - l) / d)
