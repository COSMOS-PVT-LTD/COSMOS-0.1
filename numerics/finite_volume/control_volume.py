"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.control_volume
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.control_volume foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import FloatArray, finite_output, grid


@dataclass(frozen=True, slots=True)
class ControlVolumes:
    """1D ordered structured cells; one shared face between neighbors."""

    faces: FloatArray
    centers: FloatArray
    widths: FloatArray

    @classmethod
    def build(cls, faces: ArrayLike) -> ControlVolumes:
        edges = grid(faces)
        centers, widths = finite_output(edges[:-1] / 2 + edges[1:] / 2), np.diff(edges)
        for data in (edges, centers, widths):
            data.setflags(write=False)
        return cls(edges, centers, widths)
