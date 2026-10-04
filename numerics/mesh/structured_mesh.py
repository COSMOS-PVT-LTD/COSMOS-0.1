"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.structured_mesh
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.structured_mesh foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from numerics.utilities.numerical_checks import FloatArray, grid, invalid

IntArray = NDArray[np.int64]

@dataclass(frozen=True, slots=True)
class StructuredMesh:
    """Rectilinear 1D intervals or 2D CCW quads; x index is fastest."""
    x: FloatArray
    y: FloatArray | None
    nodes: FloatArray
    cells: IntArray

    @classmethod
    def build(cls, x_nodes: ArrayLike, y_nodes: ArrayLike | None = None) -> StructuredMesh:
        x=grid(x_nodes)
        y=None if y_nodes is None else grid(y_nodes)
        if y is None:
            nodes=x[:,None].copy()
            cells=np.array([[i,i+1] for i in range(len(x)-1)],dtype=np.int64)
        else:
            nodes=np.array([[a,b] for b in y for a in x],dtype=float)
            nx=len(x)
            cells=np.array([[j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i]
                            for j in range(len(y)-1) for i in range(nx-1)],dtype=np.int64)
        for value in (x,y,nodes,cells):
            if value is not None:
                value.setflags(write=False)
        return cls(x,y,nodes,cells)

    def node_index(self, i: int, j: int = 0) -> int:
        if isinstance(i,bool) or isinstance(j,bool) or not isinstance(i,int) or not isinstance(j,int):
            invalid("Mesh indices must be integers.")
        ny=1 if self.y is None else len(self.y)
        if not 0<=i<len(self.x) or not 0<=j<ny:
            invalid("Mesh node index out of bounds.")
        return j*len(self.x)+i

    def to_json(self) -> str:
        """Canonical deterministic serialization, never an implicit disk write."""
        return json.dumps({"kind":"structured","x":self.x.tolist(),
                           "y":None if self.y is None else self.y.tolist(),
                           "nodes":self.nodes.tolist(),"cells":self.cells.tolist()},
                          sort_keys=True,separators=(",",":"),allow_nan=False)
