"""Versioned native-mm -> SI binary STL encoding, not a topology repair service.

Only exactly zero-area encoded triangles may be excluded (bounded to 1%).
No positive-area epsilon, welding, smoothing or replacement geometry is used.
Every surviving vertex is the native float32 vertex times the declared SI scale.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np

from systems.contracts.geometry._wire import require

PROFILE = "occt_native_mm_si_stl_v2"
RECORD = np.dtype([("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])


def encode_si_stl(source: Path, target: Path) -> dict[str, Any]:
    require(not target.exists() and source.is_file() and not source.is_symlink(), "ARTIFACT_EXISTS", "STL encoding requires a new target and owned input")
    raw = source.read_bytes()
    require(84 < len(raw) <= 64 * 1024**2, "INVALID_STL", "Invalid bounded native STL")
    count = int.from_bytes(raw[80:84], "little")
    require(0 < count <= 200_000 and len(raw) == 84 + 50 * count, "INVALID_STL", "Native STL exceeds qualified triangle bound")
    records = np.frombuffer(raw, RECORD, offset=84).copy()
    require(bool(np.isfinite(records["vertices"]).all()), "NONFINITE_GEOMETRY", "Nonfinite native STL vertices")
    records["vertices"] = records["vertices"].astype(np.float64) * .001
    vertices = records["vertices"].astype(np.float64)
    cross = np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0])
    keep = np.any(cross != 0, axis=1)
    removed = int((~keep).sum())
    require(bool(keep.any()) and removed <= .01 * count, "EXCESS_DEGENERACY", "Native STL zero-area exclusion exceeds declared 1% ceiling")
    records = records[keep]
    cross = cross[keep]
    records["normal"] = cross / np.linalg.norm(cross, axis=1)[:, None]
    records["attribute"] = 0
    encoded = (b"COSMOS UNITS= m " + PROFILE.encode()).ljust(80, b" ") + len(records).to_bytes(4, "little") + records.tobytes()
    with target.open("xb") as stream:
        stream.write(encoded)
    return {"stl_encoding_profile": PROFILE, "native_triangle_count": count,
            "excluded_exact_zero_area_triangles": removed, "positive_area_epsilon": None,
            "vertex_welding": False, "surviving_si_vertices_unchanged": True,
            "native_stl_sha256": hashlib.sha256(raw).hexdigest(),
            "chord_budget_fraction": .6, "native_mesh_unit": "mm", "stl_file_unit": "m"}
