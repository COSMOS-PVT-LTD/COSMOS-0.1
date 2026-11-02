"""PicoGK saved-component jobs, native/mesh originals and explicit display-only LOD."""
from hashlib import sha256
import json
from dataclasses import asdict

import numpy as np

from api.nozzle_geometry import EngineBuildsAPI,EngineCandidateSource,EnginePreviewSource
from plugins.geometry.pico_components import VERSION,POLICY
from systems.geometry.pico_component_builds import DOMAIN,SCHEMA,PicoCoordinator
from systems.geometry.pico_mesh_qa import MAX_TRIANGLES
from systems.geometry.qa import STL_RECORD
from systems.projects.authority import InvalidRecord,RecordNotFound,StoreUnavailable
from systems.contracts.geometry._wire import require


def preview(raw,parts):
    """Unmodified small mesh only. Never discard triangles to fake a large preview."""
    n=int.from_bytes(raw[80:84],"little");require(b"UNITS= m" in raw[:80] and 0<n<=MAX_TRIANGLES and len(raw)==84+50*n,"PICO_PREVIEW","Complete bounded SI STL required")
    require(n<=199900,"PICO_PREVIEW","Large mesh requires its retained topology-preserving display reduction; original geometry unchanged")
    source=np.frombuffer(raw,STL_RECORD,count=n,offset=84);arrays=[];display=[];start=0
    for p in parts:
        count=p["triangle_count"];budget=max(1,int(count*min(1,199900/n)))
        index=np.linspace(p["triangle_start"],p["triangle_start"]+count-1,budget,dtype=int)
        arrays.append(source["vertices"][index]);display.append({**p,"source_triangle_start":p["triangle_start"],"source_triangle_count":count,"triangle_start":start,"triangle_count":budget});start+=budget
    data=np.concatenate(arrays).astype("<f4").tobytes();require(len(data)<=7200000 and bool(np.isfinite(np.frombuffer(data,dtype="<f4")).all()),"PICO_PREVIEW","Display buffer exceeds qualified shared viewport bounds")
    return data,display,start<n


class PicoComponentsAPI(EngineBuildsAPI):
    domain=DOMAIN;schema=SCHEMA;policy=POLICY;version=VERSION
    source_key="model_commit_id";expected_key="expected_model";file_stem="picogk-components"
    qa_units={"voxel_resolution":"m","relative_volume":"1","centroid":"m","forward_residual":"m","reverse_distance":"m"}
    build_scope="Saved feature intent → PicoGK implicit named fields → independent per-part sampled STL QA. VDB/STL originals; no analytic STEP, BREP metrology, manufacturing or physical acceptance."

    def __init__(self,repository,jobs,factory,resolve_actor,models):super().__init__(PicoCoordinator(repository,jobs,factory,resolve_actor,models))

    def handle(self,actor,method,project,parts,query,body):
        self.coordinator.repository.get_project(actor,project)
        if parts==["capabilities"] and method=="GET":
            require(not query,"PICO_FIELDS","No capability overrides")
            configured=False;reason=""
            try:configured=bool(self.coordinator.factory().runtime_hashes)
            except (ValueError,OSError,RuntimeError,StoreUnavailable) as error:reason=str(error)[:1024]
            return {"ok":True,"runtime_configured":configured,"unavailable_reason":reason,"policy":POLICY,"version":VERSION,"output_formats":["stl"],"native_format":"vdb","qa_units":self.qa_units,"scope":self.build_scope,"analytic_step_available":False}
        if not parts and method=="POST":
            from api.project_authority import expected_head
            require(not query and set(body)=={"model_commit_id","expected_model","qa_specification","output_formats","operation_id"} and body["output_formats"]==["stl"],"PICO_FIELDS","Exact saved model/head, explicit QA/voxel, STL output and operation identity required")
            digest=sha256(json.dumps({"project":project,"path":parts,"body":body},sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
            replay=self.coordinator.jobs.resolve_command(actor,project,operation_id=body["operation_id"],request_hash=digest)
            if replay is not None:return self.job(actor,replay)
            source=self.coordinator.capture(actor,project,body["model_commit_id"],expected_head(body["expected_model"]),body["qa_specification"],body["operation_id"],digest)
            return self.job(actor,self.coordinator.start(actor,source,operation_id=body["operation_id"],request_hash=digest))
        if len(parts)>=4 and parts[1]=="jobs" and method=="GET" and (parts[3] in {"blobs","preview","mesh-context"}):
            require(not query,"PICO_FIELDS","Exact retained source; no display/source overrides")
            source=self.coordinator.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=parts[0]);job=self.coordinator.jobs.get(actor,project,parts[2])
            if job.domain!=DOMAIN or job.object_id!=source.object_id or job.state.value!="COMPLETED":raise RecordNotFound("Completed PicoGK job must belong to this exact saved source/project")
            if parts[3]=="blobs" and len(parts)==5:
                require(parts[4] in {"source.vdb","export.stl"},"PICO_FORMAT","Only retained implicit VDB and mesh STL originals; analytic STEP unavailable")
                raw=self.coordinator.jobs.blob(actor,project,job.job_id,parts[4]);return EngineCandidateSource("picogk-components-"+parts[4],raw,sha256(raw).hexdigest())
            if len(parts)==4:
                record=json.loads(job.payload);proof=json.loads(record["evidence_json"]);raw=self.coordinator.jobs.blob(actor,project,job.job_id,"export.stl")
                reduction=proof["qa-stl"].get("display_preview")
                if reduction is None:positions,display,decimated=preview(raw,proof["worker_observations"]["parts"])
                else:
                    positions=self.coordinator.jobs.blob(actor,project,job.job_id,"preview.f32")
                    require(sha256(raw).hexdigest()==reduction["source_sha256"] and sha256(positions).hexdigest()==reduction["preview_sha256"],"PICO_PREVIEW","Retained display/source checksum mismatch")
                    display,decimated=reduction["parts_map"],True
                if parts[3]=="preview":return EnginePreviewSource("picogk-components-display-only.f32",positions,sha256(positions).hexdigest())
                return {"ok":True,"job_id":job.job_id,"source_commit_id":source.commit_id,"model_commit_id":json.loads(source.payload)["model_commit_id"],"source_sha256":sha256(raw).hexdigest(),"preview_sha256":sha256(positions).hexdigest(),
                    "representation":"implicit_field","parts":display,"measurements":proof["qa-stl"]["parts"],"preview_decimated":decimated,"preview_reduction":reduction,"analytic_metrology_available":False,"scope":self.build_scope,"physical_validation":"NOT_PERFORMED"}
        return super().handle(actor,method,project,parts,query,body)
