"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.unstructured_mesh
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.unstructured_mesh foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.mesh.quality import polygon_quality
from numerics.mesh.structured_mesh import IntArray
from numerics.utilities.numerical_checks import FloatArray, invalid, matrix


@dataclass(frozen=True, slots=True)
class UnstructuredMesh:
    """Real 2D data/connectivity contract, not an automatic mesh generator."""

    nodes: FloatArray
    cells: IntArray

    @classmethod
    def build(cls, nodes: ArrayLike, cells: ArrayLike) -> UnstructuredMesh:
        x = matrix(nodes)
        raw = np.asarray(cells)
        if (
            x.shape[1] != 2
            or raw.ndim != 2
            or raw.shape[0] == 0
            or raw.shape[1] not in (3, 4)
            or raw.dtype.kind not in "iu"
        ):
            invalid(
                "Unstructured mesh requires 2D nodes and integer triangle/quad connectivity."
            )
        c = np.array(raw, dtype=np.int64, copy=True)
        if (
            np.any(c < 0)
            or np.any(c >= len(x))
            or any(len(set(row)) != len(row) for row in c)
        ):
            invalid("Cell indices must be unique within cells and in range.")
        polygon_quality(x, c)
        x.setflags(write=False)
        c.setflags(write=False)
        return cls(x, c)

    def to_json(self) -> str:
        return json.dumps(
            {
                "kind": "unstructured",
                "nodes": self.nodes.tolist(),
                "cells": self.cells.tolist(),
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
