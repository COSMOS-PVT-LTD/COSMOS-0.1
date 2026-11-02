"""Create new append-only bounded CAD inspection runtime evidence from real tests.

Does not activate a runtime, migrate a root or alter earlier qualification.
"""
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from systems.geometry.cad_tools import SCHEMA,methods,configuration


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--python",type=Path,required=True);p.add_argument("--junit",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    interpreter=a.python.absolute();report=a.junit.resolve();target=a.output.resolve()
    root=ET.parse(report).getroot();counts={k:sum(int(s.get(k,0)) for s in root.iter("testsuite")) for k in ("tests","failures","errors","skipped")}
    if counts["tests"]<10 or any(counts[k] for k in ("failures","errors","skipped")):raise ValueError("At least10 real passing, unskipped native CAD tests required")
    versions=json.loads(subprocess.check_output([str(interpreter),"-c","import importlib.metadata as m,json;print(json.dumps({k:m.version(k) for k in ('cadquery-ocp','reportlab','vtk')}))"],timeout=15))
    if versions!={"cadquery-ocp":"7.8.1.1","reportlab":"4.4.4","vtk":"9.3.1"}:raise ValueError("Explicit pinned CAD/drawing dependency versions required")
    target.mkdir(parents=True,exist_ok=False)
    receipt={"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED","method_sha256":methods(),"report_sha256":sha256(report.read_bytes()).hexdigest(),"report_path":str(report),"packages":versions,**counts,"scope":"Bounded native BREP pair and HLR/PDF software fixtures, not arbitrary CAD/full-engine manufacturing or physical acceptance. Runtime admission approval and project source currentness remain separate."}
    rp=target/"software-receipt.json"
    with rp.open("x") as f:json.dump(receipt,f,indent=2)
    cfg={"schema":SCHEMA,"python":str(interpreter),"python_sha256":sha256(interpreter.read_bytes()).hexdigest(),"method_sha256":methods(),"receipt":str(rp),"receipt_sha256":sha256(rp.read_bytes()).hexdigest()}
    path=target/"runtime.json"
    with path.open("x") as f:json.dump(cfg,f,indent=2)
    configuration(path)
    native={"occt":{"argv":[str(interpreter)],"environment":{"PYTHONPATH":str(Path(__file__).resolve().parents[1]),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}}}
    with (target/"native-test-commands.json").open("x") as f:json.dump(native,f,indent=2)
    print("Prepared separately pinned inspection evidence:",path,"; no live runtime activated.")


if __name__=="__main__":main()
