"""User-approved separately qualified OCCT-only component runtime admission.

Does not satisfy/enable the combined NGG/PicoGK or nozzle runtime profiles.
Existing combined-profile validation and all historical receipts stay intact.
"""
import json
from hashlib import sha256
from pathlib import Path

from infrastructure.geometry import WorkerCommand
from systems.contracts.geometry._wire import require
from systems.geometry.component_authority import methods
from systems.geometry.component_model import POLICY,VERSION

SCHEMA="cosmos.occt-component-runtime.v1"


def configuration(path):
    path=Path(path);root=Path(__file__).resolve().parents[1]
    require(path.is_absolute() and path.is_file() and not path.is_symlink(),"OCCT_PROFILE","Explicit private runtime manifest required")
    cfg=json.loads(path.read_bytes())
    require(set(cfg)=={"schema","qualification","production_enabled","picogk_enabled","occt","engine_components","sha256","python_sha256"} and cfg["schema"]==SCHEMA and cfg["qualification"]=="local-software-fixtures-only" and cfg["production_enabled"] is False and cfg["picogk_enabled"] is False,"OCCT_PROFILE","Only separately qualified local OCCT component research profile; PicoGK/production disabled")
    occt=cfg["occt"];item=cfg["engine_components"]
    require(set(occt)=={"argv","environment"} and type(occt["argv"]) is list and len(occt["argv"])==1,"OCCT_PROFILE","Explicit server-owned interpreter required")
    executable=Path(occt["argv"][0]);require(executable.is_absolute() and executable.is_file() and sha256(executable.read_bytes()).hexdigest()==cfg["python_sha256"],"OCCT_PROFILE","Pinned interpreter digest mismatch")
    require(set(item)=={"policy","version","worker","reader","receipt","receipt_sha256"} and item["policy"]==POLICY and item["version"]==VERSION,"OCCT_PROFILE","Exact component worker policy/version required")
    expected={str(root/p):v for p,v in methods().items()}
    require(cfg["sha256"]==expected,"OCCT_METHOD_CHANGED","Changed component methods require new qualification; historical sources are not resealed")
    for role,file in (("worker","component_worker.py"),("reader","component_step_reader.py")):
        command=item[role];require(set(command)=={"argv","environment"} and command["argv"]==[str(executable),str(root/"plugins/geometry/workers"/file)] and command["environment"]==occt["environment"],"OCCT_PROFILE","Only declared component commands may execute")
        WorkerCommand(tuple(command["argv"]),tuple(command["environment"].items()))
    receipt=Path(item["receipt"]);require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink() and sha256(receipt.read_bytes()).hexdigest()==item["receipt_sha256"],"OCCT_RECEIPT","Exact independent component software receipt required")
    proof=json.loads(receipt.read_bytes())
    require(proof.get("profile")==SCHEMA and proof.get("policy")==POLICY and proof.get("version")==VERSION and proof.get("software_qa_pass") is True and proof.get("physical_validation")=="NOT_PERFORMED" and proof.get("method_sources")==expected,"OCCT_RECEIPT","Passing current component software evidence required; no physical/manufacturing acceptance")
    for label,minimum in (("native-components",40),("component-http",6),("driving-constraints",12)):
        evidence=proof.get("reports",{}).get(label,{})
        require(evidence.get("tests",0)>=minimum and all(evidence.get(k)==0 for k in ("failures","errors","skipped")),"OCCT_RECEIPT","Executed unskipped component/HTTP/constraint tests required")
        report=Path(evidence.get("path",""));require(report.is_absolute() and report.is_file() and sha256(report.read_bytes()).hexdigest()==evidence.get("sha256"),"OCCT_RECEIPT","Qualification report integrity mismatch")
    return {**cfg,"manifest_sha256":sha256(path.read_bytes()).hexdigest()}
