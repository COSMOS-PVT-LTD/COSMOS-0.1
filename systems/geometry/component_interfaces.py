"""Actual saved-solid openings and conservative distributor/plate mating checks.

This is geometric connectivity inspection, not a pressure solution or seal test.
Unbuilt collector/pipe/port geometry is reported missing, never invented.
"""
from __future__ import annotations

import math
from hashlib import sha256
from pathlib import Path

import numpy as np

from core.quantity import Quantity
from core.unit import SI
from physics.fluids.sector_passage import annular_sector_section
from systems.contracts.geometry._wire import require
from systems.geometry.component_joints import inspect_joints
from systems.projects.authority import StoreUnavailable


def methods():
    root=Path(__file__).resolve().parents[2]
    names=("systems/geometry/component_interfaces.py","systems/geometry/component_circuits.py","systems/geometry/component_joints.py","api/component_interfaces.py","physics/fluids/sector_passage.py")
    return {name:sha256((root/name).read_bytes()).hexdigest() for name in names}


LOADED=methods()


def inspect_interfaces(plan,tolerance_m):
    require(type(tolerance_m) in {int,float} and math.isfinite(tolerance_m) and 0<tolerance_m<=.001,
            "INTERFACE_TOLERANCE","Explicit positive numerical connection tolerance <=1mm required; not a leak/assembly allowance")
    if methods()!=LOADED:raise StoreUnavailable("Interface analysis methods changed; restart before claiming new provenance")
    ports=[]; mechanical=[]; pipe_paths=[]
    def port(part,key,fluid,kind,x,center,normal,shape,area,bore_area):
        rotation,translation=plan.placement(part.frame_id)
        if shape["kind"]=="ANNULAR_SECTOR":
            shape={**shape,"boundary_corners_m":[(rotation@np.array([x,r*math.cos(a),r*math.sin(a)])+translation).tolist()
                for r in (shape["inner_radius_m"],shape["outer_radius_m"])
                for a in (shape["phase_rad"],shape["phase_rad"]+shape["width_rad"])]}
        ports.append({"id":part.part_id+"."+key,"part_id":part.part_id,"feature_id":part.feature_id,
                      "fluid":fluid,"kind":kind,"position_m":(rotation@np.r_[x,center]+translation).tolist(),
                      "normal":(rotation@np.array([normal,0.,0.] if np.isscalar(normal) else normal)).tolist(),"aperture":shape,
                      "axial_aperture_area_m2":area,"bore_normal_area_m2":bore_area})
    for part in plan.parts:
        if part.pipe:
            pipe=part.pipe; area=math.pi*pipe.bore_radius**2
            end=np.array([pipe.length,0.,0.]) if pipe.bend_radius is None else np.array([
                pipe.bend_radius*math.sin(pipe.angle_rad),pipe.bend_radius*(1-math.cos(pipe.angle_rad)),0.])
            normal=(1.,0.,0.) if pipe.bend_radius is None else (math.cos(pipe.angle_rad),math.sin(pipe.angle_rad),0.)
            aperture={"kind":"CIRCLE","minor_radius_m":pipe.bore_radius,"major_radius_m":pipe.bore_radius}
            port(part,"end-a","UNASSIGNED","PIPE_END",0.,(0.,0.),(-1.,0.,0.),aperture,area,area)
            port(part,"end-b","UNASSIGNED","PIPE_END",end[0],end[1:],normal,aperture,area,area)
            pipe_paths.append({"part_id":part.part_id,"end_a":part.part_id+".end-a","end_b":part.part_id+".end-b",
                "centerline_length_m":pipe.length if pipe.bend_radius is None else pipe.bend_radius*pipe.angle_rad,
                "bore_radius_m":pipe.bore_radius,"outer_radius_m":pipe.outer_radius,
                "bend_radius_m":pipe.bend_radius,"angle_rad":pipe.angle_rad,
                "fluid_assignment":"NOT_ASSIGNED","loss_coefficient":"NOT_CALCULATED","pressure_rating":"NOT_ASSESSED"})
        for i,hole in enumerate(part.holes):
            if hole.axial_range is not None:
                fluid,end=hole.role.split("-")
                x=hole.axial_range[0] if end=="inlet" else hole.axial_range[1]
                area=math.pi*hole.radius**2
                port(part,"port-"+str(i),"COOLANT_UNASSIGNED" if fluid=="coolant" else fluid,"COOLING_HEADER_SUPPLY" if fluid=="coolant" else "MANIFOLD_"+end.upper(),x,hole.center_yz,-1 if end=="inlet" else 1,
                     {"kind":"CIRCLE","minor_radius_m":hole.radius,"major_radius_m":hole.radius},area,area)
            elif hole.role in {"fuel","oxidizer"}:
                slope=np.array(hole.slope_yz); major=hole.radius*math.sqrt(1+float(slope@slope))
                for end,x,normal in (("INLET",part.profile[0][0],-1),("DISCHARGE",part.profile[-1][0],1)):
                    port(part,"port-"+str(i)+"-"+end.lower(),hole.role,"INJECTOR_"+end,x,np.array(hole.center_yz)+x*slope,normal,
                         {"kind":"ELLIPSE","minor_radius_m":hole.radius,"major_radius_m":major},math.pi*hole.radius*major,math.pi*hole.radius**2)
        for i,cavity in enumerate(part.cavities):
            if not cavity.open_passage or cavity.sector is None:continue
            x,low,high=cavity.profile[-1];phase,width=cavity.sector;angle=phase+width/2
            sec=annular_sector_section(Quantity(low,SI.get("m")),Quantity(high,SI.get("m")),Quantity(width,SI.get("rad")))
            center=sec.centroid_radius_m*np.array([math.cos(angle),math.sin(angle)])
            port(part,"header-channel-"+str(i),"COOLANT_UNASSIGNED","COOLING_HEADER_CHANNEL",x,center,1,
                {"kind":"ANNULAR_SECTOR","inner_radius_m":low,"outer_radius_m":high,"width_rad":width,"phase_rad":phase},sec.area_m2,None)
        if part.cooling is not None:
            c=part.cooling
            for i in range(c.count):
                angle=c.phase_rad+2*math.pi*i/c.count+c.width_rad/2
                for kind,(x,inner,_),normal in (("UPPER_COLLECTOR_CONNECTION",part.profile[0],-1),("NOZZLE_INLET_CONNECTION",part.profile[-1],1)):
                    low,high=inner+c.hot_ligament,inner+c.hot_ligament+c.depth
                    sec=annular_sector_section(Quantity(low,SI.get("m")),Quantity(high,SI.get("m")),Quantity(c.width_rad,SI.get("rad")))
                    center=sec.centroid_radius_m*np.array([math.cos(angle),math.sin(angle)])
                    port(part,"channel-"+str(i)+"-"+kind.lower(),"COOLANT_UNASSIGNED",kind,x,center,normal,
                         {"kind":"ANNULAR_SECTOR","inner_radius_m":low,"outer_radius_m":high,"width_rad":c.width_rad,"phase_rad":angle-c.width_rad/2},sec.area_m2,None)
        if any(h.role=="fastener-clearance" for h in part.holes):
            mechanical.append({"part_id":part.part_id,"bolt_count":sum(h.role=="fastener-clearance" for h in part.holes),"bore_radius_m":part.profile[0][1],
                               "outer_radius_m":part.profile[0][2],"joint_status":"SEAL_PRELOAD_MATERIAL_ATTACHMENT_NOT_ASSESSED"})
    matches=[]; used=set()
    for head in [p for p in ports if p["kind"]=="MANIFOLD_OUTLET"]:
        candidates=[]
        for plate in [p for p in ports if p["kind"]=="INJECTOR_INLET" and p["fluid"]==head["fluid"]]:
            distance=float(np.linalg.norm(np.array(head["position_m"])-plate["position_m"]))
            opposed=float(np.dot(head["normal"],plate["normal"]))
            # Only concentric circular cap bore contained by an inclined-bore
            # ellipse is supported here. Equal-area arbitrary shapes are not.
            if (distance<=tolerance_m and opposed<=-1+1e-12
                and abs(head["aperture"]["minor_radius_m"]-plate["aperture"]["minor_radius_m"])<=1e-12):
                candidates.append((plate,distance))
        require(len(candidates)<=1,"INTERFACE_AMBIGUOUS","One manifold outlet has multiple coincident same-fluid plate openings")
        if not candidates:continue
        plate,distance=candidates[0]
        require(plate["id"] not in used,"INTERFACE_AMBIGUOUS","Multiple manifold outlets compete for one injector inlet")
        used.update((head["id"],plate["id"]))
        matches.append({"from":head["id"],"to":plate["id"],"fluid":head["fluid"],"center_mismatch_m":distance,
                        "opening":"CIRCULAR_BORE_TO_CONTAINING_INCLINED_ELLIPSE","common_area_m2":head["bore_normal_area_m2"],
                        "status":"GEOMETRIC_CONNECTION_ONLY","turn_entrance_loss":"NOT_CALCULATED","seal_status":"NOT_ASSESSED"})
    for header in [p for p in ports if p["kind"]=="COOLING_HEADER_CHANNEL"]:
        candidates=[]
        for channel in [p for p in ports if p["kind"] in {"UPPER_COLLECTOR_CONNECTION","NOZZLE_INLET_CONNECTION"}]:
            if float(np.dot(header["normal"],channel["normal"]))>-1+1e-12:continue
            a=np.array(header["aperture"]["boundary_corners_m"]);b=np.array(channel["aperture"]["boundary_corners_m"])
            distance=float(np.linalg.norm(np.array(header["position_m"])-channel["position_m"]))
            mismatch=float(np.min(np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2),axis=1).max())
            if (distance<=tolerance_m and mismatch<=tolerance_m
                and abs(header["axial_aperture_area_m2"]-channel["axial_aperture_area_m2"])<=1e-12*channel["axial_aperture_area_m2"]):
                candidates.append((channel,distance,mismatch))
        require(len(candidates)<=1,"INTERFACE_AMBIGUOUS","Header channel port matches multiple passage ends")
        if not candidates:continue
        channel,distance,mismatch=candidates[0]
        require(channel["id"] not in used,"INTERFACE_AMBIGUOUS","More than one header competes for the same passage end")
        used.update((header["id"],channel["id"]))
        matches.append({"from":header["id"],"to":channel["id"],"fluid":"COOLANT_UNASSIGNED","opening":"MATCHING_WORLD_ANNULAR_SECTORS",
            "center_mismatch_m":distance,"boundary_corner_mismatch_m":mismatch,"common_area_m2":header["axial_aperture_area_m2"],
            "status":"GEOMETRIC_CONNECTION_ONLY","header_distribution_loss":"NOT_CALCULATED","seal_status":"NOT_ASSESSED"})
    for pipe_end in [p for p in ports if p["kind"]=="PIPE_END"]:
        if pipe_end["id"] in used:continue
        candidates=[]
        for other in ports:
            if (other["id"] in used or other["part_id"]==pipe_end["part_id"]
                or other["kind"] not in {"PIPE_END","MANIFOLD_INLET","COOLING_HEADER_SUPPLY"}):continue
            distance=float(np.linalg.norm(np.array(pipe_end["position_m"])-other["position_m"]))
            opposed=float(np.dot(pipe_end["normal"],other["normal"]))
            if (distance<=tolerance_m and opposed<=-1+1e-12 and other["aperture"]["kind"]=="CIRCLE"
                and abs(pipe_end["aperture"]["minor_radius_m"]-other["aperture"]["minor_radius_m"])<=1e-12):
                candidates.append((other,distance))
        require(len(candidates)<=1,"INTERFACE_AMBIGUOUS","Pipe end matches multiple actual circular openings")
        if not candidates:continue
        other,distance=candidates[0];used.update((pipe_end["id"],other["id"]))
        matches.append({"from":pipe_end["id"],"to":other["id"],"fluid":"UNASSIGNED_GEOMETRIC_ROUTE",
            "opening":"MATCHING_PIPE_CIRCLES","center_mismatch_m":distance,"common_area_m2":pipe_end["bore_normal_area_m2"],
            "status":"GEOMETRIC_CONNECTION_ONLY","joint_and_bend_loss":"NOT_CALCULATED","seal_status":"NOT_ASSESSED"})
    missing=[{"port_id":p["id"],"kind":p["kind"],"fluid":p["fluid"]} for p in ports if p["id"] not in used and p["kind"]!="INJECTOR_DISCHARGE"]
    disconnected_kinds={p["kind"] for p in ports if p["id"] not in used}
    required=[label for kind,label in (("NOZZLE_INLET_CONNECTION","Nozzle-end inlet plenum and supply connection"),
              ("UPPER_COLLECTOR_CONNECTION","Upper collector below chamber flange and outlet connection")) if kind in disconnected_kinds]
    if "COOLING_HEADER_SUPPLY" in disconnected_kinds:required.append("Supply/return pipes attached to the cooling header circular ports")
    if any(p["kind"]=="MANIFOLD_INLET" and p["fluid"]=="fuel" and p["id"] not in used for p in ports):required.append("Fuel return pipe to injector manifold")
    if any(p["kind"]=="MANIFOLD_INLET" and p["fluid"]=="oxidizer" and p["id"] not in used for p in ports):required.append("Direct LOX supply pipe")
    required.append("Sealed/qualified pressure joints")
    report={"schema":"cosmos.component-interface-inspection.v1","source_graph_id":plan.graph.graph_id,"ports":ports,"matches":matches,"unconnected_ports":missing,
            "flange_candidates":mechanical,"pipe_paths":pipe_paths,"tolerance_m":tolerance_m,"geometry_route_complete":False,
            "required_unimplemented_geometry":required,
            "injector_discharge_to_chamber":"NOT_SPATIALLY_ASSESSED","pressure_closure":"NOT_CALCULATED",
            "physical_validation":"NOT_PERFORMED","fluid_route_assignment":"NOT_ASSESSED","method_sources":dict(LOADED),
            "scope":"Actual saved openings and supported distributor/plate geometry mating only; not a sealed or pressure/thermal-closed engine"}
    report["mechanical_joints"]=inspect_joints(plan,report,tolerance_m)
    report["injector_discharge_to_chamber"]=report["mechanical_joints"]["injector_discharge_status"]
    return report
