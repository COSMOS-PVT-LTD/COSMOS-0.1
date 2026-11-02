"""Independent human-attested analysis review and revision-bound study preparation."""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
from uuid import UUID, uuid5

import numpy as np

from simulation.component_handoff import (
    ComponentHandoff,
    ComponentInterface,
    ComponentMaterialRegion,
    ComponentMeshConstraints,
    ComponentStudySetup,
)
from systems.contracts.geometry import (
    BuildState,
    Disposition,
    GeometryBuildEvent,
    GeometryBuildRecord,
    GeometryCheck,
    GeometryValidationReport,
    MappingStatus,
    NamedSelection,
)
from systems.contracts.geometry._wire import require
from systems.geometry.component_authority import (
    BUILD_DOMAIN,
    ComponentCoordinator,
    methods,
)
from systems.persistence.job_repository import JobState
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import AccessDenied, Head, HeadConflict, InvalidRecord

REVIEW_DOMAIN="engine-component-review"
REVIEW_SCHEMA="cosmos.component-engineering-review.v1"
STUDY_DOMAIN="engine-component-study"
STUDY_SCHEMA="cosmos.component-study-setup.v1"
CHECKS={"source_applicability","topology_and_dimensions","channels_ports_and_ligaments","named_boundaries_and_interfaces","materials_and_mesh_constraints","declared_limitations"}


class ComponentReview:
    def __init__(self,coordinator:ComponentCoordinator):
        self.coordinator=coordinator; self.repository=coordinator.repository; self.jobs=coordinator.jobs

    def candidate(self,actor,project,job_id,*,current=True):
        job=self.jobs.get(actor,project,job_id)
        require(job.domain==BUILD_DOMAIN and job.state is JobState.COMPLETED,"COMPONENT_REVIEW","Exact completed component candidate required; no fixture/nozzle substitution")
        source=self.repository.resolve_snapshot(actor,project,job.source_commit_id)
        if current:
            require(job.selected and job.current_input and self.coordinator.current(actor,source) and self.coordinator.runtime_current(source),"STALE_COMPONENT","Review/handoff requires current selected component source/method/runtime and attempt")
        value=json.loads(job.payload); record=GeometryBuildRecord.from_json(value["record_json"]); qa=json.loads(value["evidence_json"])
        require(record.state is BuildState.ACCEPTED and qa["qa-step"]["pass"] and qa["qa-stl"]["pass"] and qa["qa-step"]["semantic_mapping_pass"],"COMPONENT_REVIEW","Independent topology/dimensions/reimport/semantic QA required before review")
        revision=self.coordinator.decode(source) if current else None
        if revision:
            require(record.snapshot==revision.snapshot and record.feature_graph==revision.graph and record.request==revision.request,"COMPONENT_REVIEW","Native candidate must bind exact captured originals")
        return job,source,record,qa

    @staticmethod
    def selections(record,qa):
        selections=[]
        for part in qa["qa-step"]["parts"]:
            for label,entities in sorted(part["semantic_entities"].items()):
                selections.append(NamedSelection(part["part_id"]+":"+label,record.artifacts[0].geometry_revision_id,next(p["feature_id"] for p in qa["worker_observations"]["parts"] if p["part_id"]==part["part_id"]),tuple(entities),1.,MappingStatus.EXACT))
        return tuple(selections)

    @staticmethod
    def interfaces(record,qa):
        """Match explicit channel-wall/fluid witnesses, not arbitrary proximity ties."""
        parts={p["part_id"]:p for p in qa["qa-step"]["parts"]}; result=[]
        for name,metal in parts.items():
            if metal["role"]!="metal": continue
            for label,left in metal["semantic_entities"].items():
                if not label.startswith("coolant-"): continue
                channel,surface=label.split(".",1); fluid=parts.get(name+".fluid-"+channel.removeprefix("coolant-"))
                if fluid is None: continue
                right_label="fluid."+surface; right=fluid["semantic_entities"].get(right_label,[])
                witnesses_left={f["entity_ref"]:f for f in metal["face_witnesses"]}; witnesses_right={f["entity_ref"]:f for f in fluid["face_witnesses"]}
                pairs=[]; used=set(); limits=metal["limits"]
                for entity in left:
                    face=witnesses_left[entity]
                    matches=[key for key in right if abs(witnesses_right[key]["area_m2"]-face["area_m2"])/face["area_m2"]<=limits["semantic_relative_area"]
                             and np.linalg.norm(np.array(witnesses_right[key]["centroid_m"])-face["centroid_m"])<=limits["semantic_centroid_m"]]
                    require(len(matches)==1 and matches[0] not in used,"AMBIGUOUS_INTERFACE","Coolant/metal interface must pair every exact revision face uniquely; no assumed remapping")
                    used.add(matches[0]); pairs.append(entity+":"+matches[0])
                require(len(used)==len(right) and bool(pairs),"UNRESOLVED_INTERFACE","Missing actual coolant/metal interface counterparts")
                result.append(ComponentInterface(name+":"+label,name+":"+label,fluid["part_id"]+":"+right_label,tuple(pairs)))
        return tuple(result)

    def context(self,actor,project,job_id):
        job,source,record,qa=self.candidate(actor,project,job_id,current=False)
        selections=self.selections(record,qa)
        return {"ok":True,"job_id":job.job_id,"job_head":asdict(job.head),"model_commit_id":json.loads(source.payload)["model_commit_id"],"reviewer_is_builder":actor.user_id==job.creator_user_id,
                "artifact_sha256":{b.name:b.content_hash for b in job.blobs},"named_selections":[json.loads(s.to_json()) for s in selections],"interfaces":[json.loads(i.to_json()) for i in self.interfaces(record,qa)],
                "parts":[{"part_id":p["part_id"],"role":p["role"],"volume_m3":p["volume_m3"],"centroid_m":p["centroid_m"],"surface_area_m2":p["surface_area_m2"],"bounds_m":p["bounds_m"]} for p in qa["qa-step"]["parts"]],
                "required_checks":sorted(CHECKS),"scope":"Actual revision-bound metrology and boundary mapping; review declaration is not a certified material/contact/physics model or manufacturing acceptance"}

    def review(self,actor,project,job_id,command,*,command_hash):
        required={"decision","intended_use","qualification_source","rationale","limitations","checks","artifact_sha256","material_regions","mesh_constraints","expected_job","operation_id"}
        if type(command) is not dict or set(command)!=required: raise InvalidRecord("Exact explicit independent review, material/mesh context and artifact/job identities required")
        prior=self.repository.resolve_command(actor,project,operation_id=command["operation_id"],command_hash=command_hash)
        if prior is not None: return prior
        actor.require(write=True); job,source,record,qa=self.candidate(actor,project,job_id)
        if actor.user_id==job.creator_user_id: raise AccessDenied("Independent review requires another active authorized project engineer, not this build creator; do not invent a reviewer")
        require(command["decision"] in {"ACCEPT","REJECT"} and command["intended_use"]=="GEOMETRY_ANALYSIS_PREPARATION","COMPONENT_REVIEW","Explicit geometry-analysis preparation decision required; no manufacturing/hardware release")
        for key in ("qualification_source","rationale","limitations"):
            require(type(command[key]) is str and 0<len(command[key].strip())<=4096,"COMPONENT_REVIEW","Explicit bounded reviewer qualification/applicability, rationale and limitations required")
        require(type(command["checks"]) is dict and set(command["checks"])==CHECKS and all(type(v) is bool for v in command["checks"].values()),"COMPONENT_REVIEW","All independent-review checks must be explicitly declared")
        require(command["decision"]!="ACCEPT" or all(command["checks"].values()),"COMPONENT_REVIEW","Unresolved/failed checks cannot produce accepted publication")
        head=command["expected_job"]
        require(type(head) is dict and set(head)=={"version","content_hash"},"COMPONENT_REVIEW","Exact expected job version/hash required")
        if Head(head["version"],head["content_hash"])!=job.head: raise HeadConflict(job.head)
        expected={b.name:b.content_hash for b in job.blobs}
        require(command["artifact_sha256"]==expected and set(expected)=={"source.brep","export.step","export.stl"},"COMPONENT_REVIEW","Review must bind every exact original source/exchange hash")
        for name,checksum in expected.items(): require(sha256(self.jobs.blob(actor,project,job_id,name)).hexdigest()==checksum,"COMPONENT_INTEGRITY","Review requires actual retained bytes, not claimed checksums")
        require(type(command["material_regions"]) is list and 0<len(command["material_regions"])<=24 and all(type(v) is dict and set(v)=={"part_id","kind","material_name","source"} for v in command["material_regions"]),"HANDOFF_MATERIAL","Bounded explicit material-region fields required; no client-supplied contract metadata")
        materials=tuple(ComponentMaterialRegion(**v) for v in command["material_regions"])
        roles={p["part_id"]:p["role"] for p in qa["qa-step"]["parts"]}
        require(len(materials)==len(roles) and {m.part_id:m.kind for m in materials}==roles,"HANDOFF_MATERIAL","Every exact metal/fluid body must have one declared material/source; no omitted/duplicate/extra regions")
        require(type(command["mesh_constraints"]) is dict and set(command["mesh_constraints"])=={"maximum_edge_m","minimum_feature_m","cells_across_feature","curvature_tolerance_m","maximum_cells","source"},"HANDOFF_MESH","Exact explicit mesh-intent fields required; no posted generated mesh or solver authority")
        constraints=ComponentMeshConstraints(**command["mesh_constraints"])
        selections=self.selections(record,qa); interfaces=self.interfaces(record,qa)
        object_id=str(uuid5(UUID(project),actor.user_id+":component-review:"+command["operation_id"]))
        published=None
        if command["decision"]=="ACCEPT":
            human=[]
            for i,artifact in enumerate(record.artifacts):
                checks=tuple(GeometryCheck(key,True,None,None,"1",("review-"+object_id,)) for key in sorted(CHECKS))
                human.append(GeometryValidationReport("human-review-"+object_id+"-"+str(i),artifact.artifact_id,checks,"r07.geometry-analysis-review.v1",actor.user_id,Disposition.ACCEPTED))
            references=tuple(r.report_id for r in (*record.reports,*human))
            event=GeometryBuildEvent(record.job_id,len(record.events),datetime.now(timezone.utc).isoformat(),BuildState.PUBLISHED,"independent_analysis_review",None,None,"Independently attested geometry-analysis preparation only; not manufacturing/physical certification",references,tuple(a.artifact_id for a in record.artifacts),record.request.correlation_id)
            published=replace(record,events=(*record.events,event),reports=(*record.reports,*human),named_selections=selections).to_json()
        value={"command":command,"reviewer_user_id":actor.user_id,"build_creator_user_id":job.creator_user_id,"job_id":job.job_id,"build_source_commit_id":source.commit_id,"model_commit_id":json.loads(source.payload)["model_commit_id"],"published_record_json":published,"source_record_json":record.to_json(),"named_selections_json":[s.to_json() for s in selections],"interfaces_json":[i.to_json() for i in interfaces],"material_regions_json":[r.to_json() for r in materials],"mesh_constraints_json":constraints.to_json(),"method_sources":methods(),"engineering_acceptance":"ACCEPTED_FOR_GEOMETRY_ANALYSIS_PREPARATION" if published else "REJECTED","physical_validation":"NOT_PERFORMED","manufacturing_acceptance":"NOT_PERFORMED","qualification_status":"REVIEWER_DECLARED_NOT_EXTERNALLY_CREDENTIAL_VERIFIED"}
        return self.repository.save_snapshot(actor,project,domain=REVIEW_DOMAIN,object_id=object_id,input_revision=source.input_revision,payload=RecordPayload.from_mapping(value,REVIEW_SCHEMA,source_namespace=record.snapshot.project_id),expected=Head.absent(),operation_id=command["operation_id"],command_hash=command_hash,dependencies=(Dependency("component-candidate",source.commit_id,job.job_id),),purpose="create")

    def current(self,actor,source):
        value=json.loads(source.payload)
        return self.repository.dependencies_current(actor,source.project_id,source.commit_id) and value["method_sources"]==methods() and self.coordinator.current(actor,self.repository.resolve_snapshot(actor,source.project_id,value["build_source_commit_id"]))

    def handoff(self,actor,project,review_commit,*,operation_id,command_hash):
        prior=self.repository.resolve_command(actor,project,operation_id=operation_id,command_hash=command_hash)
        if prior is not None: return prior
        review=self.repository.resolve_snapshot(actor,project,review_commit)
        require(review.domain==REVIEW_DOMAIN and review.schema_id==REVIEW_SCHEMA and self.current(actor,review),"STALE_REVIEW","Exact current independent analysis review required; edits/remap proposals cannot inherit acceptance")
        value=json.loads(review.payload)
        require(value["published_record_json"] is not None,"REVIEW_REJECTED","Rejected/unreviewed geometry cannot enter study setup")
        job,build,original,_qa=self.candidate(actor,project,value["job_id"])
        record=GeometryBuildRecord.from_json(value["published_record_json"])
        require(record.state is BuildState.PUBLISHED and record.snapshot==original.snapshot and record.feature_graph==original.feature_graph,"HANDOFF_SOURCE","Published review must bind the exact original source revision")
        step=next(a for a in record.artifacts if a.output_format.value=="step")
        raw=self.jobs.blob(actor,project,job.job_id,"export.step")
        require(sha256(raw).hexdigest()==step.sha256,"HANDOFF_INTEGRITY","Actual handed-off STEP bytes must match accepted artifact")
        handoff=ComponentHandoff(step,job.job_id,build.commit_id,review.commit_id,review.head.content_hash,tuple(NamedSelection.from_json(s) for s in value["named_selections_json"]),tuple(ComponentMaterialRegion.from_json(s) for s in value["material_regions_json"]),record.snapshot.frames,tuple(ComponentInterface.from_json(s) for s in value["interfaces_json"]),ComponentMeshConstraints.from_json(value["mesh_constraints_json"]),step.sha256)
        setup=ComponentStudySetup(handoff)
        object_id=str(uuid5(UUID(project),actor.user_id+":component-study:"+operation_id))
        payload={"setup_json":setup.to_json(),"review_commit_id":review.commit_id,"job_id":job.job_id,"build_source_commit_id":build.commit_id,"model_commit_id":value["model_commit_id"],"method_sources":methods(),"scope":"Reviewed geometry study preparation only; volume mesh/material properties/BC physics and engine CFD/FEA are separate R09 work; sphere runner refuses these components"}
        return self.repository.save_snapshot(actor,project,domain=STUDY_DOMAIN,object_id=object_id,input_revision=build.input_revision,payload=RecordPayload.from_mapping(payload,STUDY_SCHEMA,source_namespace=record.snapshot.project_id),expected=Head.absent(),operation_id=operation_id,command_hash=command_hash,dependencies=(Dependency("independent-review",review.commit_id),Dependency("component-candidate",build.commit_id,job.job_id)),purpose="create")

    def remap_proposal(self,actor,project,review_commit,new_job):
        old=self.repository.resolve_snapshot(actor,project,review_commit)
        require(old.domain==REVIEW_DOMAIN,"REMAP_SOURCE","Exact original review source required")
        _,_,record,qa=self.candidate(actor,project,new_job)
        current={s.semantic_id:s for s in self.selections(record,qa)}; prior=json.loads(old.payload)
        original=GeometryBuildRecord.from_json(prior["source_record_json"])
        old_fingerprints=dict(original.feature_graph.fingerprints(original.snapshot)); new_fingerprints=dict(record.feature_graph.fingerprints(record.snapshot))
        proposals=[]
        for encoded in prior["named_selections_json"]:
            source=NamedSelection.from_json(encoded); target=current.get(source.semantic_id)
            if target is None:
                proposal=source.for_revision(record.artifacts[0].geometry_revision_id)
            else:
                confidence=1. if old_fingerprints.get(source.feature_ref)==new_fingerprints.get(target.feature_ref) else .5
                proposal=replace(target,mapping_status=MappingStatus.REMAPPED,remap_confidence=confidence)
            proposals.append(json.loads(proposal.to_json()))
        return {"ok":True,"persisted":False,"status":"PROPOSAL_REQUIRES_NEW_INDEPENDENT_REVIEW","named_selections":proposals,"confidence_meaning":"Heuristic source-fingerprint equality (1) or same semantic label (0.5), not probability or engineering acceptance","handoff_eligible":False}
