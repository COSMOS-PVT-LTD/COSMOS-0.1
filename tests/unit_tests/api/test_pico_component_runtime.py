"""Component admission is separate, current-byte bound and fails closed."""
from hashlib import sha256
import json

import pytest

from api import pico_component_runtime as runtime
from plugins.geometry.pico_components import POLICY,VERSION


def qualified(tmp_path,monkeypatch):
    monkeypatch.setattr(runtime,"ROOT",tmp_path)
    private=tmp_path/".runtime-picogk"/"test";private.mkdir(parents=True)
    exe=private/"dotnet";exe.write_bytes(b"test command, not executed")
    exe.chmod(0o700)
    dll=private/"PicoComponents.dll";dll.write_bytes(b"test worker, not executed")
    source=tmp_path/"method.py";source.write_bytes(b"test source")
    preview=tmp_path/".venv-cad-inspection/bin/python";preview.parent.mkdir(parents=True);preview.write_bytes(b"test command");preview.chmod(0o700)
    venv=preview.parent.parent/"pyvenv.cfg";venv.write_bytes(b"test venv")
    script=tmp_path/"plugins/geometry/workers/pico_preview_worker.py";script.parent.mkdir(parents=True);script.write_bytes(b"test script")
    digest=lambda f:sha256(f.read_bytes()).hexdigest()
    monkeypatch.setattr(runtime,"methods",lambda:{"method.py":digest(source)})
    hashes={str(f):digest(f) for f in (exe,dll,source,preview,venv,script)}
    reports={}
    for name,count in (("unit",10),("native",10),("http",3),("preview",5)):
        path=tmp_path/(name+".xml");path.write_text("test report fixture")
        reports[name]={"path":str(path),"sha256":digest(path),"tests":count,"failures":0,"errors":0,"skipped":0}
    proof={"schema":runtime.SCHEMA,"method_sources":{str(source):digest(source)},"runtime_hashes":hashes,"software_qa_pass":True,"physical_validation":"NOT_PERFORMED","reports":reports}
    receipt=tmp_path/"receipt.json";receipt.write_text(json.dumps(proof))
    cfg={"schema":runtime.SCHEMA,"qualification":"local-software-research-only","production_enabled":False,"policy":POLICY,"version":VERSION,
         "worker":{"argv":[str(exe),str(dll)],"environment":{}},"preview_worker":{"argv":[str(preview),str(script)],"environment":{"PYTHONPATH":str(tmp_path),"OMP_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1"}},"sha256":hashes,"receipt":str(receipt),"receipt_sha256":digest(receipt)}
    path=tmp_path/"runtime.json";path.write_text(json.dumps(cfg))
    return path,cfg,proof,receipt,dll


def test_separate_current_byte_bound_profile(tmp_path,monkeypatch):
    path,*_=qualified(tmp_path,monkeypatch)
    assert runtime.configuration(path)["production_enabled"] is False


@pytest.mark.parametrize("change",["worker","source","report","receipt","production","skip","method-omission","preview-fixtures-only"])
def test_admission_rejects_stale_or_weakened_qualification(tmp_path,monkeypatch,change):
    path,cfg,proof,receipt,dll=qualified(tmp_path,monkeypatch)
    if change=="worker":dll.write_bytes(b"changed")
    elif change=="source":(tmp_path/"method.py").write_bytes(b"changed")
    elif change=="report":(tmp_path/"native.xml").write_bytes(b"changed")
    elif change=="receipt":receipt.write_bytes(b"changed")
    elif change=="production":cfg["production_enabled"]=True
    else:
        if change=="skip":proof["reports"]["native"]["skipped"]=1
        elif change=="preview-fixtures-only":proof["reports"]["preview"]["tests"]=4
        else:proof["method_sources"]={}
        receipt.write_text(json.dumps(proof));cfg["receipt_sha256"]=sha256(receipt.read_bytes()).hexdigest()
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError):runtime.configuration(path)


def test_preview_lod_keeps_full_part_source_ranges_and_immutable_original():
    import numpy as np
    from api.pico_components import preview
    from systems.geometry.qa import STL_RECORD
    records=np.zeros(210_000,dtype=STL_RECORD)
    records["vertices"][:100_000]=1;records["vertices"][100_000:]=2
    raw=b"UNITS= m".ljust(80,b" ")+len(records).to_bytes(4,"little")+records.tobytes();before=sha256(raw).hexdigest()
    parts=[{"part_id":"a","triangle_start":0,"triangle_count":100_000},{"part_id":"b","triangle_start":100_000,"triangle_count":110_000}]
    with pytest.raises(ValueError,match="topology-preserving"):preview(raw,parts)
    assert sha256(raw).hexdigest()==before
