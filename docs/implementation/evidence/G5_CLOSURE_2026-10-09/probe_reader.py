import json
import sys
from pathlib import Path

import gmsh
import numpy as np

from systems.geometry.qa import FixtureReference

base = Path(sys.argv[1])
gmsh.initialize([], readConfigFiles=False)
gmsh.option.setNumber("General.Terminal", 0)
for native_unit in ("M", "MM"):
    scale = 1 if native_unit == "M" else .001
    for operation in ("union", "difference", "intersection"):
        gmsh.clear()
        gmsh.option.setString("Geometry.OCCTargetUnit", native_unit)
        gmsh.option.setNumber("Geometry.OCCAutoFix", 0)
        gmsh.option.setNumber("Geometry.OCCBoundsUseStl", 1)
        gmsh.option.setNumber("Mesh.StlLinearDeflectionRelative", 0)
        gmsh.option.setNumber("Mesh.StlLinearDeflection", 1e-7 / scale)
        gmsh.model.occ.importShapes(str(base / ("occt-step-" + operation) / "export.step"))
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", .001 / scale)
        gmsh.option.setNumber("Mesh.MeshSizeMax", .003 / scale)
        gmsh.model.mesh.generate(2)
        _, xyz, _ = gmsh.model.mesh.getNodes()
        ref = FixtureReference(operation)
        types = []
        curvatures = []
        for _, tag in gmsh.model.getEntities(2):
            types.append(gmsh.model.getType(2, tag))
            lo, hi = gmsh.model.getParametrizationBounds(2, tag)
            uv = [(a+b)/2 for a,b in zip(lo,hi)]
            kmax, kmin, _, _ = gmsh.model.getPrincipalCurvatures(tag, uv)
            curvatures.append([float(kmax[0])/scale, float(kmin[0])/scale])
        bounds = np.array(gmsh.model.getBoundingBox(-1, -1))*scale
        print(json.dumps({"unit": native_unit, "operation": operation, "types": types,
                          "bounds_error": float(np.abs(bounds-ref.bounds_m).max()),
                          "bounds": bounds.tolist(), "forward_max": float(np.abs(ref.sdf(np.array(xyz).reshape(-1,3)*scale)).max()),
                          "curvatures": curvatures}), flush=True)
gmsh.finalize()
