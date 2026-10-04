"""
COSMOS Rocket Propulsion Platform

Module: numerics.finite_volume.source_terms
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral finite_volume.source_terms foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from numpy.typing import ArrayLike

from numerics.finite_volume.control_volume import ControlVolumes
from numerics.utilities.numerical_checks import (
    FloatArray,
    finite_output,
    same_shape,
    vector,
)


def assemble(cells: ControlVolumes, source: ArrayLike) -> FloatArray:
    """Cell-centered source density times exact cell volume (unit cross-section)."""
    s = vector(source)
    same_shape(s, cells.widths)
    return finite_output(s * cells.widths)
