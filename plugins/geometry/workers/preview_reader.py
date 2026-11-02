"""Display-only STEP triangulation; not an export or an independent QA decision."""
import json
import sys
from pathlib import Path


def main():
    path = Path(sys.argv[1])
    if not path.is_absolute() or path.suffix != ".step" or path.is_symlink() or not 0 < path.stat().st_size <= 64 * 1024**2:
        raise ValueError("Invalid preview source")
    import gmsh  # type: ignore[import-not-found]
    import numpy as np
    gmsh.initialize([], readConfigFiles=False)
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setString("Geometry.OCCTargetUnit", "MM")
        gmsh.option.setNumber("Geometry.OCCAutoFix", 0)
        gmsh.model.occ.importShapes(str(path)); gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 2)
        gmsh.model.mesh.generate(2)
        tags, points, _ = gmsh.model.mesh.getNodes()
        kinds, _, nodes = gmsh.model.mesh.getElements(2)
        if list(kinds) != [2] or len(nodes[0]) > 75_000:
            raise ValueError("Display triangulation exceeds 25k triangle bound")
        index = {tag: i for i, tag in enumerate(tags)}
        points = np.asarray(points).reshape(-1, 3) * .001
        vertices = points[[index[tag] for tag in nodes[0]]]
        if not np.isfinite(vertices).all():
            raise ValueError("Nonfinite preview")
        print(json.dumps({"profile": "gmsh-display-only-1-2mm", "positions_m": vertices.reshape(-1).tolist()}, allow_nan=False))
    finally:
        gmsh.finalize()


if __name__ == "__main__":
    main()
