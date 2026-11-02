"""Managed reversible component models and exact-source durable builds, not new IO."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid5

from core.serialization import canonical_json_dumps
from plugins.geometry.component_protocol import validate
from systems.contracts.geometry import (
    DesignSnapshot,
    GeometryBuildRequest,
    GeometryFeatureGraph,
    OutputFormat,
    Representation,
    SourceReference,
)
from systems.geometry.authority import ManagedGeometry
from systems.geometry.component_model import (
    SCHEMA,
    VERSION,
    compile_model,
    profile_parameters,
    scalar,
)
from systems.geometry.component_qa import ComponentQALimits
from systems.geometry.component_reference import ComponentReference
from systems.geometry.engine_builds import EngineBuildCoordinator
from systems.geometry.workbench import Revision
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    Head,
    HeadConflict,
    InvalidRecord,
    RecordNotFound,
    StoreUnavailable,
)
from systems.projects.propulsion_authority import decode_design

DOMAIN="engine-component-model"
BUILD_DOMAIN="engine-component-build"
BUILD_SCHEMA="cosmos.engine-component-build-input.v1"


def injector_dimensions(design):
    """Read exactly retained CURRENT liquid-orifice dimensions, never resize."""
    result=design.workflow.current_result("injector")
    from systems.contracts.results import ResultStatus
    if result is None or design.workflow.graph.get("injector").status is not ResultStatus.CURRENT:
        raise InvalidRecord("Hydraulic bipropellant CAD requires a CURRENT injector result")
    if result.model_id!="PHYS-INJ.liquid_orifice":
        raise InvalidRecord("Unsupported injector source model; no assumed diameter mapping")
    values={}
    counts=[]
    for name in ("fuel","oxidizer"):
        row=result.outputs.get(name)
        if type(row) is not dict or type(row.get("hole_count")) is not int or type(row.get("diameter_m")) not in (int,float):
            raise InvalidRecord("Injector must retain exact SI diameter and integer port count")
        diameter=row["diameter_m"]
        if not math.isfinite(diameter) or diameter<=0:
            raise InvalidRecord("Invalid retained hydraulic port diameter")
        counts.append(row["hole_count"])
        values[name+"_hole_radius"]={"value":diameter/2,"unit":"m"}
    if counts[0]!=counts[1]:
        raise InvalidRecord("One fuel/oxidizer pair per doublet requires equal retained counts")
    values["count"]={"value":counts[0],"unit":"1"}
    # Use the frozen Core storage contract, not an independent geometry precision
    # or engineering rounding policy. This must be stable after save/reload.
    return json.loads(canonical_json_dumps(values)),result.result_id


def validate_injector_binding(design,specification):
    if "constraints" in specification:
        from systems.geometry.driving_constraints import resolve
        specification=resolve(specification)["specification"]
    for feature in specification.get("features",[]):
        if feature.get("operation") not in {"injector.biprop_doublet", "injector.biprop_radial_doublet", "manifold.dual_annular"}: continue
        dimensions,_=injector_dimensions(design)
        actual=feature.get("parameters",{})
        for name,wanted in dimensions.items():
            if type(actual.get(name)) is not dict or canonical_json_dumps(actual[name])!=canonical_json_dumps(wanted):
                raise InvalidRecord("Bipropellant CAD "+name+" must equal its exact CURRENT hydraulic source; no silent rounding or independent resizing")
    radial=[f for f in specification.get("features",[]) if f.get("operation")=="injector.biprop_radial_doublet"]
    manifolds=[f for f in specification.get("features",[]) if f.get("operation")=="manifold.dual_annular"]
    if manifolds and not radial and any(f.get("operation")=="injector.biprop_doublet" for f in specification.get("features",[])):
        raise InvalidRecord("Tangential fuel/oxidizer pairs share a radial distance; isolated annular plenums cannot silently claim that feed mapping")
    for head in manifolds:
        if not radial: continue  # Standalone head, no claim that another plate is connected.
        if not any(all(canonical_json_dumps(head["parameters"].get(key))==canonical_json_dumps(plate["parameters"].get(key))
                       for key in ("count","ring_radius","separation","phase","fuel_hole_radius","oxidizer_hole_radius")) for plate in radial):
            raise InvalidRecord("Annular manifold outlets and a radial plate in the same assembly must have exactly matching layout; tangential pairs are not an annular feed mapping")


def methods():
    root=Path(__file__).resolve().parents[2]
    files={"systems/geometry/component_authority.py","systems/geometry/component_model.py","systems/geometry/component_reference.py","systems/geometry/component_qa.py","systems/geometry/component_workspace.py","systems/geometry/component_review.py","systems/geometry/component_sections.py",
           "plugins/geometry/component_protocol.py","plugins/geometry/component_adapter.py","plugins/geometry/workers/component_worker.py","plugins/geometry/workers/component_step_reader.py","plugins/geometry/workers/stl_encoding.py","plugins/geometry/adapters.py","plugins/geometry/protocol.py",
           "systems/geometry/authority.py","systems/geometry/service.py","systems/geometry/qa.py","systems/geometry/engine_builds.py","api/component_geometry.py","api/nozzle_geometry.py","infrastructure/persistence/durable_jobs.py","infrastructure/geometry/supervisor.py","simulation/component_handoff.py"}
    files.add("systems/geometry/driving_constraints.py")
    files.add("api/occt_component_runtime.py")
    files.update(str(p.relative_to(root)) for directory in ("core","systems/contracts/geometry") for p in (root/directory).rglob("*.py"))
    return {name:sha256((root/name).read_bytes()).hexdigest() for name in sorted(files)}


class ComponentModels:
    def __init__(self,repository):
        self.repository=repository; self.loaded_methods=methods()

    def current(self,actor,source):
        value=json.loads(source.payload)
        return (source.domain==DOMAIN and source.schema_id==SCHEMA and self.repository.dependencies_current(actor,source.project_id,source.commit_id)
                and self.repository.get_snapshot(actor,source.project_id,domain=DOMAIN,object_id=source.object_id).commit_id==source.commit_id
                and value["method_sources"]==self.loaded_methods==methods())

    def envelope(self,actor,source):
        if source.domain!=DOMAIN or source.schema_id!=SCHEMA: raise InvalidRecord("Exact component-model domain/schema required")
        value=json.loads(source.payload)
        plan=from_source(source)
        current=self.current(actor,source)
        return {"ok":True,"authority":{"project_id":source.project_id,"object_id":source.object_id,"commit_id":source.commit_id,"head":asdict(source.head),"input_revision":source.input_revision},
                "source_canonical_json":source.payload.decode(),"model":value,"upstream_current":current,"usable_current_model":current,"feature_order":list(plan.graph.topological_order()),
                "parts":[{"part_id":p.part_id,"feature_id":p.feature_id,"frame_id":p.frame_id,"role":p.role,"expected_euler":p.euler} for p in plan.parts],"physical_validation":"NOT_PERFORMED","engineering_acceptance":"NOT_PERFORMED"}

    def save(self,actor,project,object_id,*,title,baseline_commit,expected_baseline,specification,expected,operation_id,command_hash,origin_commit=None):
        replay=self.repository.resolve_command(actor,project,operation_id=operation_id,command_hash=command_hash)
        if replay is not None: return replay
        actor.require(write=True)
        if methods()!=self.loaded_methods: raise StoreUnavailable("Component methods changed after loading; restart before validating new edits")
        if type(title) is not str or not 0<len(title.strip())<=240: raise InvalidRecord("Explicit bounded model title required")
        baseline=self.repository.resolve_snapshot(actor,project,baseline_commit)
        decode_design(baseline)
        current=self.repository.get_snapshot(actor,project,domain=baseline.domain,object_id=baseline.object_id)
        if baseline.head!=expected_baseline or baseline.commit_id!=current.commit_id: raise HeadConflict(current.head)
        prior=None if expected==Head.absent() else self.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=object_id)
        revision=0 if prior is None else prior.input_revision+1
        if prior is not None and prior.head!=expected: raise HeadConflict(prior.head)
        if origin_commit:
            origin=self.repository.resolve_snapshot(actor,project,origin_commit)
            if origin.domain!=DOMAIN or origin.object_id!=object_id: raise RecordNotFound("Restore origin must be an exact authorized revision of this component model")
            original=json.loads(origin.payload)
            specification=original["specification"]; title=original["title"]
            if baseline.commit_id!=original["baseline_commit_id"]: raise InvalidRecord("Restore cannot silently rebind its original baseline; explicitly edit/reconcile after restoration")
        if "constraints" in specification:
            from systems.geometry.driving_constraints import resolve
            specification=resolve(specification)["specification"]
        validate_injector_binding(decode_design(baseline),specification)
        plan=compile_model(specification,"engine-component-"+object_id,"model-"+object_id+"-"+str(revision),datetime.now(timezone.utc).isoformat(),sources=(SourceReference("engine-baseline","propulsion/"+baseline.object_id+"/"+baseline.head.content_hash+".json",baseline.head.content_hash),))
        value={"title":title,"specification":specification,"snapshot_json":plan.snapshot.to_json(),"graph_json":plan.graph.to_json(),"baseline_commit_id":baseline.commit_id,"baseline_canonical_json":baseline.payload.decode(),"method_sources":self.loaded_methods,
               "origin_commit_id":origin_commit,"source_mode":"EXPLICIT_SOURCED_CAD_GEOMETRY_WITH_ENGINE_BASELINE_PROVENANCE","scope":"Parametric component geometry; no inferred atomization/thermal sizing/physical acceptance"}
        return self.repository.save_snapshot(actor,project,domain=DOMAIN,object_id=object_id,input_revision=revision,payload=RecordPayload.from_mapping(value,SCHEMA,source_namespace=plan.snapshot.project_id),
                expected=expected,operation_id=operation_id,command_hash=command_hash,dependencies=(Dependency("engine-baseline",baseline.commit_id),),purpose="activate" if origin_commit else "create" if prior is None else "save",source_commit_id=origin_commit)

    def preview(self,actor,project,specification,*,object_id=None):
        self.repository.get_project(actor,project)
        if methods()!=self.loaded_methods: raise StoreUnavailable("Component compiler changed; restart and reconcile")
        namespace="engine-component-"+(object_id or "unsaved-preview")
        plan=compile_model(specification,namespace,"unsaved-preview",datetime.now(timezone.utc).isoformat())
        result={"ok":True,"persisted":False,"snapshot_json":plan.snapshot.to_json(),"graph_json":plan.graph.to_json(),"order":list(plan.graph.topological_order()),"parts":[{"part_id":p.part_id,"role":p.role,"frame_id":p.frame_id} for p in plan.parts],"impact":None}
        if object_id:
            source=self.repository.get_snapshot(actor,project,domain=DOMAIN,object_id=object_id); prior=from_source(source)
            result["impact"]=asdict(prior.graph.impact(prior.snapshot,plan.snapshot))
        return result

    def seed(self,actor,project,baseline_commit,settings):
        """Read exact saved chamber/nozzle and explicit missing CAD dimensions; no sizing."""
        if type(settings) is not dict or set(settings)!={"wall_thickness","convergent_length","throat_land_length","source_tolerance","export_tolerance","source"}: raise InvalidRecord("Supply every missing CAD wall/convergent/land/tolerance/source explicitly")
        source=self.repository.resolve_snapshot(actor,project,baseline_commit); design=decode_design(source)
        if source.commit_id!=self.repository.get_snapshot(actor,project,domain=source.domain,object_id=source.object_id).commit_id: raise InvalidRecord("Seed requires the exact current engine baseline")
        from systems.contracts.results import ResultStatus
        chamber=design.workflow.current_result("chamber"); nozzle=design.workflow.current_result("nozzle")
        if chamber is None or nozzle is None or design.workflow.graph.get("chamber").status is not ResultStatus.CURRENT or design.workflow.graph.get("nozzle").status is not ResultStatus.CURRENT: raise InvalidRecord("Calculate/save CURRENT chamber sizing and an actual divergent contour first; area-only/no stale-source substitution")
        c=chamber.outputs; stations=nozzle.outputs.get("stations")
        if not isinstance(stations,list) or not 2<=len(stations)<=125: raise InvalidRecord("Exact source mapping allows2–125 divergent stations plus four upstream stations; no implicit downsampling")
        diameter=c.get("chamber_diameter"); cylinder=c.get("chamber_length")
        if type(diameter) is not dict or type(cylinder) is not dict or diameter.get("unit")!="m" or cylinder.get("unit")!="m": raise InvalidRecord("Exact SI chamber diameter/length outputs required; no legacy-key/unit inference")
        radius=float(diameter["value"])/2; length=float(cylinder["value"])
        wall,convergent,land=(scalar(settings[k],"m") for k in ("wall_thickness","convergent_length","throat_land_length"))
        if min(wall,convergent,land)<=0 or radius<=stations[0]["radius_m"]: raise InvalidRecord("Positive sourced wall/convergent/land and chamber radius above throat required")
        throat=float(stations[0]["radius_m"])
        rows=[(-length-convergent-land,radius,radius+wall),(-convergent-land,radius,radius+wall),(-land,throat,throat+wall),(0.,throat,throat+wall)]
        rows.extend((float(r["x_m"]),float(r["radius_m"]),float(r["radius_m"])+wall) for r in stations[1:])
        spec={"schema":SCHEMA,"source":settings["source"],"source_tolerance":settings["source_tolerance"],"export_tolerance":settings["export_tolerance"],
              "frames":[{"id":"world","parent":None,"origin":[{"value":0.,"unit":"m"}]*3,"rotation":[1.,0.,0.,0.,1.,0.,0.,0.,1.]}],
              "features":[{"id":"thrust-chamber","operation":"profile.wall","frame":"world","depends_on":[],"parameters":profile_parameters(rows)}],"outputs":["thrust-chamber"]}
        self.preview(actor,project,spec)
        return {"ok":True,"specification":spec,"baseline_commit_id":source.commit_id,"baseline_head":asdict(source.head),"source_mode":"EXACT_SAVED_CHAMBER_AND_DIVERGENT_CONTOUR_PLUS_EXPLICIT_MISSING_CAD_DIMENSIONS",
                "warnings":["Saved chamber length is its existing cylindrical L* sizing approximation, not a new volume closure including the convergent.","Radial wall intent is not normal thickness or structural qualification.","Sector cooling geometry is not silently coupled to the older rectangular-channel thermal model."]}

    def seed_injector(self,actor,project,baseline_commit,settings):
        layout={"radius","thickness","ring_radius","phase","separation","angle"}
        if type(settings) is not dict or set(settings)!=layout|{"source","source_tolerance","export_tolerance"}:
            raise InvalidRecord("Supply exact explicit plate/layout/tolerance/source fields; hydraulic radii/count are read from the baseline")
        baseline=self.repository.resolve_snapshot(actor,project,baseline_commit)
        design=decode_design(baseline)
        if baseline.commit_id!=self.repository.get_snapshot(actor,project,domain=baseline.domain,object_id=baseline.object_id).commit_id:
            raise InvalidRecord("Injector seed requires the exact current baseline")
        dimensions,result_id=injector_dimensions(design)
        parameters={**{name:settings[name] for name in layout},**dimensions}
        spec={"schema":SCHEMA,"source":settings["source"],"source_tolerance":settings["source_tolerance"],"export_tolerance":settings["export_tolerance"],
              "frames":[{"id":"world","parent":None,"origin":[{"value":0.,"unit":"m"}]*3,"rotation":[1.,0.,0.,0.,1.,0.,0.,0.,1.]}],
              "features":[{"id":"injector-biprop","operation":"injector.biprop_doublet","frame":"world","depends_on":[],"parameters":parameters}],"outputs":["injector-biprop"]}
        self.preview(actor,project,spec)
        return {"ok":True,"specification":spec,"baseline_commit_id":baseline.commit_id,"baseline_head":asdict(baseline.head),
                "injector_result_id":result_id,"source_mode":"EXACT_CURRENT_HYDRAULIC_PORT_RADII_COUNTS_PLUS_EXPLICIT_PLATE_LAYOUT",
                "warnings":["Cold liquid-orifice sizing only; regenerative return fuel requires re-evaluated properties and hydraulics.",
                            "Fuel/oxidizer bore roles do not create feed manifolds, seals, a sealed injector/chamber joint or atomization/stability qualification.",
                            "Plate/layout dimensions remain explicit preliminary geometry intent, not structural or hot-fire approval."]}


def from_source(source):
    from systems.geometry.component_model import from_contracts
    value=json.loads(source.payload)
    return from_contracts(DesignSnapshot.from_json(value["snapshot_json"]),GeometryFeatureGraph.from_json(value["graph_json"]))


class ComponentCoordinator(EngineBuildCoordinator):
    def __init__(self,repository,jobs,factory,resolve_actor,models):
        ManagedGeometry.__init__(self,repository,jobs,dict,resolve_actor)
        self.factory,self.models,self.loaded_methods=factory,models,methods()

    def current(self,actor,source):
        value=json.loads(source.payload)
        return self.repository.dependencies_current(actor,source.project_id,source.commit_id) and value["method_sources"]==self.loaded_methods==methods() and self.models.current(actor,self.repository.resolve_snapshot(actor,source.project_id,value["model_commit_id"]))

    def capture(self,actor,project,model_commit,expected,qa_specification,operation_id,command_hash):
        actor.require(write=True)
        operation="component-build-input."+sha256((actor.user_id+operation_id).encode()).hexdigest(); capture_hash=sha256((command_hash+":input").encode()).hexdigest()
        prior=self.repository.resolve_command(actor,project,operation_id=operation,command_hash=capture_hash)
        if prior is not None: return prior
        source=self.repository.resolve_snapshot(actor,project,model_commit)
        if not self.models.current(actor,source): raise InvalidRecord("Build requires exact CURRENT saved component model, engine baseline and methods; preserve/reconcile drafts")
        if source.head!=expected: raise HeadConflict(source.head)
        if methods()!=self.loaded_methods: raise StoreUnavailable("Component build methods changed after loading")
        ComponentQALimits.from_spec(qa_specification)
        plan=from_source(source); values={p.name:p.value_si for p in plan.snapshot.parameters_si}
        object_id=str(uuid5(UUID(project),actor.user_id+":component-build:"+operation_id))
        request=GeometryBuildRequest("request-"+object_id,plan.snapshot.snapshot_id,plan.graph.graph_id,plan.graph.content_sha256,"occt",VERSION,Representation.ANALYTIC_BREP,"none",values["source_tolerance"],values["export_tolerance"],None,(OutputFormat.STEP,OutputFormat.STL),"world","build-"+object_id)
        validate(request,plan.snapshot,plan.graph); workspace=self.factory()
        value={"model_commit_id":source.commit_id,"model_sha256":source.head.content_hash,"model_canonical_json":source.payload.decode(),"snapshot_json":plan.snapshot.to_json(),"graph_json":plan.graph.to_json(),"request_json":request.to_json(),"qa_specification":qa_specification,
               "method_sources":self.loaded_methods,"runtime_hashes":workspace.runtime_hashes,"command":{"model_commit_id":source.commit_id,"expected_model":asdict(expected),"qa_specification":qa_specification,"output_formats":["step","stl"],"operation_id":operation_id},"scope":"Source-bound component software candidate; independent engineering review/handoff separate"}
        return self.repository.save_snapshot(actor,project,domain=BUILD_DOMAIN,object_id=object_id,input_revision=source.input_revision,payload=RecordPayload.from_mapping(value,BUILD_SCHEMA,source_namespace=plan.snapshot.project_id),expected=Head.absent(),operation_id=operation,command_hash=capture_hash,dependencies=(Dependency("component-model",source.commit_id),))

    def decode(self,source):
        if source.domain!=BUILD_DOMAIN or source.schema_id!=BUILD_SCHEMA or not source.source_namespace.startswith("engine-component-"): raise InvalidRecord("Exact component build domain/schema/namespace required")
        value=json.loads(source.payload); snapshot=DesignSnapshot.from_json(value["snapshot_json"]); graph=GeometryFeatureGraph.from_json(value["graph_json"]); request=GeometryBuildRequest.from_json(value["request_json"])
        validate(request,snapshot,graph)
        if value["method_sources"]!=self.loaded_methods or methods()!=self.loaded_methods: raise StoreUnavailable("Original component methods differ; capture a new explicit command after reconciliation")
        return Revision(value,snapshot,graph,request)

    def select_service(self,revision):
        workspace=self.factory()
        if workspace.runtime_hashes!=revision.settings["runtime_hashes"]: raise StoreUnavailable("Captured component runtime changed; no silent retry")
        return workspace.service_for(ComponentQALimits.from_spec(revision.settings["qa_specification"]))

    def reference(self,revision):
        return ComponentReference(validate(revision.request,revision.snapshot,revision.graph))
