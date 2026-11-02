"""Independent Gmsh import/evaluation path, separate process; no OCP/PicoGK import.

Gmsh also embeds OCCT. Tool/API/process independence is not kernel implementation
independence; analytic reference checks remain a separate verification leg.
"""
import json
import os
import re
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
        # OCCT's absolute modelling floor is calibrated in native mm. A metre
        # import spuriously perturbs Boolean edge samples at this fixture scale.
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.option.setNumber("Geometry.OCCAutoFix", 0)
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
        gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
        gmsh.option.setNumber("Mesh.StlLinearDeflection", .0005)  # 0.5 micrometre, native mm
        gmsh.model.add("p07-independent-reimport")
        gmsh.model.occ.importShapes(str(path))
        gmsh.model.occ.synchronize()
        bodies = gmsh.model.getEntities(3)
        native_volume = sum(gmsh.model.occ.getMass(3, tag) for _, tag in bodies)
        volume = native_volume * 1e-9
        centroid = [sum(gmsh.model.occ.getMass(3, tag) * gmsh.model.occ.getCenterOfMass(3, tag)[i] for _, tag in bodies) / native_volume * .001 for i in range(3)] if native_volume else [0., 0., 0.]
        bounds = [v * .001 for v in gmsh.model.getBoundingBox(-1, -1)]
        faces = gmsh.model.getEntities(2)
        types = [gmsh.model.getType(2, tag) for _, tag in faces]
        raw_types = types.copy()
        # Gmsh 4.15 OCCFace::geomType checks exact DynamicType and does not
        # unwrap Geom_RectangularTrimmedSurface. Do NOT whitelist Unknown.
        # Prove spherical analytic carriers in the actual STEP face references
        # AND independently constant principal curvatures on each unknown face.
        text = path.read_text()
        entities = dict(re.findall(r"#(\d+)\s*=\s*([\s\S]*?);", text))
        carriers = []
        for entity in entities.values():
            match = re.fullmatch(r"ADVANCED_FACE\('[^']*',\([\s\S]*\),#(\d+),\.[TF]\.\)", entity.strip())
            if match:
                surface = entities.get(match[1], "").strip()
                carriers.append(surface.split("(", 1)[0])
        import numpy as np
        classification = []
        for index, (_, tag) in enumerate(faces):
            if types[index] != "Unknown":
                continue
            lo, hi = gmsh.model.getParametrizationBounds(2, tag)
            uv = [v for u in (.2, .5, .8) for v0 in (.2, .5, .8)
                  for v in (lo[0] + u * (hi[0]-lo[0]), lo[1] + v0 * (hi[1]-lo[1]))]
            kmax, kmin, _, _ = gmsh.model.getPrincipalCurvatures(tag, uv)
            curvatures = np.r_[kmax, kmin].astype(float) * 1000
            valid = (len(carriers) == len(faces) and set(carriers) == {"SPHERICAL_SURFACE"}
                     and np.isfinite(curvatures).all() and np.min(np.abs(curvatures)) > 0
                     and np.ptp(curvatures) <= 1e-7 * np.max(np.abs(curvatures)))
            if valid:
                types[index] = "Sphere"
            classification.append({"face_tag": tag, "raw_type": "Unknown", "resolved_type": types[index],
                                   "step_spherical_carriers_only": bool(len(carriers) == len(faces) and set(carriers) == {"SPHERICAL_SURFACE"}),
                                   "principal_curvatures_per_m": curvatures.tolist()})
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 3)
        gmsh.model.mesh.generate(2)
        _, coordinates, _ = gmsh.model.mesh.getNodes()
        if len(coordinates) > 60000:
            raise ValueError("Independent sampling exceeds bound")
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
                closest, uv = gmsh.model.getClosestPoint(2, tag, (points * 1000).reshape(-1).tolist())
                distance = np.linalg.norm(np.array(closest).reshape(-1, 3) * .001 - points, axis=1)
                # Closest-point API projects to the untrimmed carrier. A point
                # outside this face's trims cannot establish reverse fidelity.
                inside = [gmsh.model.isInside(2, tag, uv[i:i+2], parametric=True) == 1 for i in range(0, len(uv), 2)]
                distance = np.where(inside, distance, np.inf)
                best = np.minimum(best, distance)
            reverse_points = best.tolist()
        result = {"reader": "gmsh", "version": gmsh.__version__, "units": "m", "body_count": len(bodies), "volume_m3": volume,
                  "centroid_m": centroid, "bounds_m": bounds, "face_types": types,
                  "face_count": len(faces), "surface_samples_m": (np.array(coordinates) * .001).tolist(), "reverse_distances_m": reverse_points,
                  "raw_face_types": raw_types, "analytic_carrier_types": carriers, "face_classification": classification,
                  "import_unit": "mm", "bounds_method": "trimmed OCC STL bounds; absolute deflection 0.5um; sampled not certified",
                  "parametric_boundary_edges": len(gmsh.model.getBoundary(faces, combined=True, oriented=True, recursive=False)),
                  "mesh_nonmanifold_edges": int((counts != 2).sum()), "mesh_orientation_errors": int((orientation != 0).sum()),
                  "mesh_triangle_count": len(triangles),
                  "boundary_count": len(gmsh.model.getBoundary(bodies, combined=False, oriented=True, recursive=False))}
        print(json.dumps(result, allow_nan=False), file=output, flush=True)
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
