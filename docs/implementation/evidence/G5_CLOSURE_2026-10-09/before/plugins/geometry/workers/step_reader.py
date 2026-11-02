"""Independent Gmsh import/evaluation path, separate process; no OCP/PicoGK import.

Gmsh also embeds OCCT. Tool/API/process independence is not kernel implementation
independence; analytic reference checks remain a separate verification leg.
"""
import json
import os
import sys
from pathlib import Path


def main():
    output = os.fdopen(os.dup(1), "w", buffering=1)
    os.dup2(2, 1)
    if len(sys.argv) != 2:
        raise ValueError("Pass one candidate")
    path = Path(sys.argv[1])
    if not path.is_absolute() or path.suffix != ".step" or path.is_symlink() or not 0 < path.stat().st_size <= 64 * 1024**2:
        raise ValueError("Unsupported bounded STEP candidate")
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise ValueError("Sampling payload too large")
    requested = json.loads(raw) if raw else []
    if not isinstance(requested, list) or len(requested) > 3072 or len(requested) % 3:
        raise ValueError("Invalid reverse sampling payload")
    import gmsh  # type: ignore[import-not-found]
    gmsh.initialize([], readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setString("Geometry.OCCTargetUnit", "M")
        gmsh.model.add("p07-independent-reimport")
        gmsh.model.occ.importShapes(str(path))
        gmsh.model.occ.synchronize()
        bodies = gmsh.model.getEntities(3)
        volume = sum(gmsh.model.occ.getMass(3, tag) for _, tag in bodies)
        centroid = [sum(gmsh.model.occ.getMass(3, tag) * gmsh.model.occ.getCenterOfMass(3, tag)[i] for _, tag in bodies) / volume for i in range(3)] if volume else [0., 0., 0.]
        bounds = gmsh.model.getBoundingBox(-1, -1)
        faces = gmsh.model.getEntities(2)
        types = [gmsh.model.getType(2, tag) for _, tag in faces]
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", .001)
        gmsh.option.setNumber("Mesh.MeshSizeMax", .003)
        gmsh.model.mesh.generate(2)
        _, coordinates, _ = gmsh.model.mesh.getNodes()
        if len(coordinates) > 60000:
            raise ValueError("Independent sampling exceeds bound")
        import numpy as np
        element_types, _, element_nodes = gmsh.model.mesh.getElements(2)
        if list(element_types) != [2]:
            raise ValueError("Independent topology sampler requires linear triangles")
        triangles = np.asarray(element_nodes[0]).reshape(-1, 3)
        directed = np.vstack((triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]))
        _, inverse, counts = np.unique(np.sort(directed, axis=1), axis=0, return_inverse=True, return_counts=True)
        orientation = np.bincount(inverse, weights=np.where(directed[:, 0] < directed[:, 1], 1, -1))
        reverse_points = []
        if requested:
            points = np.array(requested, dtype=float).reshape(-1, 3)
            if not np.isfinite(points).all() or np.abs(points).max() > .3:
                raise ValueError("Invalid reverse samples")
            best = np.full(len(points), np.inf)
            for _, tag in faces:
                closest, _ = gmsh.model.getClosestPoint(2, tag, requested)
                distance = np.linalg.norm(np.array(closest).reshape(-1, 3) - points, axis=1)
                best = np.minimum(best, distance)
            reverse_points = best.tolist()
        result = {"reader": "gmsh", "version": gmsh.__version__, "units": "m", "body_count": len(bodies), "volume_m3": volume,
                  "centroid_m": centroid, "bounds_m": bounds, "face_types": types,
                  "face_count": len(faces), "surface_samples_m": list(coordinates), "reverse_distances_m": reverse_points,
                  "parametric_boundary_edges": len(gmsh.model.getBoundary(faces, combined=True, oriented=True, recursive=False)),
                  "mesh_nonmanifold_edges": int((counts != 2).sum()), "mesh_orientation_errors": int((orientation != 0).sum()),
                  "mesh_triangle_count": len(triangles),
                  "boundary_count": len(gmsh.model.getBoundary(bodies, combined=False, oriented=True, recursive=False))}
        print(json.dumps(result, allow_nan=False), file=output, flush=True)
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
