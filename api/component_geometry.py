"""Managed component editor/build/review/handoff. No geometry math in GUI/API."""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import ClassVar
from uuid import UUID, uuid5

from api.geometry_projects import BinarySource
from api.nozzle_geometry import EngineBuildsAPI
from api.nozzle_geometry import runtime_configuration as nozzle_runtime
from infrastructure.geometry import WorkerCommand
from systems.contracts.geometry._wire import digest, require
from systems.geometry.component_authority import (
    BUILD_DOMAIN,
    BUILD_SCHEMA,
    DOMAIN,
    ComponentCoordinator,
    ComponentModels,
)
from systems.geometry.component_model import OPERATIONS, POLICY, SCHEMA, VERSION
from systems.geometry.component_review import (
    REVIEW_DOMAIN,
    STUDY_DOMAIN,
    ComponentReview,
)
from systems.projects.authority import (
    Head,
    InvalidRecord,
    RecordNotFound,
    StoreUnavailable,
)


class ComponentEvidenceSource(BinarySource):
    """Original evidence can be historical/rejected, never automatic acceptance."""


class ReviewedAnalysisSource(BinarySource):
    """Current independently attested geometry-analysis exchange, NOT manufacturing."""


def runtime_configuration(path):
    if path is not None and json.loads(Path(path).read_bytes()).get("schema")=="cosmos.occt-component-runtime.v1":
        from api.occt_component_runtime import configuration
        return configuration(path)
    config=nozzle_runtime(path)
    item=config.get("engine_components")
    require(type(item) is dict and set(item)=={"policy","version","worker","reader","receipt","receipt_sha256"} and item["policy"]==POLICY and item["version"]==VERSION,"COMPONENT_RUNTIME_REQUIRED","Separately qualified component runtime required; fixture/nozzle receipt is not component qualification")
    assert isinstance(item,dict)
    root=Path(__file__).resolve().parents[1]
    for role,file in (("worker","component_worker.py"),("reader","component_step_reader.py")):
        command=item[role]; script=root/"plugins/geometry/workers"/file
        require(type(command) is dict and set(command)=={"argv","environment"} and command["argv"]==[config["occt"]["argv"][0],str(script)] and command["environment"]==config["occt"]["environment"] and str(script) in config["sha256"],"COMPONENT_RUNTIME_REQUIRED","Only separately pinned component commands in the qualified native interpreter/environment may execute")
        WorkerCommand(tuple(command["argv"]),tuple(command["environment"].items()))
    receipt=Path(item["receipt"])
    require(receipt.is_absolute() and receipt.is_file() and not receipt.is_symlink() and sha256(receipt.read_bytes()).hexdigest()==item["receipt_sha256"],"COMPONENT_QUALIFICATION_REQUIRED","Exact separate component software-qualification receipt required")
    value=json.loads(receipt.read_bytes())
    require(value.get("policy")==POLICY and value.get("version")==VERSION and value.get("software_qa_pass") is True and value.get("physical_validation")=="NOT_PERFORMED" and type(value.get("method_sources")) is dict,"COMPONENT_QUALIFICATION_REQUIRED","Separate passing component software evidence required; human/physical readiness cannot be fabricated")
    from systems.geometry.component_authority import methods
    expected={str(root/name):checksum for name,checksum in methods().items()}
    require(value["method_sources"]==expected and all(config["sha256"].get(name)==checksum for name,checksum in expected.items()),"COMPONENT_METHOD_CHANGED","Component methods must match the separate receipt and runtime manifest; reconcile/requalify, never rewrite historical receipts")
    return config


def create_workspace(root,path,*,enabled):
    from systems.geometry.component_workspace import ComponentWorkspace
    if not enabled or path is None: raise StoreUnavailable("Component native building is disabled; use an explicit separately qualified local runtime")
    runtime_configuration(path)
    return ComponentWorkspace(root/"engine_component_candidates",lambda:runtime_configuration(path))


def catalog():
    profiles={"title":"Profile wall / solid","parameters":[],"profile_columns":{"x":"m","inner":"m","outer":"m"},"minimum_points":2,"maximum_points":129}
    plate={"radius":"m","thickness":"m","ring_radius":"m","count":"1","hole_radius":"m","phase":"rad"}
    return {
        "profile.wall":{**profiles,"title":"Chamber / convergent / throat / nozzle wall"},"profile.solid":{**profiles,"title":"Solid axisymmetric profile"},
        "cooling.axial_sector":{"title":"Internal axial sector cooling channels","parameters":{"count":"1","width":"rad","hot_ligament":"m","depth":"m","phase":"rad","fluid_domains":"1"},"requires_one_wall_operand":True},
        "injector.showerhead":{"title":"Showerhead drilled plate","parameters":plate},
        "injector.doublet":{"title":"Impinging-doublet drilled plate","parameters":{**plate,"separation":"m","angle":"rad"}},
        "injector.biprop_doublet":{"title":"Hydraulic-source bipropellant doublet (distinct fuel / oxidizer ports)","parameters":{**{key:unit for key,unit in plate.items() if key!="hole_radius"},"fuel_hole_radius":"m","oxidizer_hole_radius":"m","separation":"m","angle":"rad"}},
        "injector.biprop_radial_doublet":{"title":"Radial bipropellant doublet / separate annular feed rings","parameters":{**{key:unit for key,unit in plate.items() if key!="hole_radius"},"fuel_hole_radius":"m","oxidizer_hole_radius":"m","separation":"m","angle":"rad"}},
        "manifold.dual_annular":{"title":"Isolated fuel / LOX annular manifold head with real cap ports","parameters":{**{key:"m" for key in ("radius","back_web","plenum_length","front_web","fuel_inner","fuel_outer","oxidizer_inner","oxidizer_outer","fuel_inlet_radius","oxidizer_inlet_radius","ring_radius","separation","fuel_hole_radius","oxidizer_hole_radius")},"count":"1","phase":"rad","fuel_inlet_phase":"rad","oxidizer_inlet_phase":"rad"}},
        "interface.bolted_flange":{"title":"Annular bolted flange / explicit clearance holes (not a joint qualification)","parameters":{**{key:"m" for key in ("bore_radius","outer_radius","thickness","bolt_circle_radius","bolt_hole_radius")},"count":"1","phase":"rad"}},
        "interface.bolt_pattern":{"title":"Clearance-hole cuts on one uniform annular operand; not a pressure-joint sizing","parameters":{"bolt_circle_radius":"m","bolt_hole_radius":"m","count":"1","phase":"rad"},"requires_one_wall_operand":True},
        "interface.face_groove":{"title":"Blind annular face-groove geometry; seal selection and pressure acceptance required separately","parameters":{"inner_radius":"m","outer_radius":"m","depth":"m","face":"1"},"requires_one_wall_operand":True},
        "interface.face_grooves":{"title":"Bounded indexed blind face grooves (count1..5); not selected or qualified seals","parameters":{"count":"1",**{name+str(i):unit for i in range(5) for name,unit in (("inner_radius","m"),("outer_radius","m"),("depth","m"),("face","1"))}},"requires_one_wall_operand":True},
        "manifold.cooling_front_supply":{"title":"Cooling collector with separate front-face outlet outside channel ports","parameters":{**{key:"m" for key in ("bore_radius","outer_radius","back_web","plenum_length","front_web","plenum_inner","plenum_outer","port_inner","port_outer","supply_hole_radius")},"count":"1","width":"rad","phase":"rad","supply_phase":"rad"}},
        "manifold.cooling_annular":{"title":"Cooling inlet / collector annular header with real channel cap ports","parameters":{**{key:"m" for key in ("bore_radius","outer_radius","back_web","plenum_length","front_web","plenum_inner","plenum_outer","port_inner","port_outer","supply_hole_radius")},"count":"1","width":"rad","phase":"rad","supply_phase":"rad"}},
        "pipe.circular":{"title":"Explicit circular straight pipe; fluid assignment and joints remain separate","parameters":{key:"m" for key in ("bore_radius","wall_thickness","length")}},
        "pipe.elbow":{"title":"Toroidal circular pipe elbow; no inferred bend loss or pressure rating","parameters":{**{key:"m" for key in ("bore_radius","wall_thickness","bend_radius")},"angle":"rad"}},
        "injector.triplet":{"title":"Impinging-triplet drilled plate","parameters":{**plate,"separation":"m","angle":"rad"}},
        "injector.coaxial":{"title":"Shear-coaxial tube assembly","parameters":{key:"m" for key in ("length","inner_bore","inner_outer","outer_inner","outer_radius")}},
        "injector.pintle":{"title":"Continuous-gap pintle / rod / sleeve assembly","parameters":{key:"m" for key in ("length","rod_radius","stem_inner","stem_outer","sleeve_inner","sleeve_outer","radial_gap","tip_length","tip_radius")}},
        "placement.rigid":{"title":"Proper rigid placement in selected child frame","parameters":{},"requires_one_operand":True},
    }


class ComponentBuildsAPI(EngineBuildsAPI):
    domain=BUILD_DOMAIN; schema=BUILD_SCHEMA; policy=POLICY; version=VERSION
    source_key="model_commit_id"; expected_key="expected_model"; file_stem="component"
    qa_units:ClassVar[dict[str,str]]={"relative_volume":"1","centroid":"m","implicit_residual":"m","reverse_distance":"m","semantic_relative_area":"1","semantic_centroid":"m"}
    build_scope="Exact component feature graph → bounded analytic CAD/Boolean/rigid-placement build → per-part formula/topology/STEP/STL/semantic QA → unreviewed candidates. Independent human review and analysis handoff are separate; no manufacturing or engine solver claim."


class ComponentGeometryAPI:
    def __init__(self,repository,jobs,factory,resolve_actor):
        self.models=ComponentModels(repository)
        self.builds=ComponentBuildsAPI(ComponentCoordinator(repository,jobs,factory,resolve_actor,self.models))
        self.review=ComponentReview(self.builds.coordinator)
        self.repository,self.jobs=repository,jobs

    def evidence(self,actor,source):
        value=json.loads(source.payload)
        if source.domain==REVIEW_DOMAIN:
            current=self.review.current(actor,source)
        elif source.domain==STUDY_DOMAIN:
            current=self.repository.dependencies_current(actor,source.project_id,source.commit_id) and self.review.current(actor,self.repository.resolve_snapshot(actor,source.project_id,value["review_commit_id"]))
        else: raise InvalidRecord("Exact component review/study source required")
        return {"ok":True,"authority":{"project_id":source.project_id,"object_id":source.object_id,"commit_id":source.commit_id,"head":asdict(source.head)},"source_canonical_json":source.payload.decode(),"record":value,"upstream_current":current,"physical_validation":"NOT_PERFORMED","scope":"Exact retained review/setup source; currentness is not physical validation or a runnable engine solver"}

    def handle(self,actor,method,project,domain,parts,query,body):
        from api.project_authority import expected_head
        if domain=="component-geometry-builds":
            if len(parts)==4 and parts[1]=="jobs" and parts[3]=="sections" and method=="GET":
                if set(query)!={"part_id","x_m"} or any(len(v)!=1 for v in query.values()): raise InvalidRecord("Exact part ID and explicit local axial position [m] required; arbitrary planes are unsupported")
                from systems.geometry.component_model import from_contracts
                from systems.geometry.component_sections import section
                job,source,record,_qa=self.review.candidate(actor,project,parts[2],current=False)
                if job.object_id!=parts[0]: raise RecordNotFound("Job belongs to another exact build source")
                value=section(from_contracts(record.snapshot,record.feature_graph),query["part_id"][0],float(query["x_m"][0]))
                return {"ok":True,"job_id":job.job_id,"build_commit_id":source.commit_id,"geometry_revision_id":record.artifacts[0].geometry_revision_id,"section":value,"physical_validation":"NOT_PERFORMED"}
            if len(parts)==4 and parts[1]=="jobs" and parts[3] in {"review-context","measurements"} and method=="GET":
                if query: raise InvalidRecord("Exact current job context; query overrides forbidden")
                job=self.jobs.get(actor,project,parts[2])
                if job.object_id!=parts[0]: raise RecordNotFound("Job belongs to another exact build source")
                return self.review.context(actor,project,parts[2])
            return self.builds.handle(actor,method,project,parts,query,body)
        if any(len(values)!=1 for values in query.values()): raise InvalidRecord("Duplicate component query fields")
        allowed={"limit","after"} if not parts and method=="GET" else {"before","limit"} if len(parts)==2 and parts[1]=="history" and method=="GET" else {"commit"} if method=="GET" and parts and parts[0]!="capabilities" and (len(parts)==1 or parts[1:]==["record.json"]) else set()
        if set(query)-allowed: raise InvalidRecord("Unknown component context/query; no historical override of a mutation")
        command_hash=digest({"project":project,"domain":domain,"path":parts,"body":body})
        if domain=="component-geometry":
            if parts==["capabilities"] and method=="GET":
                return {"ok":True,"schema":SCHEMA,"catalog":catalog(),"operations":list(OPERATIONS),"outputs":"Explicit final feature outputs; consumed operands must not be exported twice","maximum_features":24,"maximum_parts":24,"maximum_triangles":200000,"scope":"Bounded parametric geometry, not atomization/swirl/combustion stability, thermal sizing, manufacturing or physical acceptance. Internal cooling uses radial-depth constant-angular-width axial sectors, not silently the existing rectangular thermal model."}
            if parts==["preview"] and method=="POST":
                if set(body)!={"specification","object_id"}: raise InvalidRecord("Exact draft specification/object context required")
                return self.models.preview(actor,project,body["specification"],object_id=body["object_id"])
            if parts==["seed-from-design"] and method=="POST":
                if set(body)!={"baseline_commit_id","settings"}: raise InvalidRecord("Exact baseline and explicitly supplied missing CAD dimensions required")
                return self.models.seed(actor,project,body["baseline_commit_id"],body["settings"])
            if parts==["seed-injector-from-design"] and method=="POST":
                if set(body)!={"baseline_commit_id","settings"}: raise InvalidRecord("Exact current injector baseline and explicit CAD layout required")
                return self.models.seed_injector(actor,project,body["baseline_commit_id"],body["settings"])
            if not parts and method=="GET":
                return {"ok":True,"models":[asdict(v) for v in self.repository.list_objects(actor,project,domain=DOMAIN,limit=int(query.get("limit",["20"])[0]),after_id=query.get("after",[""])[0])]}
            if not parts or len(parts)==1:
                if method=="GET": return self.models.envelope(actor,self.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=parts[0],commit_id=query.get("commit",[None])[0]))
                if set(body)!={"title","baseline_commit_id","expected_baseline","specification","expected","operation_id"}: raise InvalidRecord("Exact title, baseline/head, explicit feature model, model head and operation required")
                object_id=parts[0] if parts else str(uuid5(UUID(project),actor.user_id+":component-model:"+body["operation_id"]))
                expected=expected_head(body["expected"])
                if not parts and expected!=Head.absent(): raise InvalidRecord("New component model requires absent expected head")
                source=self.models.save(actor,project,object_id,title=body["title"],baseline_commit=body["baseline_commit_id"],expected_baseline=expected_head(body["expected_baseline"]),specification=body["specification"],expected=expected,operation_id=body["operation_id"],command_hash=command_hash)
                return self.models.envelope(actor,source)
            source=self.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=parts[0],commit_id=query.get("commit",[None])[0])
            if parts[1:]==["record.json"] and method=="GET": return ComponentEvidenceSource("component-model.json",source.payload,source.head.content_hash)
            if parts[1:]==["history"] and method=="GET":
                ids=self.repository.list_commit_ids(actor,project,domain=DOMAIN,object_id=source.object_id,limit=int(query.get("limit",["20"])[0]),before_version=int(query["before"][0]) if "before" in query else None)
                return {"ok":True,"commits":[{"commit_id":s.commit_id,"head":asdict(s.head),"input_revision":s.input_revision} for s in (self.repository.resolve_snapshot(actor,project,key) for key in ids)]}
            if parts[1:]==["restore"] and method=="POST":
                if set(body)!={"origin_commit_id","expected","expected_baseline","operation_id"}: raise InvalidRecord("Explicit exact restore origin/head/baseline head and operation required")
                origin=self.repository.resolve_snapshot(actor,project,body["origin_commit_id"]); value=json.loads(origin.payload)
                saved=self.models.save(actor,project,source.object_id,title=value["title"],baseline_commit=value["baseline_commit_id"],expected_baseline=expected_head(body["expected_baseline"]),specification=value["specification"],expected=expected_head(body["expected"]),operation_id=body["operation_id"],command_hash=command_hash,origin_commit=origin.commit_id)
                return self.models.envelope(actor,saved)
        elif domain in {"component-geometry-reviews","component-studies"}:
            selected=REVIEW_DOMAIN if domain=="component-geometry-reviews" else STUDY_DOMAIN
            if not parts:
                if method=="GET": return {"ok":True,"records":[asdict(s) for s in self.repository.list_objects(actor,project,domain=selected,limit=int(query.get("limit",["20"])[0]),after_id=query.get("after",[""])[0])]}
                if selected==REVIEW_DOMAIN:
                    if set(body)!={"job_id","review"}: raise InvalidRecord("Exact candidate job and explicit independent review required")
                    source=self.review.review(actor,project,body["job_id"],body["review"],command_hash=command_hash)
                else:
                    if set(body)!={"review_commit_id","operation_id"}: raise InvalidRecord("Exact independently reviewed source and operation required; no posted mesh/result/solver authority")
                    source=self.review.handoff(actor,project,body["review_commit_id"],operation_id=body["operation_id"],command_hash=command_hash)
                return self.evidence(actor,source)
            if parts==["remap-proposal"] and method=="POST" and selected==REVIEW_DOMAIN:
                if set(body)!={"review_commit_id","new_job_id"}: raise InvalidRecord("Exact old review and new current geometry job required")
                return self.review.remap_proposal(actor,project,body["review_commit_id"],body["new_job_id"])
            source=self.repository.get_snapshot(actor,project,domain=selected,object_id=parts[0],commit_id=query.get("commit",[None])[0])
            if len(parts)==1 and method=="GET": return self.evidence(actor,source)
            if parts[1:]==["record.json"] and method=="GET": return ComponentEvidenceSource("component-review.json" if selected==REVIEW_DOMAIN else "component-study-setup.json",source.payload,source.head.content_hash)
            if len(parts)==3 and parts[1]=="blobs" and method=="GET":
                value=json.loads(source.payload)
                review=source if selected==REVIEW_DOMAIN else self.repository.resolve_snapshot(actor,project,value["review_commit_id"])
                require(self.review.current(actor,review) and json.loads(review.payload)["published_record_json"] is not None,"STALE_REVIEW","Current independent analysis acceptance required for reviewed exchange; historical unreviewed originals remain accessible through build history")
                require(parts[2] in {"source.brep","export.step","export.stl"},"COMPONENT_EXCHANGE","Only exact retained reviewed source/exchanges may be downloaded")
                job_id=json.loads(review.payload)["job_id"]; self.review.candidate(actor,project,job_id)
                raw=self.jobs.blob(actor,project,job_id,parts[2]); return ReviewedAnalysisSource(parts[2],raw,sha256(raw).hexdigest())
        raise RecordNotFound("Unsupported component editor/review/study route; no engine solver fallback")
