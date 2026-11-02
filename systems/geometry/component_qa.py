"""Component-specific software QA, independent formula/reimport, not physical review."""

from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass, replace

import numpy as np

from infrastructure.geometry import WorkerCommand
from systems.contracts.geometry._wire import require
from systems.geometry.component_model import POLICY, scalar
from systems.geometry.component_reference import ComponentReference, PartReference
from systems.geometry.qa import audit_mesh, read_stl
from systems.geometry.service import GeometryBuildService


@dataclass(frozen=True)
class ComponentQALimits:
    relative_volume: float
    centroid_m: float
    implicit_residual_m: float
    reverse_distance_m: float
    semantic_relative_area: float
    semantic_centroid_m: float
    source: str

    @classmethod
    def from_spec(cls,value):
        names=("relative_volume","centroid","implicit_residual","reverse_distance","semantic_relative_area","semantic_centroid")
        require(type(value) is dict and set(value)==set(names)|{"source"} and type(value["source"]) is str and 0<len(value["source"].strip())<=2048,"COMPONENT_QA","Explicit sourced volume/centroid/CSG-residual/reverse-distance/semantic-area/semantic-centroid ceilings required")
        parsed=[scalar(value[name],"1" if name in {"relative_volume","semantic_relative_area"} else "m") for name in names]
        require(all(0<v<.1 for v in parsed),"COMPONENT_QA","Finite positive predeclared SI QA limits below the software envelope required")
        return cls(*parsed,value["source"])


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


class ComponentBuildService(GeometryBuildService):
    policy_id=POLICY
    reviewer_id="r07-component-independent-software-audit"
    acceptance_stage="component_software_qa"
    acceptance_message="Component candidates pass declared software QA; human intended-use acceptance/physical validation NOT_PERFORMED"

    def __init__(self,backend,candidate_root,*,step_reader,limits):
        super().__init__(backend,candidate_root,step_reader=step_reader); self.limits=limits

    def validate_policy(self,snapshot,reference):
        require(isinstance(reference,ComponentReference) and snapshot.project_id.startswith("engine-component-") and reference.plan.snapshot==snapshot,"COMPONENT_POLICY","Exact component snapshot/reference policy required; no fixture/nozzle policy bypass")

    def prepare_audit(self,output,reference):
        require(isinstance(reference,ComponentReference),"COMPONENT_POLICY","Component formula reference required")
        actual=output.metrics.get("parts")
        require(output.metrics.get("kernel_unit")=="mm" and output.metrics.get("input_unit")=="m" and type(actual) is list and len(actual)==len(reference.plan.parts),"COMPONENT_RESPONSE","Exact component part/units inventory required")
        start=0
        for part,raw in zip(reference.plan.parts,actual,strict=True):
            require(type(raw) is dict and set(raw)=={"part_id","feature_id","frame_id","role","triangle_start","triangle_count","volume_m3","centroid_m","bounds_m","faces"}
                    and (raw["part_id"],raw["feature_id"],raw["frame_id"],raw["role"])==(part.part_id,part.feature_id,part.frame_id,part.role)
                    and type(raw["triangle_start"]) is int and raw["triangle_start"]==start and type(raw["triangle_count"]) is int and raw["triangle_count"]>0,"COMPONENT_RESPONSE","Part IDs/roles/frame and contiguous actual triangle ranges must bind the exact admitted graph")
            start+=raw["triangle_count"]
            require(finite(raw["volume_m3"]) and raw["volume_m3"]>0 and all(type(raw[k]) is list and len(raw[k])==n and all(finite(v) for v in raw[k]) for k,n in (("centroid_m",3),("bounds_m",6)))
                    and type(raw["faces"]) is list and 0<len(raw["faces"])<=5000,"COMPONENT_RESPONSE","Finite positive native dimensions and bounded face inventory required")
            for face in raw["faces"]:
                require(type(face) is dict and set(face)=={"native_entity","semantic","area_m2","centroid_m"} and finite(face["area_m2"]) and face["area_m2"]>0
                        and type(face["native_entity"]) is str and type(face["semantic"]) is str and len(face["semantic"])<=128
                        and type(face["centroid_m"]) is list and len(face["centroid_m"])==3 and all(finite(v) for v in face["centroid_m"]),"COMPONENT_RESPONSE","Exact finite native face witnesses required")
        require(start==output.metrics.get("triangle_count") and start<=200000,"COMPONENT_RESPONSE","Part ranges must cover all actual exported triangles exactly once")
        return replace(reference,worker_parts=tuple(actual))

    def audit_candidate(self,path,format_,reference,request,job,token):
        require(isinstance(reference,ComponentReference) and bool(reference.worker_parts),"COMPONENT_POLICY","Verified component inventory required")
        limits=self.limits; results=[]; deadline=time.monotonic()+120
        def budget():
            require(not token.is_set(),"CANCELLED","Component QA cancelled; no candidate acceptance")
            require(time.monotonic()<=deadline,"QA_TIMEOUT","Component QA exceeded120-second host budget")
        if format_=="stl":
            raw,triangles,_=read_stl(path,allow_bad_normals=True)
            require(len(triangles)==sum(p["triangle_count"] for p in reference.worker_parts),"COMPONENT_RANGE","Actual STL differs from complete part-range manifest")
            for i,(part,actual) in enumerate(zip(reference.plan.parts,reference.worker_parts,strict=True)):
                budget(); start,count=actual["triangle_start"],actual["triangle_count"]
                scratch=path.parent/("audit-part-"+str(i)+".stl")
                require(not scratch.exists(),"ARTIFACT_EXISTS","Refuse independent audit scratch overwrite")
                try:
                    with scratch.open("xb") as stream: stream.write(raw[:80]+count.to_bytes(4,"little")+raw[84+50*start:84+50*(start+count)])
                    qa=audit_mesh(scratch,PartReference(reference.plan,part),voxel_m=None,export_tolerance_m=request.export_tolerance_m,euler_characteristic=part.euler,
                                  volume_ceiling=limits.relative_volume,centroid_ceiling_m=limits.centroid_m,distance_ceiling_m=limits.reverse_distance_m,
                                  forward_ceiling_m=limits.implicit_residual_m,check_budget=budget)
                finally:
                    scratch.unlink(missing_ok=True)
                qa.update(part_id=part.part_id,role=part.role,forward_metric="absolute signed CSG constraint residual; not general Euclidean distance",reverse_metric="reference samples to actual planar STL triangles",expected_bounds_m=PartReference(reference.plan,part).bounds_m.tolist())
                qa["bidirectional_sampling_scope"]="All exported vertices/face centroids to labelled analytic CSG residual; explicit retained-station/midpoint/port/channel/azimuth samples to actual triangles. Not certified Hausdorff or self-intersection proof."
                results.append(qa)
            return {"pass":all(r["pass"] for r in results),"topology_pass":all(r["topology_pass"] for r in results),"dimensions_pass":all(r["dimensions_pass"] for r in results),"parts":results,"part_range_map":"Every triangle covered once; each named part independently checked; STL has no native CAD hierarchy","physical_validation_claimed":False}
        text=path.read_text()
        require(text.startswith("ISO-10303-21;") and text.rstrip().endswith("END-ISO-10303-21;") and "MANIFOLD_SOLID_BREP" in text and "FACETED_BREP" not in text
                and re.search(r"LENGTH_UNIT\(\).*?SI_UNIT\(\$\s*,\s*\.METRE\.\)",text,re.DOTALL) is not None and ".MILLI." not in text,"INVALID_STEP","Complete analytic metre STEP assembly required")
        expected=[]
        for part in reference.plan.parts:
            ref=PartReference(reference.plan,part)
            expected.append({"id":part.part_id,"volume_m3":ref.volume_m3,"centroid_m":ref.centroid_m.tolist(),"bounds_m":ref.bounds_m.tolist(),"samples_m":ref.surface_samples().tolist()})
        command=WorkerCommand((*self.step_reader.argv,str(path)),self.step_reader.environment)
        payload={"parts":expected,"body_relative_volume":limits.relative_volume,"body_centroid_m":limits.centroid_m,"reverse_distance_m":limits.reverse_distance_m}
        run=self.backend.supervisor.submit("qa-"+job,command,json.dumps(payload,allow_nan=False).encode(),path.parent,cancellation=token).result()
        require(run.code=="OK",run.code,"Independent component STEP reimport failed; no accepted geometry")
        data=json.loads(run.stdout)
        require(type(data) is dict and set(data)=={"reader","version","units","import_unit","bbox_deflection_m","parts"} and data["reader"]=="gmsh" and data["version"]=="4.15.0" and data["units"]=="m" and data["import_unit"]=="mm"
                and finite(data["bbox_deflection_m"]) and 0<data["bbox_deflection_m"]<=limits.reverse_distance_m/10 and type(data["parts"]) is list and len(data["parts"])==len(expected),"COMPONENT_REIMPORT","Exact finite pinned independent reimport envelope required")
        for part,native,actual in zip(reference.plan.parts,reference.worker_parts,data["parts"],strict=True):
            budget(); ref=PartReference(reference.plan,part)
            require(type(actual) is dict and set(actual)=={"part_id","volume_m3","centroid_m","bounds_m","faces","surface_samples_m","reverse_distances_m","unmatched_reverse_samples","nonmanifold_edges","orientation_errors","euler_characteristic","triangle_count"} and actual["part_id"]==part.part_id,"COMPONENT_REIMPORT","Imported part identity/fields differ")
            require(finite(actual["volume_m3"]) and actual["volume_m3"]>0 and all(type(actual[k]) is list and len(actual[k])==n and all(finite(v) for v in actual[k]) for k,n in (("centroid_m",3),("bounds_m",6)))
                    and type(actual["surface_samples_m"]) is list and 0<len(actual["surface_samples_m"])<=30000 and all(type(row) is list and len(row)==3 and all(finite(v) for v in row) for row in actual["surface_samples_m"]),"COMPONENT_REIMPORT","Finite correctly shaped imported SI measurements required")
            reverse=actual["reverse_distances_m"]
            require(type(reverse) is list and len(reverse)==len(ref.surface_samples()) and actual["unmatched_reverse_samples"]==0 and all(finite(v) and v>=0 for v in reverse),"COMPONENT_REVERSE_UNAVAILABLE","Every declared source sample needs a finite trimmed imported-face projection; unmatched samples cannot pass")
            for key in ("unmatched_reverse_samples","nonmanifold_edges","orientation_errors","euler_characteristic","triangle_count"):
                require(type(actual[key]) is int and -512<=actual[key]<=200000,"COMPONENT_REIMPORT","Bounded integer topology observations required")
            volume=abs(actual["volume_m3"]-ref.volume_m3)/ref.volume_m3; centroid=float(np.linalg.norm(np.array(actual["centroid_m"])-ref.centroid_m)); bounds=float(np.max(np.abs(np.array(actual["bounds_m"])-ref.bounds_m)))
            forward=np.abs(ref.sdf(actual["surface_samples_m"]))
            faces=actual["faces"]
            require(type(faces) is list and len(faces)==len(native["faces"]),"COMPONENT_REIMPORT","Reimport face hierarchy differs from original construction witnesses")
            semantics={}; used=set(); mapping=True
            for face in faces:
                require(type(face) is dict and set(face)=={"entity_ref","area_m2","centroid_m","carrier"} and type(face["entity_ref"]) is str and len(face["entity_ref"])<=128 and finite(face["area_m2"]) and face["area_m2"]>0 and type(face["centroid_m"]) is list and len(face["centroid_m"])==3 and all(finite(v) for v in face["centroid_m"]),"COMPONENT_REIMPORT","Finite actual imported face witnesses required")
                matches=[f for f in native["faces"] if abs(f["area_m2"]-face["area_m2"])/f["area_m2"]<=limits.semantic_relative_area and np.linalg.norm(np.array(f["centroid_m"])-face["centroid_m"])<=limits.semantic_centroid_m]
                if len(matches)!=1 or matches[0]["native_entity"] in used or matches[0]["semantic"] in {"UNRESOLVED","AMBIGUOUS"}:
                    mapping=False; continue
                used.add(matches[0]["native_entity"]); semantics.setdefault(matches[0]["semantic"],[]).append(face["entity_ref"])
            topology=actual["nonmanifold_edges"]==actual["orientation_errors"]==0 and actual["euler_characteristic"]==part.euler and actual["triangle_count"]>0
            dimensions=volume<=limits.relative_volume and centroid<=limits.centroid_m and bounds<=limits.reverse_distance_m and float(forward.max())<=limits.implicit_residual_m and max(reverse)<=limits.reverse_distance_m
            results.append({"part_id":part.part_id,"role":part.role,"pass":bool(topology and dimensions and mapping),"topology_pass":bool(topology),"dimensions_pass":bool(dimensions),"semantic_mapping_pass":mapping,"semantic_entities":semantics,
                            "volume_m3":actual["volume_m3"],"relative_volume_error":volume,"centroid_m":actual["centroid_m"],"centroid_error_m":centroid,"bounds_m":actual["bounds_m"],"bounds_error_m":bounds,"surface_area_m2":sum(f["area_m2"] for f in faces),
                            "implicit_residual_max_m":float(forward.max()),"implicit_residual_p95_m":float(np.percentile(forward,95)),"reverse_max_m":max(reverse),"reverse_p95_m":float(np.percentile(reverse,95)),"reverse_samples":len(reverse),"actual_surface_nodes":len(forward),"face_count":len(faces),"euler_characteristic":actual["euler_characteristic"],"expected_euler_characteristic":part.euler,
                            "face_witnesses":faces,"limits":{"relative_volume":limits.relative_volume,"centroid_m":limits.centroid_m,"implicit_residual_m":limits.implicit_residual_m,"reverse_distance_m":limits.reverse_distance_m,"semantic_relative_area":limits.semantic_relative_area,"semantic_centroid_m":limits.semantic_centroid_m}})
        return {"pass":all(r["pass"] for r in results),"topology_pass":all(r["topology_pass"] for r in results),"dimensions_pass":all(r["dimensions_pass"] for r in results),"semantic_mapping_pass":all(r["semantic_mapping_pass"] for r in results),"parts":results,"reader":"gmsh-4.15.0","reader_kernel_independence":False,"independence_scope":"Separate process/API/STEP import plus kernel-independent integrals and signed analytic CSG constraints; Gmsh/OCP share OCCT","sampling_scope":"Actual imported nodes to explicitly labelled CSG residual, reference station/midpoint/port/sector samples to actual trimmed imported faces; not certified Hausdorff","physical_validation_claimed":False,"reader_observed_rss_bytes":run.maximum_rss_bytes}
