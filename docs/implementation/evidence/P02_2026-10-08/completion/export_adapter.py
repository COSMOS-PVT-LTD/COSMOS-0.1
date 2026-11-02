"""Explicit zero-area export conditioning. No vertex displacement or area threshold."""
import hashlib
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_benchmarks import read_stl


class ExportRejected(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def condition(source, target):
    source, target = Path(source), Path(target)
    if target.exists():
        raise ExportRejected("ARTIFACT_EXISTS", "Refusing to overwrite an export")
    try:
        triangles, normals = read_stl(source, strict_normals=False)
    except (ValueError, OSError) as error:
        raise ExportRejected("STL_INPUT", "Source STL is missing, nonfinite or lacks explicit metre units") from error
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    length = np.linalg.norm(cross, axis=1)
    keep = length != 0.0
    removed = int(np.count_nonzero(~keep))
    if removed > len(triangles) * .01 or not keep.any():
        raise ExportRejected("EXCESS_DEGENERACY", "Zero-area removal exceeds the bounded 1% fixture profile")
    if not np.isfinite(normals[keep]).all():
        raise ExportRejected("NONFINITE_NORMAL", "Nonfinite normals remain on nonzero-area triangles")
    if np.any(np.einsum("ij,ij->i", triangles[~keep, 0], np.cross(triangles[~keep, 1], triangles[~keep, 2])) != 0):
        raise ExportRejected("NONZERO_VOLUME_REMOVAL", "Removed faces would change signed volume")
    dtype = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])
    records = np.zeros(int(keep.sum()), dtype=dtype)
    records["vertices"] = triangles[keep]
    records["normal"] = cross[keep] / length[keep, None]
    original = source.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("xb") as stream:
            stream.write(original[:80] + struct.pack("<I", len(records)) + records.tobytes())
    except FileExistsError as error:
        raise ExportRejected("ARTIFACT_EXISTS", "Refusing to overwrite an export") from error
    return {"profile": "zero-area-only-v1", "sourceSha256": hashlib.sha256(original).hexdigest(),
        "exportSha256": hashlib.sha256(target.read_bytes()).hexdigest(), "sourceTriangleCount": len(triangles),
        "exportTriangleCount": len(records), "exactZeroAreaFacesRemoved": removed,
        "maximumVertexDisplacementM": 0, "areaToleranceM2": 0,
        "nonfiniteSourceNormalsOnRemovedFaces": int(np.count_nonzero(~np.isfinite(normals[~keep]).all(axis=1))),
        "artifactUnit": "m", "geometryRepresentation": "tessellated surface", "cadReady": False}
