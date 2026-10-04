"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.refinement
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.refinement foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import numpy as np

from numerics.mesh.structured_mesh import StructuredMesh
from numerics.utilities.numerical_checks import FloatArray, finite_output


def _bisect(axis: FloatArray) -> FloatArray:
    refined=np.empty(2*len(axis)-1)
    refined[::2]=axis
    refined[1::2]=axis[:-1]/2+axis[1:]/2
    return finite_output(refined)

def refine(mesh: StructuredMesh) -> StructuredMesh:
    """Deterministic uniform bisection of each axis; no adaptive/CAD remeshing."""
    return StructuredMesh.build(_bisect(mesh.x),None if mesh.y is None else _bisect(mesh.y))
