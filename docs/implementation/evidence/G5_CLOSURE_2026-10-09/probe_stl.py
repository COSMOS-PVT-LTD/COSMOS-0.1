import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere
from OCP.StlAPI import StlAPI_Writer

from systems.geometry.qa import STL_RECORD, FixtureReference, audit_mesh

directory = Path(sys.argv[1])
shape = BRepPrimAPI_MakeSphere(10).Shape()
mesh = BRepMesh_IncrementalMesh(shape, .0006, False, .05, False)
writer = StlAPI_Writer(); writer.ASCIIMode = False
writer.Write(shape, str(directory / "native-mm.stl"))
raw = (directory / "native-mm.stl").read_bytes()
records = np.frombuffer(raw, STL_RECORD, offset=84).copy()
records["vertices"] = records["vertices"].astype(np.float64) * .001
vertices = records["vertices"].astype(np.float64)
cross = np.cross(vertices[:,1]-vertices[:,0], vertices[:,2]-vertices[:,0])
keep = np.any(cross != 0, axis=1)
records = records[keep]; cross = cross[keep]
records["normal"] = cross / np.linalg.norm(cross,axis=1)[:,None]
output = b"COSMOS G5 UNITS= m native-mm tessellation".ljust(80,b" ")+len(records).to_bytes(4,"little")+records.tobytes()
(directory / "sphere-mm-m.stl").write_bytes(output)
print(json.dumps({"raw_count":len(keep), "removed_exact_zero": int((~keep).sum()),"sha":hashlib.sha256(output).hexdigest()}))
print(json.dumps(audit_mesh(directory / "sphere-mm-m.stl",FixtureReference("sphere"),voxel_m=None,export_tolerance_m=1e-6)))
