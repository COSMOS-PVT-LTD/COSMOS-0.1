"""Independent SI mesh parsing and analytic software-fixture comparisons.

No PicoGK, OCCT, CadQuery or Gmsh imports. Sample distances are not certified
Hausdorff distance, self-intersection detection, manufacturing or physical validation.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from systems.contracts.geometry._wire import require

STL_RECORD = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attribute", "<u2")])


class SurfaceReference(Protocol):
    """Read-only independent reference, not a backend acceptance authority."""
    @property
    def operation(self) -> str: ...
    @property
    def radius_m(self) -> float: ...
    @property
    def volume_m3(self) -> float: ...
    @property
    def centroid_m(self) -> Any: ...
    def sdf(self, points: Any) -> Any: ...
    def surface_samples(self) -> Any: ...


def read_stl(path: Path, *, allow_bad_normals: bool = False):
    require(path.is_file() and not path.is_symlink() and 84 <= path.stat().st_size <= 64 * 1024**2, "INVALID_STL", "Invalid/oversized STL file")
    data = path.read_bytes()
    require(b"UNITS= m" in data[:80], "INVALID_UNIT", "STL must explicitly declare metre coordinates")
    count = int.from_bytes(data[80:84], "little")
    require(0 < count <= 200_000 and len(data) == 84 + 50 * count, "INVALID_STL", "Triangle count/byte length exceeds the 200k-triangle qualified QA bound")
    records = np.frombuffer(data, STL_RECORD, count=count, offset=84)
    tris = records["vertices"].astype(np.float64)
    normals = records["normal"].astype(np.float64)
    require(bool(np.isfinite(tris).all()) and (allow_bad_normals or bool(np.isfinite(normals).all())), "NONFINITE", "Nonfinite STL data")
    return data, tris, normals


def condition_exact_zero_faces(source: Path, target: Path) -> dict[str, Any]:
    """Explicit profile, identical surviving vertices. No epsilon/weld/smoothing."""
    require(not target.exists() and target.parent.resolve() == source.parent.resolve(), "ARTIFACT_EXISTS", "Refuse overwrite/alternate conditioning directory")
    data, tris, _ = read_stl(source, allow_bad_normals=True)
    cross = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    keep = np.any(cross != 0, axis=1)
    removed = len(tris) - int(keep.sum())
    require(bool(keep.any()) and removed / len(tris) <= .01, "EXCESS_DEGENERACY", "Exact-zero conditioning exceeded explicit refusal ceiling")
    records = np.frombuffer(data, STL_RECORD, offset=84).copy()[keep]
    retained = cross[keep]
    records["normal"] = retained / np.linalg.norm(retained, axis=1)[:, None]
    require(bool(np.isfinite(records["normal"]).all()) and np.array_equal(records["vertices"].astype(np.float64), tris[keep]), "CONDITIONING_FAILED", "Conditioning changed vertices or retained invalid faces")
    output = data[:80] + int(keep.sum()).to_bytes(4, "little") + records.tobytes()
    with target.open("xb") as stream:
        stream.write(output)
    return {"profile": "exact_zero_faces_v1", "source_export_sha256": hashlib.sha256(data).hexdigest(),
            "conditioned_export_sha256": hashlib.sha256(output).hexdigest(), "removed_exact_zero_faces": removed,
            "surviving_vertices_identical": True, "positive_area_epsilon": None, "voxel_refinement": False}


@dataclass(frozen=True, slots=True)
class FixtureReference:
    """Predeclared synthetic analytic reference, never an arbitrary design policy."""
    operation: str
    radius_m: float = .01
    separation_m: float = .01

    def __post_init__(self):
        require(self.operation in {"sphere", "cylinder", "box", "union", "difference", "intersection", "self_union"}
                and self.radius_m == .01 and self.separation_m == .01, "UNSUPPORTED_REFERENCE", "Only the predeclared P07 analytic fixtures are approved by this software policy")

    @property
    def volume_m3(self) -> float:
        r, d = self.radius_m, self.separation_m
        sphere = 4 * math.pi * r**3 / 3
        overlap = math.pi * (4 * r + d) * (2 * r - d)**2 / 12
        return {"sphere": sphere, "self_union": sphere, "union": 2 * sphere - overlap,
                "difference": sphere - overlap, "intersection": overlap,
                "cylinder": math.pi * r**2 * .02, "box": .02 * .03 * .04}[self.operation]

    @property
    def centroid_m(self):
        if self.operation in {"union", "intersection"}:
            return np.array([self.separation_m / 2, 0, 0])
        if self.operation == "difference":
            overlap = 4 * math.pi * self.radius_m**3 / 3 - self.volume_m3
            return np.array([-overlap * self.separation_m / (2 * self.volume_m3), 0, 0])
        return np.zeros(3)

    @property
    def bounds_m(self):
        r, d = self.radius_m, self.separation_m
        if self.operation == "box":
            return np.array([-.01, -.015, -.02, .01, .015, .02])
        if self.operation == "intersection":
            c = math.sqrt(r**2 - (d / 2)**2)
            return np.array([d-r, -c, -c, r, c, c])
        right = d+r if self.operation == "union" else (d/2 if self.operation == "difference" else r)
        return np.array([-r, -r, -r, right, r, r])

    def sdf(self, points):
        if self.operation == "box":
            q = np.abs(points) - [.01, .015, .02]
            return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0)
        if self.operation == "cylinder":
            q = np.column_stack((np.linalg.norm(points[:, :2], axis=1) - .01, np.abs(points[:, 2]) - .01))
            return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(np.max(q, axis=1), 0)
        a = np.linalg.norm(points, axis=1) - self.radius_m
        b = np.linalg.norm(points - [self.separation_m, 0, 0], axis=1) - self.radius_m
        return {"sphere": a, "self_union": a, "union": np.minimum(a, b), "difference": np.maximum(a, -b), "intersection": np.maximum(a, b)}[self.operation]

    def surface_samples(self):
        if self.operation == "box":
            points = []
            half = np.array([.01, .015, .02])
            for axis in range(3):
                for sign in (-1, 1):
                    others = [i for i in range(3) if i != axis]
                    for first in np.linspace(-half[others[0]], half[others[0]], 5):
                        for second in np.linspace(-half[others[1]], half[others[1]], 5):
                            p = np.zeros(3); p[axis] = sign*half[axis]; p[others] = [first, second]
                            points.append(p)
            return np.array(points)
        if self.operation == "cylinder":
            points = [[.01*math.cos(a), .01*math.sin(a), z] for a in np.arange(24)*2*math.pi/24 for z in np.linspace(-.01, .01, 5)]
            points += [[r*math.cos(a), r*math.sin(a), z] for r in np.linspace(0, .01, 5) for a in np.arange(24)*2*math.pi/24 for z in (-.01, .01)]
            return np.array(points)
        # Fixed independent latitude/longitude sampling; only spherical fixtures.
        azimuth = np.arange(24) * (2 * math.pi / 24)
        polar = np.arange(1, 12) * (math.pi / 12)
        points = np.array([[math.sin(p) * math.cos(a), math.sin(p) * math.sin(a), math.cos(p)] for p in polar for a in azimuth]) * self.radius_m
        points = np.vstack((points, [[0, 0, self.radius_m], [0, 0, -self.radius_m]]))
        if self.operation not in {"sphere", "self_union"}:
            points = np.vstack((points, points + [self.separation_m, 0, 0]))
        return points[np.abs(self.sdf(points)) <= 1e-14]  # Analytic sample membership roundoff, not an acceptance tolerance.


def distances_to_triangles(points, triangles, *, ceiling_m=None, check_budget=None):
    """Bounded batches of exact planar point/triangle distances, no vertex proxy."""
    output = np.full(len(points), np.inf)
    triangle_min = triangles.min(axis=1) if ceiling_m is not None else None
    triangle_max = triangles.max(axis=1) if ceiling_m is not None else None
    for p0 in range(0, len(points), 16):
        if check_budget is not None:
            check_budget()
        p = points[p0:p0 + 16, None, :]
        best = np.full(len(p), np.inf)
        candidates = triangles
        if ceiling_m is not None:
            # Conservative batch AABB rejection: every triangle closer than the
            # explicit pass ceiling is retained. Never a nearest-vertex proxy.
            candidates = triangles[((triangle_max >= p[:, 0].min(axis=0) - ceiling_m)
                                    & (triangle_min <= p[:, 0].max(axis=0) + ceiling_m)).all(axis=1)]
        for t0 in range(0, len(candidates), 4096):
            if check_budget is not None:
                check_budget()
            t = candidates[t0:t0 + 4096]
            a, b, c = t[:, 0], t[:, 1], t[:, 2]
            ab, ac, ap = b-a, c-a, p-a
            normal = np.cross(ab, ac)
            normal2 = np.einsum("ij,ij->i", normal, normal)
            height = np.einsum("ptj,tj->pt", ap, normal) / normal2
            projection = ap - height[:, :, None] * normal
            d00 = np.einsum("ij,ij->i", ab, ab); d01 = np.einsum("ij,ij->i", ab, ac); d11 = np.einsum("ij,ij->i", ac, ac)
            d20 = np.einsum("ptj,tj->pt", projection, ab); d21 = np.einsum("ptj,tj->pt", projection, ac)
            denominator = d00*d11-d01*d01
            v = (d11*d20-d01*d21)/denominator; w = (d00*d21-d01*d20)/denominator
            inside = (v >= 0) & (w >= 0) & (v+w <= 1)
            distance2 = np.where(inside, height**2 * normal2, np.inf)
            for first, second in ((a, b), (b, c), (c, a)):
                edge = second-first
                alpha = np.clip(np.einsum("ptj,tj->pt", p-first, edge) / np.einsum("ij,ij->i", edge, edge), 0, 1)
                delta = p-first-alpha[:, :, None]*edge
                distance2 = np.minimum(distance2, np.einsum("ptj,ptj->pt", delta, delta))
            best = np.minimum(best, np.sqrt(distance2.min(axis=1)))
        output[p0:p0 + len(p)] = best
    return output


def audit_mesh(path: Path, reference: SurfaceReference, *, voxel_m: float | None, export_tolerance_m: float,
               euler_characteristic: int = 2, volume_ceiling: float | None = None,
               centroid_ceiling_m: float | None = None, distance_ceiling_m: float | None = None,
               check_budget=None, forward_ceiling_m: float | None = None) -> dict[str, Any]:
    require(math.isfinite(export_tolerance_m) and export_tolerance_m > 0
            and (voxel_m is None or math.isfinite(voxel_m) and voxel_m > 0), "INVALID_TOLERANCE", "QA requires explicit positive finite SI tolerances")
    require(type(euler_characteristic) is int and -512 <= euler_characteristic <= 2 and euler_characteristic % 2 == 0
            and all(v is None or type(v) in (int, float) and math.isfinite(v) and v > 0 for v in (volume_ceiling, centroid_ceiling_m, distance_ceiling_m, forward_ceiling_m)),
            "INVALID_TOLERANCE", "Supported topology and explicit positive finite QA ceilings required")
    if check_budget is not None:
        check_budget()
    _, tris, normals = read_stl(path, allow_bad_normals=True)
    cross = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(cross, axis=1)
    degenerate = int((lengths == 0).sum())
    vertices, ids = np.unique(tris.reshape(-1, 3), axis=0, return_inverse=True)
    faces = ids.reshape(-1, 3)
    directed = np.vstack((faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]))
    edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
    orientation = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
    parents = np.arange(len(vertices))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]; i = parents[i]
        return i
    for a, b in edges:
        parents[find(a)] = find(b)
    components = len({find(i) for i in range(len(vertices))})
    six_volume = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2]))
    volume = float(six_volume.sum() / 6)
    require(volume > 0 and math.isfinite(volume), "INVALID_TOPOLOGY", "Mesh has no positive finite enclosed signed volume")
    centroid = (six_volume[:, None] * tris.sum(axis=1)).sum(axis=0) / (24 * volume)
    topology = (degenerate == 0 and bool(np.isfinite(normals).all()) and bool((counts == 2).all())
                and bool((orientation == 0).all()) and components == 1 and len(vertices)-len(edges)+len(faces) == euler_characteristic
                and len(np.unique(np.sort(faces, axis=1), axis=0)) == len(faces) and volume > 0)
    if topology:
        alignment = np.einsum("ij,ij->i", normals, cross / lengths[:, None])
        topology = bool((alignment > .999).all())
    samples = np.vstack((vertices, tris.mean(axis=1)))
    forward = np.abs(reference.sdf(samples))
    reverse = distances_to_triangles(reference.surface_samples(), tris, ceiling_m=distance_ceiling_m, check_budget=check_budget) if topology else np.array([])
    require(np.isfinite(reverse).all(), "SURFACE_DISTANCE_OUTSIDE_CEILING", "Some reference samples have no candidate triangles within the conservative explicit QA search ceiling; no successful distance is invented")
    h = voxel_m if voxel_m is not None else export_tolerance_m
    volume_limit = 2 * (h / reference.radius_m)**2 + .0005 if voxel_m is not None else 3 * h / reference.radius_m
    centroid_limit = 2 * h if voxel_m is not None else 2 * export_tolerance_m
    forward_limit = 1.5 * h if voxel_m is not None else 1.5 * export_tolerance_m
    reverse_limit = 2 * h if voxel_m is not None else 2 * export_tolerance_m
    if volume_ceiling is not None:
        volume_limit = volume_ceiling
    if centroid_ceiling_m is not None:
        centroid_limit = centroid_ceiling_m
    if distance_ceiling_m is not None:
        forward_limit = reverse_limit = distance_ceiling_m
    if forward_ceiling_m is not None:
        forward_limit = forward_ceiling_m
    volume_error = abs(volume-reference.volume_m3) / reference.volume_m3
    centroid_error = float(np.linalg.norm(centroid-reference.centroid_m))
    result = {"topology_pass": topology, "triangle_count": len(tris), "components": components, "degenerate_faces": degenerate,
              "nonmanifold_edges": int((counts != 2).sum()), "orientation_errors": int((orientation != 0).sum()),
              "volume_m3": volume, "relative_volume_error": volume_error, "relative_volume_limit": volume_limit,
              "centroid_m": centroid.tolist(), "centroid_error_m": centroid_error, "centroid_limit_m": centroid_limit,
              "forward_sample_count": len(forward), "reverse_sample_count": len(reverse),
              "forward_max_m": float(forward.max()), "forward_p95_m": float(np.percentile(forward, 95)), "forward_limit_m": forward_limit,
              "reverse_max_m": float(reverse.max()) if len(reverse) else None, "reverse_p95_m": float(np.percentile(reverse, 95)) if len(reverse) else None, "reverse_limit_m": reverse_limit,
              "bidirectional_sampling_scope": "vertices+face centroids to analytic SDF; fixed analytic sphere samples to planar triangles; not certified Hausdorff",
              "units": "m", "physical_validation_claimed": False}
    result["euler_characteristic"] = len(vertices) - len(edges) + len(faces)
    result["expected_euler_characteristic"] = euler_characteristic
    result["dimensions_pass"] = bool(topology and volume_error <= volume_limit and centroid_error <= centroid_limit and forward.max() <= forward_limit and len(reverse) and reverse.max() <= reverse_limit)
    result["pass"] = bool(topology and result["dimensions_pass"])
    return result
