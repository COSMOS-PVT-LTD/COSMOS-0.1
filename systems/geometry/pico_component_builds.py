"""Source-bound PicoGK component policy over existing snapshot/job authority."""
from dataclasses import dataclass,asdict,replace
from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path
import threading
import time
from uuid import UUID,uuid5

from infrastructure.geometry import WorkerCommand,WorkerSupervisor
from plugins.geometry.pico_components import VERSION,POLICY,validate,field_graph,PicoComponentAdapter
from systems.contracts.geometry import DesignSnapshot,GeometryFeatureGraph,GeometryBuildRequest,Representation,OutputFormat
from systems.contracts.geometry._wire import require
from systems.geometry.authority import ManagedGeometry
from systems.geometry.component_authority import from_source,methods as component_methods
from systems.geometry.component_model import scalar
from systems.geometry.component_reference import ComponentReference,PartReference
from systems.geometry.engine_builds import EngineBuildCoordinator
from systems.geometry.pico_mesh_qa import read_mesh,audit_part,MAX_TRIANGLES
from systems.geometry.service import GeometryBuildService
from systems.geometry.workbench import Revision
from systems.persistence.project_repository import RecordPayload,Dependency
from systems.projects.authority import Head,HeadConflict,InvalidRecord,StoreUnavailable

DOMAIN="picogk-component-build"
SCHEMA="cosmos.picogk-component-build.v1"


def methods():
    root=Path(__file__).resolve().parents[2]
    names={"plugins/geometry/pico_components.py","plugins/geometry/workers/pico-components/Program.cs","plugins/geometry/workers/pico-components/PicoComponents.csproj",
        "systems/geometry/pico_mesh_qa.py","systems/geometry/pico_component_builds.py","systems/geometry/pico_preview.py","plugins/geometry/display_encoding.py","plugins/geometry/workers/pico_preview_worker.py","api/pico_components.py","api/pico_component_runtime.py"}
    return {**component_methods(),**{n:sha256((root/n).read_bytes()).hexdigest() for n in sorted(names)}}


@dataclass(frozen=True)
class PicoLimits:
    voxel_m:float
    relative_volume:float
    centroid_m:float
    forward_m:float
    reverse_m:float
    source:str

    @classmethod
    def from_spec(cls,spec):
        keys=("voxel_resolution","relative_volume","centroid","forward_residual","reverse_distance")
        require(type(spec) is dict and set(spec)==set(keys)|{"source"} and type(spec["source"]) is str and 0<len(spec["source"].strip())<=2048,"PICO_QA","Explicit voxel/volume/centroid/residual/reverse ceilings and applicability source required")
        numbers=[scalar(spec[k],"1" if k=="relative_volume" else "m") for k in keys]
        require(2.5e-5<=numbers[0]<=.002 and all(0<v<.1 for v in numbers[1:]),"PICO_QA","Positive finite explicit QA within bounded local research envelope required")
        return cls(*numbers,spec["source"])


@dataclass(frozen=True)
class PicoReference:
    plan:object
    parts:tuple=()
    @property
    def operation(self):return "picogk-engine-components-v1"


class PicoBuildService(GeometryBuildService):
    artifact_limit_bytes=256*1024**2
    policy_id=POLICY;reviewer_id="picogk-component-independent-mesh-audit"
    acceptance_stage="picogk_component_software_qa"
    acceptance_message="Implicit component candidates pass explicit sampled mesh QA; analytic CAD/manufacturing/physical acceptance NOT_PERFORMED"

    def __init__(self,backend,root,limits,preview_workspace=None):super().__init__(backend,root);self.limits=limits;self.preview_workspace=preview_workspace

    def submit(self,*args,conditioning_profile="raw",**kwargs):
        require(conditioning_profile in {"raw","exact_zero_faces_v1"},"PICO_CONDITIONING","Only declared exact-zero encoding profile supported")
        # This worker removes exact-zero faces per part before publishing ranges.
        # Do not apply generic assembly-wide conditioning that can invalidate IDs.
        return super().submit(*args,conditioning_profile="raw",**kwargs)

    def validate_policy(self,snapshot,reference):
        require(isinstance(reference,PicoReference) and reference.plan.snapshot==snapshot and snapshot.project_id.startswith("engine-component-"),"PICO_POLICY","Exact saved component reference required; no fixture policy substitution")

    def prepare_audit(self,output,reference):
        metrics=output.metrics;parts=metrics.get("parts");expected=reference.plan.parts
        require(metrics.get("input_unit")=="m" and metrics.get("kernel_unit")=="mm" and abs(metrics.get("actual_voxel_m",0)-self.limits.voxel_m)<=self.limits.voxel_m*1e-6
            and metrics.get("native_allocations_after")==0 and type(parts) is list and len(parts)==len(expected),"PICO_RESPONSE","Exact native units/resolution/disposal/part inventory required")
        tie_bound=64*2.220446049250313e-16*max(max(1,max(abs(v) for v in PartReference(reference.plan,p).bounds_m)*1000) for p in expected)/1000
        require(metrics.get("zero_isovalue_tie_break")=="positive within 64 double ULP scale of source bounds (mm); nominal recipes unchanged"
            and abs(metrics.get("zero_isovalue_max_bound_m",-1)-tie_bound)<=tie_bound*1e-12,"PICO_RESPONSE","Explicit source-scaled numerical zero tie rule required; no hidden geometric offset")
        start=0
        for p,item in zip(expected,parts,strict=True):
            require(set(item)=={"part_id","feature_id","frame_id","role","triangle_start","triangle_count","removed_exact_zero_faces","field_name"}
                and (item["part_id"],item["feature_id"],item["frame_id"],item["role"],item["field_name"])==(p.part_id,p.feature_id,p.frame_id,p.role,p.part_id)
                and item["triangle_start"]==start and type(item["triangle_count"]) is int and item["triangle_count"]>0 and type(item["removed_exact_zero_faces"]) is int and item["removed_exact_zero_faces"]>=0,"PICO_RESPONSE","Source-bound contiguous actual part ranges required")
            start+=item["triangle_count"]
        require(start==metrics.get("triangle_count") and start<=MAX_TRIANGLES and metrics.get("vdb_roundtrip_fields")==[p.part_id for p in expected],"PICO_RESPONSE","Complete named VDB round trip and mesh inventory required")
        return replace(reference,parts=tuple(parts))

    def audit_candidate(self,path,format_,reference,request,job,token):
        require(format_=="stl","PICO_FORMAT","Only explicit implicit STL mesh audit is supported")
        raw,records=read_mesh(path);require(len(records)==sum(p["triangle_count"] for p in reference.parts),"PICO_RANGE","Part map does not cover actual triangles")
        deadline=time.monotonic()+300
        def budget():
            require(not token.is_set(),"CANCELLED","PicoGK mesh QA cancelled")
            require(time.monotonic()<deadline,"PICO_QA_TIMEOUT","Independent mesh QA exceeded300-second software budget")
        results=[]
        for p,item in zip(reference.plan.parts,reference.parts,strict=True):
            start=item["triangle_start"];results.append(audit_part(records[start:start+item["triangle_count"]],PartReference(reference.plan,p),self.limits,budget))
        display=None
        if all(r["pass"] for r in results) and len(records)>199900 and self.preview_workspace is not None:
            from systems.geometry.pico_preview import reduce_preview
            positions,parts,_,display=reduce_preview(self.preview_workspace,raw,list(reference.parts),reference.plan,self.limits,cancellation=token,check_budget=budget)
            budget()
            display={**display,"parts_map":parts}
            for name,value in (("preview.f32",positions),("preview.json",json.dumps(display,allow_nan=False,sort_keys=True).encode())):
                with (path.parent/name).open("xb") as f:f.write(value)
        return {"pass":all(r["pass"] for r in results),"topology_pass":all(r["topology_pass"] for r in results),"dimensions_pass":all(r["dimensions_pass"] for r in results),"parts":results,
            "display_preview":display,"representation":"implicit_field","export_representation":"tessellated_surface","analytic_step_available":False,"physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED"}


class PicoWorkspace:
    def __init__(self,root,configuration):
        self.root=Path(root);require(self.root.is_absolute() and not self.root.is_symlink(),"PICO_PATH","Owned absolute non-symlink candidate root required");self.root.mkdir(mode=0o700,exist_ok=True);self.configuration=configuration
        self.supervisor=WorkerSupervisor(timeout_s=300,stdout_limit=4*1024**2);self.services={};self.lock=threading.Lock();self.closed=False
        self.preview_lock=threading.Lock();self.previews={}
    @property
    def runtime_hashes(self):
        cfg=self.configuration();return {**cfg["sha256"],"runtime-manifest":cfg["manifest_sha256"]}
    def service_for(self,limits):
        cfg=self.configuration()
        with self.lock:
            require(not self.closed,"SERVICE_CLOSED","PicoGK workspace closed")
            if limits not in self.services:
                require(len(self.services)<16,"PICO_QA_CAPACITY","At most16 explicit QA profiles per application lifetime")
                c=cfg["worker"];command=WorkerCommand(tuple(c["argv"]),tuple(c["environment"].items()))
                self.services[limits]=PicoBuildService(PicoComponentAdapter("picogk",command,self.supervisor,enabled=True),self.root,limits,self)
            return self.services[limits]
    def close(self):
        self.closed=True
        for s in self.services.values():s.close()
        self.supervisor.close()


class PicoCoordinator(EngineBuildCoordinator):
    def __init__(self,repository,jobs,factory,resolve_actor,models):
        ManagedGeometry.__init__(self,repository,jobs,dict,resolve_actor)
        self.factory,self.models,self.loaded_methods=factory,models,methods()
    def current(self,actor,source):
        value=json.loads(source.payload)
        return source.domain==DOMAIN and source.schema_id==SCHEMA and self.repository.dependencies_current(actor,source.project_id,source.commit_id) and value["method_sources"]==self.loaded_methods==methods() and self.models.current(actor,self.repository.resolve_snapshot(actor,source.project_id,value["model_commit_id"]))
    def capture(self,actor,project,model_commit,expected,qa_specification,operation_id,command_hash):
        actor.require(write=True);op="pico-component-input."+sha256((actor.user_id+operation_id).encode()).hexdigest();capture_hash=sha256((command_hash+":input").encode()).hexdigest()
        prior=self.repository.resolve_command(actor,project,operation_id=op,command_hash=capture_hash)
        if prior is not None:return prior
        source=self.repository.resolve_snapshot(actor,project,model_commit)
        if not self.models.current(actor,source):raise InvalidRecord("PicoGK requires an exact CURRENT saved component model and engine baseline")
        if source.head!=expected:raise HeadConflict(source.head)
        if methods()!=self.loaded_methods:raise StoreUnavailable("PicoGK methods changed; restart and reconcile")
        limits=PicoLimits.from_spec(qa_specification);plan=from_source(source);graph=field_graph(plan)
        values={p.name:p.value_si for p in plan.snapshot.parameters_si};object_id=str(uuid5(UUID(project),actor.user_id+":pico-component-build:"+operation_id))
        request=GeometryBuildRequest("request-"+object_id,plan.snapshot.snapshot_id,graph.graph_id,graph.content_sha256,"picogk",VERSION,Representation.IMPLICIT_FIELD,"sparse_volume",values["source_tolerance"],values["export_tolerance"],limits.voxel_m,(OutputFormat.STL,),"world","build-"+object_id)
        validate(request,plan.snapshot,graph);workspace=self.factory()
        value={"model_commit_id":source.commit_id,"model_sha256":source.head.content_hash,"model_canonical_json":source.payload.decode(),"snapshot_json":plan.snapshot.to_json(),"graph_json":graph.to_json(),"request_json":request.to_json(),
            "qa_specification":qa_specification,"method_sources":self.loaded_methods,"runtime_hashes":workspace.runtime_hashes,
            "command":{"model_commit_id":source.commit_id,"expected_model":asdict(expected),"qa_specification":qa_specification,"output_formats":["stl"],"operation_id":operation_id},
            "scope":"PicoGK fields generated directly from saved dimensional intent; independent sampled mesh QA, not analytic BREP/STEP or physical acceptance"}
        return self.repository.save_snapshot(actor,project,domain=DOMAIN,object_id=object_id,input_revision=source.input_revision,payload=RecordPayload.from_mapping(value,SCHEMA,source_namespace=plan.snapshot.project_id),expected=Head.absent(),operation_id=op,command_hash=capture_hash,dependencies=(Dependency("component-model",source.commit_id),))
    def decode(self,source):
        if source.domain!=DOMAIN or source.schema_id!=SCHEMA:raise InvalidRecord("Exact PicoGK component build source required")
        value=json.loads(source.payload);snapshot=DesignSnapshot.from_json(value["snapshot_json"]);graph=GeometryFeatureGraph.from_json(value["graph_json"]);request=GeometryBuildRequest.from_json(value["request_json"])
        validate(request,snapshot,graph);PicoLimits.from_spec(value["qa_specification"])
        if value["method_sources"]!=self.loaded_methods or methods()!=self.loaded_methods:raise StoreUnavailable("Captured PicoGK component methods changed; capture a new explicit build")
        return Revision(value,snapshot,graph,request)
    def select_service(self,revision):
        workspace=self.factory()
        if workspace.runtime_hashes!=revision.settings["runtime_hashes"]:raise StoreUnavailable("Captured PicoGK runtime changed; no silent retry")
        return workspace.service_for(PicoLimits.from_spec(revision.settings["qa_specification"]))
    def reference(self,revision):return PicoReference(validate(revision.request,revision.snapshot,revision.graph))

    @staticmethod
    def collect(candidate):
        from plugins.geometry.protocol import checked_file
        from systems.persistence.job_repository import BlobAttachment
        items={}
        for artifact in candidate.record.artifacts:
            for name,digest,kind in ((artifact.storage_uri.rsplit("/",1)[-1],artifact.sha256,"artifact"),("source.vdb",artifact.source_artifact_sha256,"source")):
                path=checked_file(candidate.directory,name,digest,max_bytes=256*1024**2)
                raw=path.read_bytes();require(sha256(raw).hexdigest()==digest,"PICO_RETENTION","Candidate changed while retaining original")
                items[name]=BlobAttachment(name,raw,digest,kind)
        proof=json.loads(candidate.evidence_json).get("qa-stl",{}).get("display_preview")
        if proof is not None:
            for name,limit in (("preview.f32",7200000),("preview.json",1024**2)):
                path=candidate.directory/name;require(path.is_file() and not path.is_symlink() and 0<path.stat().st_size<=limit,"PICO_RETENTION","Bounded display proof required")
                raw=path.read_bytes();digest=sha256(raw).hexdigest()
                if name=="preview.f32":require(digest==proof["preview_sha256"],"PICO_RETENTION","Display changed during retention")
                else:require(json.loads(raw)==proof,"PICO_RETENTION","Display proof changed during retention")
                items[name]=BlobAttachment(name,raw,digest,"diagnostic")
        return tuple(items.values())
