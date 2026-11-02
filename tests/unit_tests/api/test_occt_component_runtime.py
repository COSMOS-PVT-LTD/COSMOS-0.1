"""Separate research runtime admission, without a native dependency or fake G5 pass."""
import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from api import occt_component_runtime as runtime


def profile(tmp_path,monkeypatch):
    monkeypatch.setattr(runtime,"methods",dict)
    executable=tmp_path/"python";executable.write_bytes(b"inert test-only interpreter identity");executable.chmod(0o700)
    reports={}
    for label,tests in (("native-components",48),("component-http",7),("driving-constraints",14)):
        report=tmp_path/(label+".xml");report.write_text("<testsuite />")
        reports[label]={"path":str(report),"sha256":sha256(report.read_bytes()).hexdigest(),"tests":tests,"failures":0,"errors":0,"skipped":0}
    receipt=tmp_path/"receipt.json"
    proof={"profile":runtime.SCHEMA,"policy":runtime.POLICY,"version":runtime.VERSION,"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","method_sources":{},"reports":reports}
    receipt.write_text(json.dumps(proof))
    root=Path(runtime.__file__).resolve().parents[1]
    item={"policy":runtime.POLICY,"version":runtime.VERSION,"receipt":str(receipt),"receipt_sha256":sha256(receipt.read_bytes()).hexdigest()}
    for role,file in (("worker","component_worker.py"),("reader","component_step_reader.py")):
        item[role]={"argv":[str(executable),str(root/"plugins/geometry/workers"/file)],"environment":{}}
    cfg={"schema":runtime.SCHEMA,"qualification":"local-software-fixtures-only","production_enabled":False,"picogk_enabled":False,"occt":{"argv":[str(executable)],"environment":{}},"engine_components":item,"sha256":{},"python_sha256":sha256(executable.read_bytes()).hexdigest()}
    return cfg,proof,receipt


def admit(tmp_path,cfg):
    path=tmp_path/"runtime.json";path.write_text(json.dumps(cfg))
    return runtime.configuration(path)


def test_occt_only_profile_does_not_claim_production_or_picogk(tmp_path,monkeypatch):
    cfg,_,_=profile(tmp_path,monkeypatch)
    accepted=admit(tmp_path,cfg)
    assert accepted["schema"]==runtime.SCHEMA
    assert accepted["picogk_enabled"] is accepted["production_enabled"] is False


@pytest.mark.parametrize("mutation",["picogk","production","methods","interpreter","receipt","worker","report"])
def test_occt_profile_rejects_unqualified_changes(tmp_path,monkeypatch,mutation):
    cfg,_,receipt=profile(tmp_path,monkeypatch)
    if mutation=="picogk":cfg["picogk_enabled"]=True
    elif mutation=="production":cfg["production_enabled"]=True
    elif mutation=="methods":cfg["sha256"]={"unknown":"0"*64}
    elif mutation=="interpreter":cfg["python_sha256"]="0"*64
    elif mutation=="receipt":receipt.write_text("{}")
    elif mutation=="worker":cfg["engine_components"]["worker"]["argv"][1]="/tmp/unrecognized-worker.py"
    else:(tmp_path/"native-components.xml").write_text("changed")
    with pytest.raises(ValueError):admit(tmp_path,cfg)


@pytest.mark.parametrize("failure",["skipped","errors","failures","too_few","physical_claim"])
def test_occt_profile_requires_sufficient_unskipped_evidence(tmp_path,monkeypatch,failure):
    cfg,proof,receipt=profile(tmp_path,monkeypatch);proof=deepcopy(proof)
    if failure=="physical_claim":proof["physical_validation"]="PASSED"
    elif failure=="too_few":proof["reports"]["native-components"]["tests"]=1
    else:proof["reports"]["driving-constraints"][failure]=1
    receipt.write_text(json.dumps(proof));cfg["engine_components"]["receipt_sha256"]=sha256(receipt.read_bytes()).hexdigest()
    with pytest.raises(ValueError):admit(tmp_path,cfg)
