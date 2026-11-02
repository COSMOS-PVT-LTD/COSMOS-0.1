"""Authorized retained-native inspection and draft drawing orchestration.

Uses the existing process supervisor; no native import into the application.
Configured by a separate, hash-pinned software-test receipt. Does not mutate
geometry, create an engineering approval or install a runtime from a request.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from systems.contracts.geometry._wire import require
from systems.geometry.component_model import from_contracts
from systems.projects.authority import InvalidRecord

ROOT=Path(__file__).resolve().parents[2]
SCHEMA="cosmos.cad-tools-runtime.v1"


def methods():
    names=("systems/geometry/cad_tools.py","systems/geometry/manufacturing_drawing.py","plugins/geometry/workers/cad_inspection_worker.py","api/cad_tools.py")
    return {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def number(raw, low, high, label):
    require(type(raw) in (str,int,float) and not isinstance(raw,bool),"CAD_NUMBER",label+" must be explicit and finite")
    try:value=float(raw)
    except (ValueError,TypeError) as error:raise InvalidRecord(label+" must be finite") from error
    require(math.isfinite(value) and low<=value<=high,"CAD_NUMBER",label+" outside supported bounds")
    return value


def configuration(path):
    require(path is not None,"CAD_RUNTIME_DISABLED","Explicit separately qualified CAD inspection runtime required")
    path=Path(path)
    require(path.is_absolute() and path.is_file() and not path.is_symlink(),"CAD_RUNTIME","Private absolute runtime manifest required")
    cfg=json.loads(path.read_bytes())
    require(type(cfg) is dict and set(cfg)=={"schema","python","python_sha256","method_sha256","receipt","receipt_sha256"} and cfg["schema"]==SCHEMA,"CAD_RUNTIME","Exact CAD tools manifest required")
    interpreter=Path(cfg["python"]);receipt=Path(cfg["receipt"])
    require(interpreter.is_absolute() and interpreter.is_file() and sha256(interpreter.read_bytes()).hexdigest()==cfg["python_sha256"],"CAD_RUNTIME","Pinned native interpreter required")
    require(cfg["method_sha256"]==methods(),"CAD_METHOD_CHANGED","CAD tools changed; qualify a new manifest, never reseal historical receipts")
    require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink() and sha256(receipt.read_bytes()).hexdigest()==cfg["receipt_sha256"],"CAD_RECEIPT","Exact separate CAD software receipt required")
    proof=json.loads(receipt.read_bytes())
    require(proof.get("software_qa_pass") is True and proof.get("method_sha256")==methods() and proof.get("physical_validation")=="NOT_PERFORMED" and proof.get("failures")==0 and proof.get("skipped")==0 and proof.get("tests",0)>=10,"CAD_RECEIPT","Executed passing CAD software tests required; not manufacturing/physical acceptance")
    return cfg


class CadTools:
    def __init__(self,components,path=None):
        self.components=components;self.path=path or os.environ.get("COSMOS_CAD_TOOLS_CONFIG");self.lock=threading.Lock();self.supervisor=None

    def capabilities(self):
        try:configuration(self.path);enabled=True;diagnostic="Separately pinned local CAD inspection software runtime"
        except (ValueError,OSError,KeyError,TypeError) as error:enabled=False;diagnostic=str(error)
        return {"ok":True,"enabled":enabled,"diagnostic":diagnostic,"driving_constraints":True,"maximum_parts":24,"pairwise_only":True,"manufacturing_acceptance":"NOT_PERFORMED","scope":"B-rep pair clearance/interference and unreleased PDF/SVG orthographic drawings; not a general sketch solver, certified tolerances or hardware approval"}

    def close(self):
        with self.lock:
            if self.supervisor:self.supervisor.close();self.supervisor=None

    def candidate(self,actor,project,job_id):
        job,source,record,qa=self.components.review.candidate(actor,project,job_id,current=False)
        observed=qa["worker_observations"]
        require(observed.get("kernel_unit")=="mm","CAD_UNITS","Only the component exporter's explicit millimetre native BREP contract is supported")
        plan=from_contracts(record.snapshot,record.feature_graph)
        parts=observed["parts"]
        require([p.part_id for p in plan.parts]==[p["part_id"] for p in parts],"CAD_PART_MAPPING","Source feature outputs and retained exporter order differ")
        raw=self.components.jobs.blob(actor,project,job_id,"source.brep")
        blob=next(b for b in job.blobs if b.name=="source.brep")
        require(0<len(raw)<=64*1024**2 and sha256(raw).hexdigest()==blob.content_hash,"CAD_SOURCE","Exact bounded retained native BREP required")
        provenance={"job_id":job.job_id,"build_commit_id":source.commit_id,"model_commit_id":json.loads(source.payload)["model_commit_id"],"geometry_revision_id":record.artifacts[0].geometry_revision_id,"source_sha256":blob.content_hash,"physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED"}
        return raw,parts,plan,provenance

    def run(self,raw,parts,request):
        cfg=configuration(self.path)
        with self.lock:
            if self.supervisor is None:self.supervisor=WorkerSupervisor(timeout_s=120,stdout_limit=16*1024**2,max_workers=1,max_queued=1)
            supervisor=self.supervisor
        command=WorkerCommand((cfg["python"],str(ROOT/"plugins/geometry/workers/cad_inspection_worker.py")),(("PYTHONPATH",str(ROOT)),("OMP_NUM_THREADS","1"),("OPENBLAS_NUM_THREADS","1")))
        payload={**request,"source_sha256":sha256(raw).hexdigest(),"parts":[{k:p[k] for k in ("part_id","volume_m3","centroid_m")} for p in parts]}
        with tempfile.TemporaryDirectory(prefix="cosmos-cad-inspect-") as directory:
            root=Path(directory).resolve();(root/"source.brep").write_bytes(raw)
            process=supervisor.submit("inspect-"+uuid4().hex,command,json.dumps(payload,allow_nan=False).encode(),root).result(timeout=130)
            require(process.code=="OK" and process.exit_code==0,"CAD_WORKER",("CAD worker failed: "+process.stderr.decode(errors="replace")[-500:]+process.stdout.decode(errors="replace")[-500:]))
            value=json.loads(process.stdout)
            require(value.get("ok") is True and value.get("source_sha256")==payload["source_sha256"],"CAD_WORKER","Native result source differs from request")
            result=value["result"];output=None
            if "output_name" in result:
                require(result["output_name"] in {"drawing.pdf","drawing.svg"},"CAD_OUTPUT","Unrecognized worker output")
                path=root/result["output_name"]
                require(path.is_file() and not path.is_symlink() and path.stat().st_size<=16*1024**2,"CAD_OUTPUT","Bounded private drawing output required")
                output=path.read_bytes();require(sha256(output).hexdigest()==result["output_sha256"],"CAD_OUTPUT","Drawing digest mismatch")
            return result,output

    def clearance(self,actor,project,job_id,query):
        require(set(query)=={"a","b","linear_tolerance_m","volume_resolution_m3","required_clearance_m"},"CAD_FIELDS","Exact part pair, numeric resolution and explicit required clearance required")
        raw,parts,_,source=self.candidate(actor,project,job_id)
        ids={p["part_id"] for p in parts};a,b=query["a"],query["b"]
        require(a!=b and a in ids and b in ids,"CAD_PART","Two distinct parts of this exact native source required")
        request={"operation":"clearance","pair":[a,b],"linear_tolerance_m":number(query["linear_tolerance_m"],1e-10,1e-4,"Numerical length resolution [m]"),"volume_resolution_m3":number(query["volume_resolution_m3"],1e-21,1e-6,"Numerical volume resolution [m³]"),"required_clearance_m":number(query["required_clearance_m"],0,5,"Required design clearance [m]")}
        result,_=self.run(raw,parts,request)
        return {"ok":True,"source":source,"inspection":result,"method_sha256":methods()}

    def drawing(self,actor,project,job_id,query,format):
        names={"part_id","title","number","revision","author","material","process","tolerance_note","finish_note","scale_denominator","curve_deflection_m"}
        require(set(query)==names and format in {"pdf","svg","json"},"CAD_FIELDS","Exact drawing title-block, scale, source part and curve deflection required")
        raw,parts,plan,source=self.candidate(actor,project,job_id);part=next((p for p in plan.parts if p.part_id==query["part_id"]),None)
        require(part is not None,"CAD_PART","Drawing part must belong to the retained source")
        metadata={}
        for key in names-{"part_id","scale_denominator","curve_deflection_m"}:
            value=query[key];require(type(value) is str and 0<len(value.strip())<= (72 if key in {"material","process","tolerance_note","finish_note"} else 80) and all(32<=ord(c)<=126 for c in value),"CAD_DRAWING_TEXT","Explicit bounded single-line ASCII drawing declarations required; no guessed material/tolerance/process")
            metadata[key]=value
        metadata["scale_denominator"]=number(query["scale_denominator"],.1,1000,"Drawing scale denominator")
        feature_ids=set();features={f.feature_id:f for f in plan.graph.features}
        def visit(key):
            if key in feature_ids:return
            feature_ids.add(key)
            for upstream in features[key].dependency_ids:visit(upstream)
        visit(part.feature_id)
        refs={r for k in feature_ids for r in features[k].parameter_refs}
        parameters=[{"name":p.name,"value":p.value_si,"unit":p.unit_symbol} for p in plan.snapshot.parameters_si if p.name in refs]
        require(len(parameters)<=512,"CAD_DRAWING_CAPACITY","Part schedule exceeds512 parameters; split the source explicitly")
        metadata.update(parameters=parameters,**source)
        result,output=self.run(raw,parts,{"operation":"drawing","part_id":part.part_id,"format":format,"curve_deflection_m":number(query["curve_deflection_m"],1e-7,1e-4,"Projected curve deflection [m]"),"metadata":metadata})
        return {"ok":True,"source":source,"drawing":result,"declarations":metadata,"method_sha256":methods()},output
