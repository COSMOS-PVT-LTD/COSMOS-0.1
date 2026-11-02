"""Opt-in, separately qualified local PicoGK components; no old G5 substitution."""
from hashlib import sha256
import json
from pathlib import Path

from infrastructure.geometry import WorkerCommand
from systems.contracts.geometry._wire import require
from systems.geometry.pico_component_builds import methods,PicoWorkspace
from plugins.geometry.pico_components import VERSION,POLICY

SCHEMA="cosmos.picogk-component-runtime.v1"
ROOT=Path(__file__).resolve().parents[1]


def configuration(path):
    path=Path(path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink() and path.stat().st_size<1024*1024,"PICO_RUNTIME","Explicit private bounded qualification manifest required")
    cfg=json.loads(path.read_bytes())
    require(set(cfg)=={"schema","qualification","production_enabled","policy","version","worker","preview_worker","sha256","receipt","receipt_sha256"}
        and cfg["schema"]==SCHEMA and cfg["qualification"]=="local-software-research-only" and cfg["production_enabled"] is False
        and cfg["policy"]==POLICY and cfg["version"]==VERSION,"PICO_RUNTIME","Exact separately qualified research component policy required")
    command=cfg["worker"]
    require(set(command)=={"argv","environment"} and type(command["argv"]) is list and len(command["argv"])==2,"PICO_RUNTIME","Only pinned server-owned .NET/component worker command supported")
    exe,dll=map(Path,command["argv"])
    require(exe.name=="dotnet" and dll.name=="PicoComponents.dll" and all(p.is_absolute() and ROOT/".runtime-picogk" in p.parents for p in (exe,dll)),"PICO_RUNTIME","Persistent private component runtime required; no temporary or caller worker paths")
    WorkerCommand(tuple(command["argv"]),tuple(command["environment"].items()))
    hashes=cfg["sha256"];expected={str(ROOT/n):v for n,v in methods().items()}
    preview=cfg["preview_worker"];python=ROOT/".venv-cad-inspection/bin/python";script=ROOT/"plugins/geometry/workers/pico_preview_worker.py"
    require(set(preview)=={"argv","environment"} and preview["argv"]==[str(python),str(script)] and preview["environment"]=={"PYTHONPATH":str(ROOT),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}
        and str(python.resolve()) in hashes and str(ROOT/".venv-cad-inspection/pyvenv.cfg") in hashes,"PICO_PREVIEW_RUNTIME","Pinned server-owned display reduction interpreter/worker required")
    WorkerCommand(tuple(preview["argv"]),tuple(preview["environment"].items()))
    require(type(hashes) is dict and expected.items()<=hashes.items() and all(str(p) in hashes for p in (exe,dll)),"PICO_METHOD_CHANGED","Current source methods and native command must be pinned")
    for name,digest in hashes.items():
        file=Path(name)
        require(file.is_absolute() and file.is_file() and not file.is_symlink() and sha256(file.read_bytes()).hexdigest()==digest,"PICO_RUNTIME_CHANGED","PicoGK method/runtime bytes changed; qualify new sources without rewriting old receipts")
    receipt=Path(cfg["receipt"])
    require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink() and sha256(receipt.read_bytes()).hexdigest()==cfg["receipt_sha256"],"PICO_QUALIFICATION","Exact separate PicoGK component qualification receipt required")
    proof=json.loads(receipt.read_bytes())
    require(proof.get("schema")==SCHEMA and proof.get("method_sources")==expected and proof.get("runtime_hashes")==hashes and proof.get("software_qa_pass") is True
        and proof.get("physical_validation")=="NOT_PERFORMED","PICO_QUALIFICATION","Passing current source-bound software qualification required")
    for key,minimum in (("unit",10),("native",10),("http",3),("preview",5)):
        r=proof.get("reports",{}).get(key,{})
        require(r.get("tests",0)>=minimum and all(r.get(k)==0 for k in ("skipped","errors","failures")),"PICO_QUALIFICATION","Sufficient executed unskipped unit/native/HTTP evidence required")
        f=Path(r.get("path",""));require(f.is_absolute() and f.is_file() and sha256(f.read_bytes()).hexdigest()==r.get("sha256"),"PICO_QUALIFICATION","Qualification report hash mismatch")
    return {**cfg,"manifest_sha256":sha256(path.read_bytes()).hexdigest()}


def create_workspace(root,path,*,enabled):
    if not enabled or path is None:
        from systems.projects.authority import StoreUnavailable
        raise StoreUnavailable("PicoGK component generation requires explicit separately qualified local runtime; OCCT remains independent")
    configuration(path)
    return PicoWorkspace(Path(root)/"picogk_component_candidates",lambda:configuration(path))
