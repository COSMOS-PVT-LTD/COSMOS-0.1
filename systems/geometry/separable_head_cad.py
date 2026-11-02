"""Build the approved isolated revised concept from exact retained source.

No target-thrust scaling, owner installation or pressure/thermal qualification.
The explicit coolant-domain export selection changes representation only; every
metal cooling passage remains a real cut. Grooves are optional explicit study
geometry, never automatic seal selection.
"""
import math
from copy import deepcopy

import numpy as np

from systems.contracts.geometry._wire import identifier, require
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.separable_head_layout import prepare_layout


def prepare_cad(specification,inspection,layout_proposal,cad_proposal):
    layout=prepare_layout(specification,inspection,layout_proposal)
    fields={"scope","source","suppressed_mount_feature","export_coolant_domains","pipe_wall_m","bend_radius_m",
        "stub_length_m","return_outer_center_radius_m","fuel_supply_length_m","oxidizer_supply_length_m","grooves"}
    require(type(cad_proposal) is dict and set(cad_proposal)==fields
        and cad_proposal["scope"]=="ISOLATED_REVISED_CAD_STUDY_NOT_OWNER_INPUTS_OR_HARDWARE_ACCEPTANCE"
        and type(cad_proposal["source"]) is str and 0<len(cad_proposal["source"])<=2048
        and type(cad_proposal["export_coolant_domains"]) is bool
        and type(cad_proposal["grooves"]) is list and len(cad_proposal["grooves"])<=5,
        "REVISED_CAD_PROPOSAL","Exact explicit revised-concept CAD proposal required")
    for key in ("pipe_wall_m","bend_radius_m","stub_length_m","return_outer_center_radius_m","fuel_supply_length_m","oxidizer_supply_length_m"):
        require(type(cad_proposal[key]) in {int,float} and math.isfinite(cad_proposal[key]) and cad_proposal[key]>0,
            "REVISED_CAD_PROPOSAL","Explicit finite positive routing dimensions required")
    result=deepcopy(specification);features={f["id"]:f for f in result["features"]};q=lambda v,u="m":{"value":float(v),"unit":u}
    def compile(value):return compile_model(value,"engine-component-revised-concept-preparation","isolated-cold-replay","2026-10-21T00:00:00Z")
    original=compile(specification);parts={p.part_id:p for p in original.parts}
    header,plate,head,chamber=[parts[layout_proposal[k]] for k in ("header_part_id","injector_part_id","head_part_id","chamber_part_id")]
    def root(feature,operation):
        chain=[];current=features[feature]
        while current["operation"] in {"interface.bolt_pattern","interface.face_groove","interface.face_grooves"}:
            require(len(current["depends_on"])==1,"REVISED_CAD_SOURCE","One explicit modifier operand required")
            chain.append(current["id"]);current=features[current["depends_on"][0]]
        require(current["operation"]==operation,"REVISED_CAD_SOURCE","Exact supported source feature family required")
        return current,chain
    upper,consumed=root(header.feature_id,"manifold.cooling_annular")
    injector,plate_modifiers=root(plate.feature_id,"injector.biprop_radial_doublet")
    distributor,head_modifiers=root(head.feature_id,"manifold.dual_annular")
    require(not plate_modifiers and not head_modifiers,"REVISED_CAD_SOURCE","This proposal starts from the retained unmodified injector/head, not reinterpreted seal geometry")
    cooled=features[chamber.feature_id]
    require(cooled["operation"]=="cooling.axial_sector" and len(cooled["depends_on"])==1,"REVISED_CAD_SOURCE","Direct source axial cooling feature required")
    wall=features[cooled["depends_on"][0]]
    require(wall["operation"]=="profile.wall" and wall["frame"]=="world","REVISED_CAD_SOURCE","Direct unplaced source chamber profile required")
    wall["parameters"]["x0"]=q(layout["proposed_main_chamber_start_x_m"])
    cooled["parameters"]["fluid_domains"]=q(int(cad_proposal["export_coolant_domains"]),"1")
    upper["operation"]="manifold.cooling_front_supply"
    upper["parameters"].update(outer_radius=q(layout["mount_outer_radius_m"]),plenum_outer=q(layout_proposal["collector_plenum_outer_radius_m"]))
    frame=next(f for f in result["frames"] if f["id"]==upper["frame"])
    require(frame["parent"]=="world","REVISED_CAD_SOURCE","Direct world-child upper header frame required")
    frame["origin"][0]=q(layout["proposed_collector_x_m"][0])
    for feature in (injector,distributor):feature["parameters"]["radius"]=q(layout["mount_outer_radius_m"])
    suppressed=cad_proposal["suppressed_mount_feature"]
    require(suppressed in features and features[suppressed]["operation"]=="interface.bolted_flange",
        "REVISED_CAD_SOURCE","Explicit obsolete separate collar feature required; its function is replaced by the enlarged mounting stack")
    pipes={f["id"] for f in result["features"] if f["operation"] in {"pipe.circular","pipe.elbow"}}
    remove={suppressed,*pipes,*consumed}
    require(not any(set(f["depends_on"])&remove for f in result["features"] if f["id"] not in remove),
        "REVISED_CAD_SOURCE","Cannot suppress a feature consumed by another retained component")
    result["features"]=[f for f in result["features"] if f["id"] not in remove]
    result["outputs"]=[v for v in result["outputs"] if v not in remove]
    result["source"]=cad_proposal["source"]
    aliases={}
    for parent,name in ((upper,"collector-mount-bolts"),(injector,"injector-mount-bolts"),(distributor,"head-mount-bolts")):
        require(name not in features,"REVISED_CAD_SOURCE","Reserved revised feature name already exists")
        result["features"].append({"id":name,"operation":"interface.bolt_pattern","frame":parent["frame"],"depends_on":[parent["id"]],
            "parameters":{"bolt_circle_radius":q(layout["bolt_circle_radius_m"]),"bolt_hole_radius":q(layout["bolt_hole_radius_m"]),
                "count":q(layout["bolt_count"],"1"),"phase":q(0.,"rad")}})
        result["outputs"]=[name if v==parent["id"] else v for v in result["outputs"]]
        if parent is upper and name not in result["outputs"]:result["outputs"].append(name)  # Its old modifier may have been suppressed.
        aliases[parent["id"]]=name
    groups={};reserved={f["id"] for f in result["features"]}
    for groove in cad_proposal["grooves"]:
        require(type(groove) is dict and set(groove)=={"id","part_feature_id","inner_radius_m","outer_radius_m","depth_m","face"}
            and type(groove["id"]) is str and type(groove["part_feature_id"]) is str and groove["part_feature_id"] in aliases
            and all(type(groove[k]) in {int,float} and math.isfinite(groove[k]) for k in ("inner_radius_m","outer_radius_m","depth_m","face")),
            "REVISED_CAD_GROOVE","Explicit groove source feature and finite SI dimensions required")
        name=groove["id"];identifier(name,"groove id")
        require(len(name)<=48 and name not in reserved,"REVISED_CAD_GROOVE","Unique bounded explicit groove ID required")
        reserved.add(name);groups.setdefault(groove["part_feature_id"],[]).append(groove)
    for parent,grooves in groups.items():
        operand=aliases[parent];name=grooves[-1]["id"];multiple=len(grooves)>1
        parameters={"count":q(len(grooves),"1")} if multiple else {}
        for index,groove in enumerate(grooves):
            suffix=str(index) if multiple else ""
            parameters.update({"inner_radius"+suffix:q(groove["inner_radius_m"]),"outer_radius"+suffix:q(groove["outer_radius_m"]),
                "depth"+suffix:q(groove["depth_m"]),"face"+suffix:q(groove["face"],"1")})
        result["features"].append({"id":name,"operation":"interface.face_grooves" if multiple else "interface.face_groove",
            "frame":features[parent]["frame"],"depends_on":[operand],"parameters":parameters})
        result["outputs"]=[name if v==operand else v for v in result["outputs"]];aliases[parent]=name
    # Drop only now-unused coordinate frames in this new isolated proposal.
    needed={"world",*[f["frame"] for f in result["features"]]};frames={f["id"]:f for f in result["frames"]}
    for name in tuple(needed):
        while frames[name]["parent"] is not None:name=frames[name]["parent"];needed.add(name)
    result["frames"]=[f for f in result["frames"] if f["id"] in needed]
    current=compile(result);read=inspect_interfaces(current,1e-6)
    def port(part_id,kind,fluid=None):
        found=[p for p in read["ports"] if p["part_id"]==part_id and p["kind"]==kind and (fluid is None or p["fluid"]==fluid)]
        require(len(found)==1,"REVISED_CAD_SOURCE","One exact supported opening required")
        return found[0]
    a=port(aliases[upper["id"]],"COOLING_HEADER_SUPPLY");b=port(aliases[distributor["id"]],"MANIFOLD_INLET","fuel")
    lower_ports=[p for p in read["ports"] if p["kind"]=="COOLING_HEADER_SUPPLY" and p["part_id"]!=a["part_id"]]
    require(len(lower_ports)==1,"REVISED_CAD_SOURCE","One separate actual nozzle-end supply header required")
    lower=lower_ports[0]
    ox=port(aliases[distributor["id"]],"MANIFOLD_INLET","oxidizer")
    require(np.allclose(a["normal"],[1,0,0],rtol=0,atol=1e-12) and np.allclose(b["normal"],[-1,0,0],rtol=0,atol=1e-12)
        and a["aperture"]["minor_radius_m"]==b["aperture"]["minor_radius_m"],"REVISED_CAD_ROUTING","Explicit +X collector / -X equal-bore fuel head openings required")
    pa,pb=np.array(a["position_m"]),np.array(b["position_m"])
    require(abs(pa[2]-pb[2])<1e-12 and abs(pa[2])<1e-12,"REVISED_CAD_ROUTING","This bounded route requires the source meridional XY plane")
    radius=cad_proposal["bend_radius_m"];stub=cad_proposal["stub_length_m"];height=cad_proposal["return_outer_center_radius_m"]
    bore=a["aperture"]["minor_radius_m"];outer=bore+cad_proposal["pipe_wall_m"]
    margin=4*max(specification["source_tolerance"]["value"],specification["export_tolerance"]["value"])
    spans=(height-pa[1]-2*radius,pa[0]-pb[0]+2*stub,height-pb[1]-2*radius)
    require(min(spans)>margin and height-outer-layout["mount_outer_radius_m"]>margin
        and pa[1]-outer-chamber.profile[0][2]>margin,"REVISED_CAD_ROUTING","Declared route must clear the enlarged flange and actual chamber with resolved straight spans")
    def append(name,origin,x,y,bore,*,length=None,bend=False):
        require(name not in {f["id"] for f in result["features"]},"REVISED_CAD_ROUTING","Reserved pipe feature already exists")
        result["frames"].append({"id":name,"parent":"world","origin":[q(float(v)) for v in origin],"rotation":np.column_stack((x,y,np.cross(x,y))).flatten().tolist()})
        parameters={"bore_radius":q(bore),"wall_thickness":q(cad_proposal["pipe_wall_m"])}
        parameters.update({"bend_radius":q(radius),"angle":q(math.pi/2,"rad")} if bend else {"length":q(length)})
        result["features"].append({"id":name,"operation":"pipe.elbow" if bend else "pipe.circular","frame":name,"depends_on":[],"parameters":parameters})
        result["outputs"].append(name)
    append("return-collector",pa,[1,0,0],[0,1,0],bore,length=stub)
    append("return-elbow-a",pa+[stub,0,0],[1,0,0],[0,1,0],bore,bend=True)
    point=pa+[stub+radius,radius,0]
    append("return-outward",point,[0,1,0],[-1,0,0],bore,length=spans[0])
    append("return-elbow-b",point+[0,spans[0],0],[0,1,0],[-1,0,0],bore,bend=True)
    point=np.array([pa[0]+stub,height,0.])
    append("return-over-flange",point,[-1,0,0],[0,-1,0],bore,length=spans[1])
    append("return-elbow-c",point+[-spans[1],0,0],[-1,0,0],[0,-1,0],bore,bend=True)
    point=np.array([pb[0]-stub-radius,height-radius,0.])
    append("return-inward",point,[0,-1,0],[1,0,0],bore,length=spans[2])
    append("return-elbow-d",point+[0,-spans[2],0],[0,-1,0],[1,0,0],bore,bend=True)
    append("return-head",pb+[-stub,0,0],[1,0,0],[0,1,0],bore,length=stub)
    append("fuel-supply",np.array(lower["position_m"]),[1,0,0],[0,1,0],lower["aperture"]["minor_radius_m"],length=cad_proposal["fuel_supply_length_m"])
    length=cad_proposal["oxidizer_supply_length_m"]
    append("oxidizer-supply",np.array(ox["position_m"])-[length,0,0],[1,0,0],[0,1,0],ox["aperture"]["minor_radius_m"],length=length)
    compile(result)
    return result,{"fuel_boundary":"fuel-supply.end-b","oxidizer_boundary":"oxidizer-supply.end-a"},layout
