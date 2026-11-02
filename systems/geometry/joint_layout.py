"""Explicit isolated matching bolt cuts; never a service-load sizing rule."""
import math
from copy import deepcopy

import numpy as np

from systems.contracts.geometry._wire import digest, identifier, require
from systems.geometry.component_model import compile_model


def append_header_bolts(specification,inspection,proposal):
    require(inspection.get("source_graph_id")=="components-"+digest(specification),"JOINT_SOURCE","Exact current opening inspection required")
    require(type(proposal) is dict and set(proposal)=={"scope","source","header_part_id","collar_part_id","feature_id"}
        and proposal["scope"]=="ISOLATED_GEOMETRY_HYPOTHESIS_NOT_INSTALLED_ENGINE_INPUTS"
        and type(proposal["source"]) is str and 0<len(proposal["source"])<=2048,
        "JOINT_PROPOSAL","Explicit isolated matching-hole proposal required; no assumed bolt material, thread or preload")
    identifier(proposal["feature_id"],"new bolt feature")
    plan=compile_model(specification,"engine-component-joint-preparation","isolated-replay","2026-10-21T00:00:00Z")
    parts={p.part_id:p for p in plan.parts}
    require(proposal["header_part_id"] in parts and proposal["collar_part_id"] in parts,"JOINT_SOURCE","Actual exported header and collar required")
    header,collar=parts[proposal["header_part_id"]],parts[proposal["collar_part_id"]]
    source=next(f for f in specification["features"] if f["id"]==header.feature_id)
    require(source["operation"]=="manifold.cooling_annular" and header.part_id==header.feature_id,
        "JOINT_LAYOUT_UNSUPPORTED","Direct unmodified cooling header required; no guessed operand through placements")
    contacts=[c for j in inspection["mechanical_joints"]["header_joints"] if j["header_part_id"]==header.part_id
        for c in j["contacts"] if c["part_id"]==collar.part_id]
    require(len(contacts)==1 and contacts[0]["mating_bolt_bores"]>=3 and contacts[0]["header_bolt_bores"]==0,
        "JOINT_LAYOUT_UNSUPPORTED","One actual coaxial opposed collar face with a clearance pattern required")
    require(collar.holes and all(h.role=="fastener-clearance" and h.slope_yz==(0.,0.) and h.axial_range is None for h in collar.holes),
        "JOINT_LAYOUT_UNSUPPORTED","Only a complete uniform axial clearance-hole collar is supported")
    rh,th=plan.placement(header.frame_id);rc,tc=plan.placement(collar.frame_id)
    centers=[(rh.T@(rc@np.r_[collar.profile[0][0],h.center_yz]+tc-th))[1:] for h in collar.holes]
    ring=float(np.linalg.norm(centers[0]));phase=math.atan2(centers[0][1],centers[0][0]);n=len(centers);hole=collar.holes[0].radius
    require(all(h.radius==hole and abs(float(np.linalg.norm(c))-ring)<=1e-12 for h,c in zip(collar.holes,centers,strict=True))
        and all(np.linalg.norm(c-ring*np.array([math.cos(phase+2*math.pi*i/n),math.sin(phase+2*math.pi*i/n)]))<=1e-12
                for i,c in enumerate(centers)),"JOINT_LAYOUT_UNSUPPORTED","Exact uniform matching pattern required; no best-fit bolt circle or inferred reducer")
    result=deepcopy(specification);result["source"]=proposal["source"];name=proposal["feature_id"]
    require(name not in {f["id"] for f in result["features"]},"JOINT_PROPOSAL","New feature ID must be unused")
    q=lambda v,u="m":{"value":v,"unit":u}
    result["features"].append({"id":name,"operation":"interface.bolt_pattern","frame":header.frame_id,
        "depends_on":[header.feature_id],"parameters":{"bolt_circle_radius":q(ring),"bolt_hole_radius":q(hole),"count":q(n,"1"),"phase":q(phase,"rad")}})
    result["outputs"]=[name if value==header.feature_id else value for value in result["outputs"]]
    # Compile before allowing persistence; collision/ligament rules are the
    # shared feature contract, not bypassed by a proposal helper.
    compile_model(result,"engine-component-joint-preparation","isolated-replay","2026-10-21T00:00:00Z")
    return result
