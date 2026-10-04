"""
COSMOS Rocket Propulsion Platform

Module: numerics.mesh.connectivity
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral mesh.connectivity foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from numerics.utilities.numerical_checks import count, invalid


@dataclass(frozen=True, slots=True)
class Connectivity:
    faces: tuple[tuple[int, ...], ...]
    cell_faces: tuple[tuple[int, ...], ...]
    face_cells: tuple[tuple[int, ...], ...]


def build(cells: ArrayLike, node_count: int) -> Connectivity:
    """Unique faces and at most two adjacent cells; no nonmanifold acceptance."""
    n = count(node_count)
    c = np.asarray(cells)
    if (
        c.ndim != 2
        or c.size == 0
        or c.shape[1] not in (2, 3, 4)
        or c.dtype.kind not in "iu"
    ):
        invalid("Connectivity requires integer interval/triangle/quad cells.")
    if np.any(c < 0) or np.any(c >= n) or any(len(set(row)) != len(row) for row in c):
        invalid("Connectivity node index out of range or repeated.")
    lookup: dict[tuple[int, ...], int] = {}
    faces: list[tuple[int, ...]] = []
    neighbors: list[list[int]] = []
    cell_faces: list[tuple[int, ...]] = []
    for index, cell in enumerate(c):
        local = (
            [(int(i),) for i in cell]
            if len(cell) == 2
            else [
                tuple(sorted((int(cell[j]), int(cell[(j + 1) % len(cell)]))))
                for j in range(len(cell))
            ]
        )
        indices = []
        for face in local:
            if face not in lookup:
                lookup[face] = len(faces)
                faces.append(face)
                neighbors.append([])
            number = lookup[face]
            neighbors[number].append(index)
            if len(neighbors[number]) > 2:
                invalid("Nonmanifold face belongs to more than two cells.")
            indices.append(number)
        cell_faces.append(tuple(indices))
    return Connectivity(
        tuple(faces), tuple(cell_faces), tuple(tuple(v) for v in neighbors)
    )
