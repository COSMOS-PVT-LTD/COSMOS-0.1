"""Append-only qualification of the approved OCCT-only component profile."""
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from api.occt_component_runtime import SCHEMA,configuration
from systems.geometry.component_authority import methods
from systems.geometry.component_model import POLICY,VERSION


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python",type=Path,required=True);parser.add_argument("--output",type=Path,required=True)
    for key in ("native-components","component-http","driving-constraints"):parser.add_argument("--"+key,type=Path,required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];interpreter=args.python.absolute();reports={}
    for label,minimum in (("native-components",40),("component-http",6),("driving-constraints",12)):
        path=getattr(args,label.replace("-","_")).resolve();tree=ET.parse(path).getroot()
        counts={key:sum(int(s.get(key,0)) for s in tree.iter("testsuite")) for key in ("tests","failures","errors","skipped")}
        if counts["tests"]<minimum or any(counts[k] for k in ("failures","errors","skipped")):raise ValueError("Actual unskipped passing qualification required: "+label)
        reports[label]={"path":str(path),"sha256":sha256(path.read_bytes()).hexdigest(),**counts}
    packages=json.loads(subprocess.check_output([str(interpreter),"-c","import importlib.metadata as m,json;print(json.dumps({k:m.version(k) for k in ('cadquery-ocp','gmsh')}))"],timeout=15))
    if packages!={"cadquery-ocp":"7.8.1.1","gmsh":"4.15.0"}:raise ValueError("Pinned independently imported OCCT/Gmsh package versions required")
    target=args.output.resolve();target.mkdir(parents=True,exist_ok=False)
    hashes={str(root/name):value for name,value in methods().items()}
    receipt={"profile":SCHEMA,"policy":POLICY,"version":VERSION,"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED","method_sources":hashes,"reports":reports,"packages":packages,"scope":"User-approved OCCT-only component research runtime. PicoGK and production disabled. Existing combined-runtime receipts and live owner data unchanged."}
    receipt_path=target/"software-receipt.json"
    with receipt_path.open("x") as f:json.dump(receipt,f,indent=2)
    environment={"PYTHONPATH":str(root),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}
    command=lambda file:{"argv":[str(interpreter),str(root/"plugins/geometry/workers"/file)],"environment":environment}
    item={"policy":POLICY,"version":VERSION,"worker":command("component_worker.py"),"reader":command("component_step_reader.py"),"receipt":str(receipt_path),"receipt_sha256":sha256(receipt_path.read_bytes()).hexdigest()}
    cfg={"schema":SCHEMA,"qualification":"local-software-fixtures-only","production_enabled":False,"picogk_enabled":False,"occt":{"argv":[str(interpreter)],"environment":environment},"engine_components":item,"sha256":hashes,"python_sha256":sha256(interpreter.read_bytes()).hexdigest()}
    path=target/"runtime.json"
    with path.open("x") as f:json.dump(cfg,f,indent=2)
    configuration(path);print("Qualified OCCT-only component software profile:",path,"; owner runtime not switched.")


if __name__=="__main__":main()
