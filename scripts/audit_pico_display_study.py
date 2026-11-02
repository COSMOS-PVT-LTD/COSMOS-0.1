"""Independently inspect a display study against its exact captured source/QA."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from systems.contracts.geometry import DesignSnapshot,GeometryFeatureGraph
from systems.geometry.component_model import from_contracts
from systems.geometry.component_reference import PartReference
from systems.geometry.pico_component_builds import PicoLimits
from systems.geometry.pico_mesh_qa import audit_part
from systems.geometry.qa import STL_RECORD


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("inputs","metadata","positions"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();source=json.loads(a.inputs.read_bytes());m=json.loads(source["model_canonical_json"])
    plan=from_contracts(DesignSnapshot.from_json(m["snapshot_json"]),GeometryFeatureGraph.from_json(m["graph_json"]))
    meta=json.loads(a.metadata.read_bytes());data=a.positions.read_bytes()
    if sha256(data).hexdigest()!=meta["sha256"] or len(data)>7200000:raise ValueError("Display checksum/capacity mismatch")
    tri=np.frombuffer(data,dtype="<f4").reshape(-1,3,3);records=np.zeros(len(tri),dtype=STL_RECORD);records["vertices"]=tri
    normals=np.cross(tri[:,1].astype(float)-tri[:,0],tri[:,2].astype(float)-tri[:,0]);records["normal"]=normals/np.linalg.norm(normals,axis=1)[:,None]
    checks=[audit_part(records[p["triangle_start"]:p["triangle_start"]+p["triangle_count"]],PartReference(plan,q),PicoLimits.from_spec(source["qa_specification"]),lambda:None) for p,q in zip(meta["parts"],plan.parts,strict=True)]
    print(json.dumps({"source_inputs_sha256":sha256(a.inputs.read_bytes()).hexdigest(),"metadata_sha256":sha256(a.metadata.read_bytes()).hexdigest(),"preview_sha256":meta["sha256"],
        "parts":len(checks),"triangles":len(tri),"all_pass":all(c["pass"] for c in checks),"failed":[c for c in checks if not c["pass"]],"max_volume_error":max(c["relative_volume_error"] for c in checks),"max_reverse_m":max(c["reverse_max_m"] or 0 for c in checks),"checks":checks}))


if __name__=="__main__":main()
