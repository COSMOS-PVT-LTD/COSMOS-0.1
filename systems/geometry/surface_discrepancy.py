"""Direct encoded surface queries, independent of the generating geometry kernel.

Floating-point planar triangles with conservative AABB pruning. Sampled results
are not certified Hausdorff distance, global wall minima or self-intersection.
"""

from __future__ import annotations

import heapq

import numpy as np

from systems.contracts.geometry._wire import require


def closest_triangle(point, triangles):
    a, b, c = (triangles[:, i].astype(float) for i in range(3))
    ab, ac, ap = b - a, c - a, point - a
    normal = np.cross(ab, ac)
    n2 = np.einsum("ij,ij->i", normal, normal)
    require(
        bool((n2 > 0).all()),
        "R08_DEGENERATE",
        "Degenerate encoded triangles cannot be qualified",
    )
    projection = point - (np.einsum("ij,ij->i", ap, normal) / n2)[:, None] * normal
    d00 = np.einsum("ij,ij->i", ab, ab)
    d01 = np.einsum("ij,ij->i", ab, ac)
    d11 = np.einsum("ij,ij->i", ac, ac)
    d20 = np.einsum("ij,ij->i", projection - a, ab)
    d21 = np.einsum("ij,ij->i", projection - a, ac)
    denominator = d00 * d11 - d01 * d01
    with np.errstate(divide="ignore", invalid="ignore"):
        v = (d11 * d20 - d01 * d21) / denominator
        w = (d00 * d21 - d01 * d20) / denominator
    valid = (
        (denominator > 0)
        & np.isfinite(v)
        & np.isfinite(w)
        & (v >= 0)
        & (w >= 0)
        & (v + w <= 1)
    )
    best = projection.copy()
    distance = np.where(
        valid, np.einsum("ij,ij->i", projection - point, projection - point), np.inf
    )
    for first, second in ((a, b), (b, c), (c, a)):
        edge = second - first
        e2 = np.einsum("ij,ij->i", edge, edge)
        alpha = np.clip(np.einsum("ij,ij->i", point - first, edge) / e2, 0, 1)
        candidate = first + alpha[:, None] * edge
        d2 = np.einsum("ij,ij->i", candidate - point, candidate - point)
        choose = d2 < distance
        best[choose] = candidate[choose]
        distance = np.minimum(distance, d2)
    index = int(np.argmin(distance))
    require(
        np.isfinite(distance[index]),
        "R08_DISTANCE",
        "No finite encoded-surface witness",
    )
    return float(np.sqrt(distance[index])), best[index], index


class TriangleTree:
    def __init__(self, triangles, check=lambda: None):
        self.triangles = np.asarray(triangles)
        require(
            self.triangles.ndim == 3
            and self.triangles.shape[1:] == (3, 3)
            and 0 < len(self.triangles) <= 4_000_000
            and bool(np.isfinite(self.triangles).all()),
            "R08_MESH",
            "Finite bounded actual triangles required",
        )
        self.nodes = []
        self.check = check
        self.pad = (
            64 * np.finfo(float).eps * max(1.0, float(np.abs(self.triangles).max()))
        )
        centers = self.triangles.mean(axis=1)

        def build(ids):
            check()
            low = self.triangles[ids].min(axis=(0, 1))
            high = self.triangles[ids].max(axis=(0, 1))
            i = len(self.nodes)
            self.nodes.append(None)
            if len(ids) <= 64:
                self.nodes[i] = (low, high, ids, None)
            else:
                axis = int(np.argmax(high - low))
                order = np.argpartition(centers[ids, axis], len(ids) // 2)
                middle = len(ids) // 2
                children = (build(ids[order[:middle]]), build(ids[order[middle:]]))
                self.nodes[i] = (low, high, None, children)
            return i

        build(np.arange(len(triangles), dtype=np.int32))

    def nearest(self, point):
        point = np.asarray(point, dtype=float)
        require(
            point.shape == (3,) and bool(np.isfinite(point).all()),
            "R08_POINT",
            "Finite world point required",
        )
        queue = [(0.0, 0)]
        best = np.inf
        witness = None
        triangle = None
        visits = 0
        while queue:
            lower, i = heapq.heappop(queue)
            if lower > best + self.pad:
                continue
            _low, _high, ids, children = self.nodes[i]
            visits += 1
            if visits % 128 == 0:
                self.check()
            if ids is not None:
                distance, actual, j = closest_triangle(point, self.triangles[ids])
                if distance < best:
                    best, witness, triangle = distance, actual, int(ids[j])
            else:
                for child in children:
                    lo, hi, _, _ = self.nodes[child]
                    d = float(
                        np.linalg.norm(
                            np.maximum(np.maximum(lo - point, point - hi), 0)
                        )
                    )
                    if d <= best + self.pad:
                        heapq.heappush(queue, (d, child))
        require(witness is not None, "R08_DISTANCE", "No actual triangle witness")
        return best, witness, triangle


def sample_surface(triangles, count):
    """Deterministic equal-area-stratum triangle centroids; no random state."""
    t = np.asarray(triangles)
    area = (
        np.linalg.norm(
            np.cross(t[:, 1].astype(float) - t[:, 0], t[:, 2].astype(float) - t[:, 0]),
            axis=1,
        )
        / 2
    )
    require(
        bool((area > 0).all()), "R08_DEGENERATE", "Zero-area encoded surface rejected"
    )
    cumulative = np.cumsum(area)
    indices = np.searchsorted(
        cumulative, (np.arange(count) + 0.5) * cumulative[-1] / count
    )
    return t[indices].mean(axis=1).astype(float), indices


def statistics(tree, points, ceiling, outlier_limit):
    values = []
    outliers = []
    for i, point in enumerate(points):
        tree.check()
        d, q, face = tree.nearest(point)
        values.append(d)
        if d > ceiling and len(outliers) < outlier_limit:
            outliers.append(
                {
                    "sample_index": i,
                    "point_m": point.tolist(),
                    "closest_m": q.tolist(),
                    "triangle_index": face,
                    "distance_m": d,
                }
            )
    require(bool(values), "R08_SAMPLING", "Nonempty declared samples required")
    return {
        "pass": max(values) <= ceiling,
        "maximum_m": max(values),
        "p95_m": float(np.percentile(values, 95)),
        "p99_m": float(np.percentile(values, 99)),
        "samples": len(values),
        "outlier_count": sum(d > ceiling for d in values),
        "outliers": outliers,
        "limit_m": ceiling,
    }
