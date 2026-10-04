"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.fluxes
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.fluxes foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

from numerics.finite_difference.boundary_conditions import DirichletBoundary
from numerics.finite_volume.control_volume import ControlVolumes
from numerics.finite_volume.discretization import face_coefficients
from numerics.utilities.numerical_checks import (
    FloatArray,
    finite_output,
    same_shape,
    vector,
)


def face_fluxes(
    cells: ControlVolumes,
    values: ArrayLike,
    boundary: DirichletBoundary,
    *,
    diffusivity: float,
    velocity: float = 0.0,
) -> FloatArray:
    u = vector(values)
    same_shape(u, cells.centers)
    a, b = face_coefficients(
        cells, boundary, diffusivity=diffusivity, velocity=velocity
    )
    return finite_output(a @ u + b)


def cell_outward_fluxes(faces: ArrayLike) -> FloatArray:
    """Each cell has (-west,+east); shared internal values cancel exactly."""
    f = vector(faces)
    return np.column_stack((-f[:-1], f[1:]))
