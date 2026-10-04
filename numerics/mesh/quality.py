"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.quality
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.quality foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from numerics.mesh.structured_mesh import IntArray, StructuredMesh
from numerics.utilities.numerical_checks import FloatArray, invalid


@dataclass(frozen=True, slots=True)
class MeshQuality:
    minimum_measure: float
    maximum_edge_ratio: float

def structured_quality(mesh: StructuredMesh) -> MeshQuality:
    dx=np.diff(mesh.x)
    if mesh.y is None:
        return MeshQuality(float(dx.min()),float(dx.max()/dx.min()))
    dy=np.diff(mesh.y)
    return MeshQuality(float(dx.min()*dy.min()),float(max(dx.max()/dy.min(),dy.max()/dx.min())))

def polygon_quality(nodes: FloatArray, cells: IntArray) -> MeshQuality:
    """Convex CCW triangles/quads only; reject zero/inverted/concave cells."""
    areas,ratios=[],[]
    for cell in cells:
        points=nodes[cell]
        edges=np.roll(points,-1,axis=0)-points
        cross=edges[:,0]*np.roll(edges,-1,axis=0)[:,1]-edges[:,1]*np.roll(edges,-1,axis=0)[:,0]
        area=.5*float(np.sum(points[:,0]*np.roll(points,-1,axis=0)[:,1]-points[:,1]*np.roll(points,-1,axis=0)[:,0]))
        lengths=np.hypot(edges[:,0],edges[:,1])
        if not np.isfinite(area) or area<=0 or np.any(cross<=0) or np.any(lengths<=0):
            invalid("Mesh cells must be finite nondegenerate convex CCW polygons.")
        areas.append(area)
        ratios.append(float(lengths.max()/lengths.min()))
    return MeshQuality(min(areas),max(ratios))
