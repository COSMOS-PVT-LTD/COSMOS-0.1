"""Separate Gmsh STEP reimport process. Shared OCCT kernel, independent API/tool path."""

import json
import os
import re
import sys
from pathlib import Path


def main():
    output = os.fdopen(os.dup(1), "w", buffering=1)
    os.dup2(2, 1)
    if len(sys.argv) != 2:
        raise ValueError("Pass exactly one STEP candidate")
    path = Path(sys.argv[1])
    if not path.is_absolute() or path.suffix != ".step" or path.is_symlink() or not 0 < path.stat().st_size <= 64 * 1024 ** 2:
        raise ValueError("Invalid bounded STEP candidate")
    raw = sys.stdin.buffer.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("Reimport sampling payload exceeds bound")
    request = json.loads(raw)
    if set(request) != {"samples_m", "distance_limit_m"} or type(request["distance_limit_m"]) not in (float, int) or not 0 < request["distance_limit_m"] < .1:
        raise ValueError("Explicit bounded sample-distance ceiling required")
    import gmsh  # type: ignore[import-not-found]
    import numpy as np
    points = np.array(request["samples_m"], dtype=float)
    if points.ndim != 2 or points.shape[1] != 3 or not 1 <= len(points) <= 5000 or not np.isfinite(points).all() or np.abs(points).max() > 3:
        raise ValueError("Invalid bounded SI reverse samples")
    gmsh.initialize([], readConfigFiles=False)
    try:
        if gmsh.__version__ != "4.15.0":
            raise ValueError("Pinned Gmsh 4.15.0 required")
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.option.setNumber("Geometry.OCCAutoFix", 0)
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
        gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
        deflection = request["distance_limit_m"] / 10
        gmsh.option.setNumber("Mesh.StlLinearDeflection", deflection * 1000)
        gmsh.model.add("r07-independent-engine-nozzle")
        gmsh.model.occ.importShapes(str(path)); gmsh.model.occ.synchronize()
        bodies, faces = gmsh.model.getEntities(3), gmsh.model.getEntities(2)
        mass = sum(gmsh.model.occ.getMass(3, tag) for _, tag in bodies)
        if mass <= 0 or len(bodies) != 1 or len(faces) > 260:
            raise ValueError("One positive-volume bounded nozzle solid required")
        centroid = [sum(gmsh.model.occ.getMass(3, tag) * gmsh.model.occ.getCenterOfMass(3, tag)[i] for _, tag in bodies) / mass * .001 for i in range(3)]
        bounds = [v * .001 for v in gmsh.model.getBoundingBox(-1, -1)]
        best = np.full(len(points), np.inf)
        for _, tag in faces:
            box = np.array(gmsh.model.getBoundingBox(2, tag)) * .001
            indices = np.flatnonzero(((points >= box[:3] - request["distance_limit_m"]) & (points <= box[3:] + request["distance_limit_m"])).all(axis=1))
            if not len(indices):
                continue
            closest, uv = gmsh.model.getClosestPoint(2, tag, (points[indices] * 1000).reshape(-1).tolist())
            inside = np.array([gmsh.model.isInside(2, tag, uv[i:i + 2], parametric=True) == 1 for i in range(0, len(uv), 2)])
            distance = np.linalg.norm(np.array(closest).reshape(-1, 3) * .001 - points[indices], axis=1)
            best[indices] = np.minimum(best[indices], np.where(inside, distance, np.inf))
        size = max(bounds[3] - bounds[0], bounds[4] - bounds[1]) * 1000 / 32
        gmsh.option.setNumber("Mesh.MeshSizeMin", size / 2)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.model.mesh.generate(2)
        _tags, coordinates, _ = gmsh.model.mesh.getNodes()
        if len(coordinates) > 60000:
            raise ValueError("Independent surface sampling exceeds 20k-node bound")
        kinds, _, nodes = gmsh.model.mesh.getElements(2)
        if list(kinds) != [2]:
            raise ValueError("Reimport topology requires linear triangles")
        triangles = np.array(nodes[0]).reshape(-1, 3)
        directed = np.vstack((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]))
        edges, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
        orientation = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
        text = path.read_text()
        entities = dict(re.findall(r"#(\d+)\s*=\s*([\s\S]*?);", text))
        carriers = []
        for value in entities.values():
            match = re.fullmatch(r"ADVANCED_FACE\('[^']*',\([\s\S]*\),#(\d+),\.[TF]\.\)", value.strip())
            if match:
                carriers.append(entities.get(match[1], "").strip().split("(", 1)[0])
        emit = {"reader": "gmsh", "version": gmsh.__version__, "units": "m", "import_unit": "mm", "body_count": len(bodies), "face_count": len(faces), "face_types": [gmsh.model.getType(2, tag) for _, tag in faces], "analytic_carrier_types": carriers,
                "volume_m3": mass * 1e-9, "centroid_m": centroid, "bounds_m": bounds,
                "surface_samples_m": (np.array(coordinates).reshape(-1, 3) * .001).tolist(), "reverse_distances_m": [float(v) if np.isfinite(v) else None for v in best], "unmatched_reverse_samples": int((~np.isfinite(best)).sum()),
                "mesh_nonmanifold_edges": int((counts != 2).sum()), "mesh_orientation_errors": int((orientation != 0).sum()), "mesh_triangle_count": len(triangles), "mesh_euler_characteristic": len(np.unique(triangles)) - len(edges) + len(triangles),
                "boundary_face_count": len(gmsh.model.getBoundary(bodies, combined=False, oriented=True, recursive=False)), "bbox_deflection_m": deflection,
                "sampling_scope": "Gmsh imported surface nodes to exact meridian distance; retained stations/midpoints and eight azimuths to trimmed imported faces. AABB filtering only within explicit distance ceiling; no certified Hausdorff bound"}
        print(json.dumps(emit, allow_nan=False), file=output, flush=True)
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
