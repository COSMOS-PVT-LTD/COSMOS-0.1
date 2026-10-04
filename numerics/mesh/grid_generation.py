"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.grid_generation
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.grid_generation foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.mesh.structured_mesh import StructuredMesh
from numerics.utilities.numerical_checks import count, finite, invalid


def uniform_1d(lower: float, upper: float, cells: int) -> StructuredMesh:
    a,b,n=finite(lower),finite(upper),count(cells)
    if b<=a:
        invalid("Grid extent must increase.")
    return StructuredMesh.build(np.linspace(a,b,n+1))

def uniform_2d(x_bounds: tuple[float,float], y_bounds: tuple[float,float],
               x_cells: int, y_cells: int) -> StructuredMesh:
    x=uniform_1d(*x_bounds,x_cells).x
    y=uniform_1d(*y_bounds,y_cells).x
    return StructuredMesh.build(x,y)
