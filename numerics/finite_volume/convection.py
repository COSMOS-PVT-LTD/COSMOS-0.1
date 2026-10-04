"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.convection
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.convection foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numerics.finite_volume.interpolation import upwind
from numerics.utilities.numerical_checks import finite


def flux(left: float, right: float, velocity: float) -> float:
    """Signed upwind convective flux, positive in increasing coordinate direction."""
    v = finite(velocity)
    return finite(v*upwind(left,right,v))
