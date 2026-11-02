"""Read-only direct mesh QA process. No CAD construction or persistence authority."""

import json
import sys
from hashlib import sha256
from pathlib import Path

import numpy as np

from systems.contracts.geometry import DesignSnapshot, GeometryFeatureGraph
from systems.contracts.geometry._wire import require
from systems.geometry.component_model import from_contracts
from systems.geometry.component_reference import PartReference
from systems.geometry.qa import STL_RECORD
from systems.geometry.qualification_policy import exact, validate
from systems.geometry.surface_discrepancy import (
    TriangleTree,
    sample_surface,
    statistics,
)


def read(name, digest, parts):
    path = Path.cwd() / name
    require(
        path.is_file()
        and not path.is_symlink()
        and 84 < path.stat().st_size <= 256 * 1024**2,
        "R08_FILE",
        "Bounded private original STL required",
    )
    checksum = sha256()
    with path.open("rb") as f:
        header = f.read(84)
        checksum.update(header)
        for block in iter(lambda: f.read(1024**2), b""):
            checksum.update(block)
    count = int.from_bytes(header[80:84], "little")
    require(
        b"UNITS= m" in header[:80]
        and 0 < count <= 4_000_000
        and path.stat().st_size == 84 + 50 * count
        and checksum.hexdigest() == digest,
        "R08_INTEGRITY",
        "Original SI mesh/hash/length mismatch",
    )
    start = 0
    for part in parts:
        require(
            type(part["triangle_start"]) is int
            and part["triangle_start"] == start
            and type(part["triangle_count"]) is int
            and part["triangle_count"] > 0,
            "R08_PARTS",
            "Contiguous complete source-bound triangle ranges required",
        )
        start += part["triangle_count"]
    require(
        start == count,
        "R08_PARTS",
        "All original triangles must be covered exactly once",
    )
    return np.memmap(path, dtype=STL_RECORD, mode="r", offset=84, shape=(count,))


def metrics(tri, ref, policy):
    volume = 0.0
    moment = np.zeros(3)
    area = 0.0
    low = np.full(3, np.inf)
    high = -low
    residual = 0.0
    for i in range(0, len(tri), 16384):
        t = tri[i : i + 16384].astype(float)
        cross = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        length = np.linalg.norm(cross, axis=1)
        require(
            bool(np.isfinite(t).all()) and bool((length > 0).all()),
            "R08_MESH",
            "Nonfinite/degenerate encoded triangles rejected",
        )
        six = np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2]))
        volume += float(six.sum() / 6)
        moment += (six[:, None] * t.sum(axis=1)).sum(axis=0) / 24
        area += float(length.sum() / 2)
        low = np.minimum(low, t.min(axis=(0, 1)))
        high = np.maximum(high, t.max(axis=(0, 1)))
        residual = max(
            residual,
            float(np.abs(ref.sdf(t.reshape(-1, 3))).max()),
            float(np.abs(ref.sdf(t.mean(axis=1))).max()),
        )
    require(
        volume > 0 and np.isfinite(volume),
        "R08_VOLUME",
        "Positive oriented encoded volume required",
    )
    actual = {
        "volume_m3": volume,
        "surface_area_m2": area,
        "centroid_m": (moment / volume).tolist(),
        "bounds_m": np.r_[low, high].tolist(),
        "relative_volume": abs(volume - ref.volume_m3) / ref.volume_m3,
        "relative_area": abs(area - policy["reference_area_m2"])
        / policy["reference_area_m2"],
        "centroid_m_error": float(np.linalg.norm(moment / volume - ref.centroid_m)),
        "bounds_m_error": float(np.abs(np.r_[low, high] - ref.bounds_m).max()),
        "reference_residual_m": residual,
    }
    actual["pass"] = (
        all(
            actual[k] <= policy[k]
            for k in ("relative_volume", "relative_area", "reference_residual_m")
        )
        and actual["centroid_m_error"] <= policy["centroid_m"]
        and actual["bounds_m_error"] <= policy["bounds_m"]
    )
    return actual


def evaluate(value):
    exact(
        value,
        {
            "snapshot_json",
            "graph_json",
            "policy",
            "reference_parts",
            "candidate_parts",
            "reference_sha256",
            "candidate_sha256",
            "compare",
        },
        "worker request",
    )
    plan = from_contracts(
        DesignSnapshot.from_json(value["snapshot_json"]),
        GeometryFeatureGraph.from_json(value["graph_json"]),
    )
    require(
        type(value["compare"]) is bool,
        "R08_FIELDS",
        "Explicit comparison Boolean required",
    )
    policy = validate(value["policy"], plan)
    reference = read(
        "reference.stl", value["reference_sha256"], value["reference_parts"]
    )
    candidate = read(
        "candidate.stl", value["candidate_sha256"], value["candidate_parts"]
    )
    expected = [p.part_id for p in plan.parts]
    require(
        [p["part_id"] for p in value["reference_parts"]]
        == expected
        == [p["part_id"] for p in value["candidate_parts"]],
        "R08_PARTS",
        "Actual representations must preserve exact part order/identity",
    )
    output = []
    limits = {p["part_id"]: p for p in policy["parts"]}
    sampling = policy["sampling"]
    for part, a, b in zip(
        plan.parts, value["reference_parts"], value["candidate_parts"], strict=True
    ):
        p = limits[part.part_id]
        ref = PartReference(plan, part)
        left = reference["vertices"][
            a["triangle_start"] : a["triangle_start"] + a["triangle_count"]
        ]
        right = candidate["vertices"][
            b["triangle_start"] : b["triangle_start"] + b["triangle_count"]
        ]
        measured = metrics(right, ref, p)
        tree = TriangleTree(right)
        # Common-reference samples are separately labelled, never substituted
        # for the direct representation-to-representation comparison below.
        samples = ref.surface_samples()
        take = np.linspace(
            0,
            len(samples) - 1,
            min(len(samples), sampling["samples_per_part"]),
            dtype=int,
        )
        reverse = statistics(
            tree, samples[take], p["reverse_distance_m"], sampling["outlier_limit"]
        )
        critical = []
        for probe in p["critical_features"]:
            answers = [tree.nearest(point) for point in probe["points_m"]]
            span = float(np.linalg.norm(answers[1][1] - answers[0][1]))
            critical.append(
                {
                    "id": probe["id"],
                    "kind": probe["kind"],
                    "pass": bool(
                        all(r[0] <= probe["surface_tolerance_m"] for r in answers)
                        and probe["minimum_m"] <= span <= probe["maximum_m"]
                    ),
                    "measured_span_m": span,
                    "minimum_m": probe["minimum_m"],
                    "maximum_m": probe["maximum_m"],
                    "surface_distances_m": [a[0] for a in answers],
                    "closest_points_m": [a[1].tolist() for a in answers],
                    "triangle_indices": [a[2] for a in answers],
                }
            )
        direct = None
        if value["compare"]:
            points, indices = sample_surface(left, sampling["samples_per_part"])
            forward = statistics(
                tree, points, p["representation_distance_m"], sampling["outlier_limit"]
            )
            del tree
            tree = TriangleTree(left)
            points, other_indices = sample_surface(right, sampling["samples_per_part"])
            backward = statistics(
                tree, points, p["representation_distance_m"], sampling["outlier_limit"]
            )
            direct = {
                "reference_to_candidate": forward,
                "candidate_to_reference": backward,
                "reference_sample_triangle_indices": indices.tolist(),
                "candidate_sample_triangle_indices": other_indices.tolist(),
                "pass": forward["pass"] and backward["pass"],
            }
        del tree
        passed = (
            measured["pass"]
            and reverse["pass"]
            and all(c["pass"] for c in critical)
            and (direct is None or direct["pass"])
        )
        output.append(
            {
                "part_id": part.part_id,
                "frame_id": part.frame_id,
                "role": part.role,
                "pass": passed,
                "dimensions": measured,
                "reference_reverse": reverse,
                "critical_features": critical,
                "direct_discrepancy": direct,
            }
        )
    return {
        "pass": all(p["pass"] for p in output),
        "parts": output,
        "reference_sha256": value["reference_sha256"],
        "candidate_sha256": value["candidate_sha256"],
        "sampling": "Deterministic area-stratum actual triangle centroids in each direction; separate evenly indexed analytic-reference samples; explicit source-bound local critical spans",
        "metric": "Floating-point point-to-actual-planar-triangle distances, not nearest vertices, common-reference proxy, certified Hausdorff distance or global minimum thickness",
        "mesh_self_intersection": "NOT_CERTIFIED",
        "physical_validation": "NOT_PERFORMED",
    }


if __name__ == "__main__":
    raw = sys.stdin.buffer.read(2 * 1024**2 + 1)
    require(len(raw) <= 2 * 1024**2, "R08_CAPACITY", "Bounded worker request required")
    print(json.dumps(evaluate(json.loads(raw)), allow_nan=False, separators=(",", ":")))
