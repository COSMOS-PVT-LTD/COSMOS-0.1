"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.discretization
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.discretization foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_volume.control_volume import ControlVolumes
from numerics.utilities.numerical_checks import (
    FloatArray,
    finite,
    finite_output,
    positive,
)


def face_coefficients(cells: ControlVolumes, boundary: DirichletBoundary, *,
                      diffusivity: float, velocity: float = 0.) -> tuple[FloatArray,FloatArray]:
    """One signed flux expression per shared face; diffusion plus first-order upwind."""
    k,v = positive(diffusivity),finite(velocity)
    n=len(cells.centers)
    a,b=np.zeros((n+1,n)),np.zeros(n+1)
    dl,dr = cells.centers[0]-cells.faces[0],cells.faces[-1]-cells.centers[-1]
    a[0,0]=-k/dl+(min(0, v))
    b[0]=(k/dl+(max(v, 0)))*boundary.left
    a[-1,-1]=k/dr+(max(v, 0))
    b[-1]=(-k/dr+(min(0, v)))*boundary.right
    for face in range(1,n):
        d=cells.centers[face]-cells.centers[face-1]
        a[face,face-1]=k/d+(max(v, 0))
        a[face,face]=-k/d+(min(0, v))
    return finite_output(a),finite_output(b)

def assemble(cells: ControlVolumes, boundary: DirichletBoundary, *, diffusivity: float,
             velocity: float = 0.) -> tuple[FloatArray,FloatArray]:
    a,b=face_coefficients(cells,boundary,diffusivity=diffusivity,velocity=velocity)
    return a[1:]-a[:-1],b[1:]-b[:-1]
