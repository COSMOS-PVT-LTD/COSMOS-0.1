"""Source-bound axial joint geometry, not bolt strength or seal qualification.

The annular lands are conservative full-circumference radial intervals. A
circle/sector opening removes its entire radial envelope from the land list;
isolated pads between holes are not described as a continuous seal land.
Separate bodies are never merged into a purported integral load path.
"""
from __future__ import annotations

import math

import numpy as np

from systems.contracts.geometry._wire import require


def _holes_at_face(part,x):
    result=[]
    for hole in part.holes:
        begin,end=hole.axial_range or (part.profile[0][0],part.profile[-1][0])
        if begin-1e-12<=x<=end+1e-12:
            result.append(hole)
    return result


def _blocked_bands(part,row):
    x,inner,_=row;bands=[]
    for h in _holes_at_face(part,x):
        center=np.array(h.center_yz)+x*np.array(h.slope_yz)
        # Major axis bounds the projected ellipse in every radial direction.
        radius=h.radius*math.sqrt(1+sum(v*v for v in h.slope_yz))
        r=float(np.linalg.norm(center));bands.append((r-radius,r+radius))
    for cavity in part.cavities:
        if cavity.profile[0][0]-1e-12<=x<=cavity.profile[-1][0]+1e-12:
            bands.append((min(r[1] for r in cavity.profile),max(r[2] for r in cavity.profile)))
    if part.cooling:
        c=part.cooling;bands.append((inner+c.hot_ligament,inner+c.hot_ligament+c.depth))
    return bands


def _lands(low,high,bands):
    result=[];cursor=low
    for a,b in sorted(bands):
        if b<=cursor or a>=high:continue
        if a>cursor:result.append((cursor,min(a,high)))
        cursor=max(cursor,b)
    if cursor<high:result.append((cursor,high))
    return [{"inner_radius_m":a,"outer_radius_m":b,"radial_width_m":b-a} for a,b in result if b>a]


def _bolt_faces(plan,part,row):
    rotation,translation=plan.placement(part.frame_id);x=row[0]
    return [{"hole_index":i,"radius_m":h.radius,
             "position_m":(rotation@np.r_[x,h.center_yz]+translation).tolist()}
            for i,h in enumerate(part.holes) if h.role=="fastener-clearance" and h in _holes_at_face(part,x)]


def _injector_contacts(plan,inspection,tolerance_m):
    plates=[p for p in plan.parts if {h.role for h in p.holes}>={"fuel","oxidizer"}
        and all(h.axial_range is None for h in p.holes)]
    walls=[p for p in plan.parts if p.role=="metal" and not p.pipe and not p.sector
        and ((not p.holes and not p.cavities) or any(c.open_passage and c.sector for c in p.cavities))
        and all(row[1]>0 for row in p.profile)]
    result=[]
    for plate in plates:
        rp,tp=plan.placement(plate.frame_id);end=plate.profile[-1]
        center=rp@np.array([end[0],0.,0.])+tp;normal=rp[:,0]
        openings=[p for p in inspection["ports"] if p["part_id"]==plate.part_id and p["kind"]=="INJECTOR_DISCHARGE"]
        candidates=[]
        for wall in walls:
            rw,tw=plan.placement(wall.frame_id);begin=wall.profile[0]
            wall_center=rw@np.array([begin[0],0.,0.])+tw
            mismatch=float(np.linalg.norm(center-wall_center))
            if mismatch>tolerance_m or float(normal@rw[:,0])<1-1e-12:continue
            # A circumscribed circle is a conservative containment proof for
            # each inclined-bore ellipse. No sampled edge can hide a breach.
            margin=min((begin[1]-float(np.linalg.norm(np.array(p["position_m"])-wall_center))
                        -p["aperture"]["major_radius_m"] for p in openings),default=None)
            overlap=max(0.,min(end[2],begin[2])-max(end[1],begin[1]))
            candidates.append({"wall_part_id":wall.part_id,"center_mismatch_m":mismatch,
                "discharge_apertures_proven_inside_gas_bore":bool(margin is not None and margin>=0),
                "conservative_radial_aperture_margin_m":margin,"annular_face_overlap_width_m":overlap,
                "face_attachment_geometry":"ZERO_ANNULAR_FACE_LAND" if overlap==0 else "POTENTIAL_FACE_LAND_NOT_A_SEAL_DESIGN",
                "mechanical_seal_and_attachment":"NOT_DESIGNED"})
        require(len(candidates)<=1,"JOINT_AMBIGUOUS","Injector discharge face matches multiple candidate thrust walls")
        result.append({"injector_part_id":plate.part_id,"discharge_openings":len(openings),"wall_contacts":candidates,
            "discharge_geometry_connected":bool(candidates and candidates[0]["discharge_apertures_proven_inside_gas_bore"]),
            "pressure_boundary_complete":False})
    return result


def inspect_joints(plan,inspection,tolerance_m):
    require(inspection.get("source_graph_id")==plan.graph.graph_id,"JOINT_SOURCE","Joint inspection requires exact saved opening source")
    require(type(tolerance_m) in {int,float} and math.isfinite(tolerance_m) and 0<tolerance_m<=.001,
            "INTERFACE_TOLERANCE","Explicit finite numerical contact tolerance required; not a service gap or leak allowance")
    parts={p.part_id:p for p in plan.parts};ports={p["id"]:p for p in inspection["ports"]};joints=[]
    for header in plan.parts:
        sectors=[c for c in header.cavities if c.open_passage and c.sector is not None]
        if not sectors:continue
        rotation,translation=plan.placement(header.frame_id);row=header.profile[-1]
        center=rotation@np.array([row[0],0.,0.])+translation;normal=rotation[:,0]
        matches=[m for m in inspection["matches"] if m["opening"]=="MATCHING_WORLD_ANNULAR_SECTORS" and ports[m["from"]]["part_id"]==header.part_id]
        channel_parts=sorted({ports[m["to"]]["part_id"] for m in matches})
        contacts=[]
        for other in parts.values():
            if other is header or other.pipe or other.sector or other.role!="metal":continue
            r,t=plan.placement(other.frame_id)
            for end,sign in ((other.profile[0],-1),(other.profile[-1],1)):
                if float(normal@(r[:,0]*sign))>-1+1e-12:continue
                other_center=r@np.array([end[0],0.,0.])+t
                mismatch=float(np.linalg.norm(other_center-center))
                if mismatch>tolerance_m:continue  # Only coaxial opposed axial faces.
                low,high=max(row[1],end[1]),min(row[2],end[2])
                if high<=low:continue
                a,b=_bolt_faces(plan,header,row),_bolt_faces(plan,other,end);paired=[];used=set()
                for first in a:
                    candidates=[second for second in b if abs(first["radius_m"]-second["radius_m"])<=1e-12
                        and np.linalg.norm(np.array(first["position_m"])-second["position_m"])<=tolerance_m]
                    require(len(candidates)<=1,"JOINT_AMBIGUOUS","A fastener axis matches more than one mating clearance bore")
                    if not candidates:continue
                    second=candidates[0];require(second["hole_index"] not in used,"JOINT_AMBIGUOUS","Competing fastener axes")
                    used.add(second["hole_index"]);paired.append({"header_hole_index":first["hole_index"],"mating_hole_index":second["hole_index"],
                        "axis_mismatch_m":float(np.linalg.norm(np.array(first["position_m"])-second["position_m"])),"bore_radius_m":first["radius_m"]})
                contacts.append({"part_id":other.part_id,"center_mismatch_m":mismatch,"overlap_inner_radius_m":low,"overlap_outer_radius_m":high,
                    "continuous_annular_lands_m":_lands(low,high,_blocked_bands(header,row)+_blocked_bands(other,end)),
                    "header_bolt_bores":len(a),"mating_bolt_bores":len(b),"matched_bolt_axes":paired,
                    "bolt_axes_complete":bool(a and b and len(paired)==len(a)==len(b)),
                    "load_path":"NOT_ASSESSED_SEPARATE_BODIES_ARE_NOT_AN_INTEGRAL_FLANGE"})
        header_bolts=_bolt_faces(plan,header,row)
        cavity_clearance=min((math.hypot(*h.center_yz)-h.radius-max(v[2] for v in c.profile)
            for h in header.holes if h.role=="fastener-clearance" for c in header.cavities),default=None)
        joints.append({"header_part_id":header.part_id,"channel_part_ids":channel_parts,
            "channel_openings":len(sectors),"matched_channel_openings":len(matches),
            "all_channel_openings_mated":len(matches)==len(sectors),"position_m":center.tolist(),"normal":normal.tolist(),
            "gas_bore_radius_m":row[1],"gas_to_coolant_radial_land_m":min(c.profile[-1][1] for c in sectors)-row[1],
            "coolant_port_outer_radius_m":max(c.profile[-1][2] for c in sectors),"contacts":contacts,
            "header_bolt_bores":len(header_bolts),"minimum_outer_bolt_to_cavity_radial_ligament_m":cavity_clearance,
            "gland_geometry":"NOT_GENERATED","seal_selection":"NOT_SUPPLIED","joint_acceptance":"INCOMPLETE"})
    injector_contacts=_injector_contacts(plan,inspection,tolerance_m)
    mounting=[];glands=[]
    for part in plan.parts:
        for cavity in part.cavities:
            if not cavity.open_face:continue
            (begin,low,high),(end,_,_)=cavity.profile
            glands.append({"part_id":part.part_id,"role":cavity.role,"face":cavity.open_face,"inner_radius_m":low,"outer_radius_m":high,
                "depth_m":end-begin,"seal_selection":"NOT_SUPPLIED","service_fit":"NOT_ASSESSED","pressure_acceptance":"NOT_PERFORMED"})
        if part.pipe or part.sector or not any(h.role=="fastener-clearance" for h in part.holes):continue
        row=part.profile[-1];r,t=plan.placement(part.frame_id);center=r@np.array([row[0],0.,0.])+t
        for other in plan.parts:
            if other is part or other.pipe or other.sector or not any(h.role=="fastener-clearance" for h in other.holes):continue
            end=other.profile[0];rr,tt=plan.placement(other.frame_id);opposite=rr@np.array([end[0],0.,0.])+tt
            if np.linalg.norm(center-opposite)>tolerance_m or float(r[:,0]@rr[:,0])<1-1e-12:continue
            a,b=_bolt_faces(plan,part,row),_bolt_faces(plan,other,end);pairs=[];used=set()
            for first in a:
                found=[second for second in b if abs(first["radius_m"]-second["radius_m"])<=1e-12
                    and np.linalg.norm(np.array(first["position_m"])-second["position_m"])<=tolerance_m]
                require(len(found)<=1,"JOINT_AMBIGUOUS","Mounting face has ambiguous clearance-bore axes")
                if not found:continue
                second=found[0];require(second["hole_index"] not in used,"JOINT_AMBIGUOUS","Competing mounting-stack bores")
                used.add(second["hole_index"]);pairs.append({"from_hole":first["hole_index"],"to_hole":second["hole_index"]})
            low,high=max(row[1],end[1]),min(row[2],end[2])
            mounting.append({"from_part":part.part_id,"to_part":other.part_id,"matched_bolt_axes":pairs,
                "bolt_axes_complete":bool(a and b and len(a)==len(b)==len(pairs)),
                "continuous_annular_lands_m":_lands(low,high,_blocked_bands(part,row)+_blocked_bands(other,end)),
                "seal_and_preload_acceptance":"NOT_PERFORMED"})
    return {"schema":"cosmos.axial-header-joint-geometry.v1","source_graph_id":plan.graph.graph_id,
        "tolerance_m":tolerance_m,"header_joints":joints,"complete_engine_pressure_joints":False,
        "injector_chamber_interfaces":injector_contacts,
        "mounting_stack_contacts":mounting,"native_grooves":glands,
        "injector_discharge_status":"GEOMETRY_ALIGNED_APERTURES_ONLY" if injector_contacts and all(v["discharge_geometry_connected"] for v in injector_contacts) else "NOT_PROVEN_CONNECTED",
        "scope":"Actual coaxial axial header contacts, conservative continuous radial lands and equal clearance-bore axis mating only; no seal fit, attachment, flange bending, preload, leakage or pressure rating",
        "remaining_interfaces":"Injector-head/plate gas and propellant sealing, lower-header attachment and pipe joints require separate joint designs"}
