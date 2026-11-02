"""Source-bound layout study for the approved isolated mechanical concept.

This is a geometric feasibility planner, NOT a generated CAD model or a
pressure/thermal design. Missing native operations are explicit outputs.
"""
import math

import numpy as np

from systems.contracts.geometry._wire import digest, require
from systems.geometry.component_model import IDENTITY, compile_model
from systems.geometry.component_reference import ring_integrals


def prepare_layout(specification,inspection,proposal):
    require(inspection.get("source_graph_id")=="components-"+digest(specification),"CONCEPT_SOURCE","Exact saved source inspection required")
    fields={"scope","source","header_part_id","injector_part_id","head_part_id","chamber_part_id",
        "mount_outer_radius_m","collector_plenum_outer_radius_m","bolt_circle_radius_m","bolt_hole_radius_m","bolt_count"}
    require(type(proposal) is dict and set(proposal)==fields
        and proposal["scope"]=="APPROVED_ISOLATED_CONCEPT_STUDY_NOT_OWNER_INPUTS_OR_HARDWARE_ACCEPTANCE"
        and type(proposal["source"]) is str and 0<len(proposal["source"])<=2048,"CONCEPT_PROPOSAL","Explicit isolated revised-concept proposal required")
    for key in fields-{"scope","source","header_part_id","injector_part_id","head_part_id","chamber_part_id","bolt_count"}:
        require(type(proposal[key]) in {int,float} and math.isfinite(proposal[key]) and proposal[key]>0,"CONCEPT_DIMENSION","Explicit finite positive layout dimensions required")
    n=proposal["bolt_count"];require(type(n) is int and 3<=n<=32,"CONCEPT_DIMENSION","Explicit supported integer bolt count required")
    plan=compile_model(specification,"engine-component-separable-head-study","retained-replay","2026-10-21T00:00:00Z")
    parts={p.part_id:p for p in plan.parts}
    ids=[proposal[k] for k in ("header_part_id","injector_part_id","head_part_id","chamber_part_id")]
    require(len(set(ids))==4 and all(name in parts for name in ids),"CONCEPT_SOURCE","Four distinct actual component parts required")
    header,plate,head,chamber=[parts[name] for name in ids]
    require(header.cavities and any(c.open_passage and c.sector for c in header.cavities)
        and chamber.cooling is not None and len(header.profile)==2 and len(plate.profile)==2
        and {h.role for h in plate.holes}>={"fuel","oxidizer"} and {c.role for c in head.cavities}>={"fuel","oxidizer"},
        "CONCEPT_LAYOUT_UNSUPPORTED","Actual cooling header, bipropellant plate, segregated head and cooled chamber required")
    for part in (header,plate,head,chamber):
        rotation,translation=plan.placement(part.frame_id)
        require(np.array_equal(rotation,np.array(IDENTITY).reshape(3,3)) and np.linalg.norm(translation[1:])<=1e-12,
            "CONCEPT_LAYOUT_UNSUPPORTED","This isolated layout supports coaxial +X parts only; no inferred rotated/arbitrary plumbing")
    start,gas_radius,wall_outer=chamber.profile[0]
    chamber_translation=plan.placement(chamber.frame_id)[1]
    require(np.linalg.norm(chamber_translation)<=1e-12 and chamber.profile[1][1:]==chamber.profile[0][1:]
        and header.profile[0][1]==header.profile[-1][1]==gas_radius
        and max(r[2] for p in (head,plate) for r in p.profile)<=gas_radius,
        "CONCEPT_LAYOUT_UNSUPPORTED","Unplaced straight cylindrical chamber entry and exact matching header gas bore required")
    plate_end=plate.profile[-1][0]+plan.placement(plate.frame_id)[1][0]
    header_end=header.profile[-1][0]+plan.placement(header.frame_id)[1][0]
    require(abs(plate_end-start)<=1e-12 and abs(header_end-start)<=1e-12,
        "CONCEPT_LAYOUT_UNSUPPORTED","Retained injector/chamber start and original header/channel face must coincide")
    ports={p["id"]:p for p in inspection["ports"]}
    outlets={p["id"] for p in ports.values() if p["part_id"]==head.part_id and p["kind"]=="MANIFOLD_OUTLET"}
    mated={m["from"] for m in inspection["matches"] if m["from"] in outlets and ports[m["to"]]["part_id"]==plate.part_id}
    require(bool(outlets) and outlets==mated,"CONCEPT_SOURCE","Retained segregated head outlets must already match this injector plate")
    margin=4*max(specification["source_tolerance"]["value"],specification["export_tolerance"]["value"])
    length=header.profile[-1][0]-header.profile[0][0]
    require(start+length<chamber.profile[1][0]-margin,"CONCEPT_LAYOUT_UNSUPPORTED","Collector length cannot consume the cylindrical chamber or move the convergent/throat")
    outer,high,ring,hole=[proposal[k] for k in ("mount_outer_radius_m","collector_plenum_outer_radius_m","bolt_circle_radius_m","bolt_hole_radius_m")]
    plenum=[c for c in header.cavities if c.role=="coolant"]
    require(len(plenum)==1,"CONCEPT_SOURCE","One exact coolant plenum required")
    low=plenum[0].profile[0][1];supply=[h for h in header.holes if h.role=="coolant-inlet"]
    require(len(supply)==1,"CONCEPT_SOURCE","Exact retained supply bore required")
    supply_radius=supply[0].radius;supply_center=(low+high)/2
    require(outer<=1 and min(high-low,outer-high,hole,ring-hole-high,outer-ring-hole)>margin
        and 2*ring*math.sin(math.pi/n)>2*hole+margin
        and 2*supply_radius+2*margin<high-low,
        "CONCEPT_LIGAMENT","Resolved proposed plenum, mounting ring and bolt ligaments required")
    exposed_clearance=supply_center-supply_radius-wall_outer
    require(exposed_clearance>margin,"CONCEPT_SUPPLY_BLOCKED","Proposed downstream axial return port must clear the actual chamber outer wall")
    # Replace exactly L of the cylindrical entry with an equal-bore collector
    # gas passage. No uniform scaling, throat movement or target-forcing volume.
    old_gas_volume=math.pi*ring_integrals(tuple((x,0.,inner) for x,inner,_ in chamber.profile))[0]
    new_profile=((start+length,gas_radius,wall_outer),*chamber.profile[1:])
    new_core_volume=math.pi*ring_integrals(tuple((x,0.,inner) for x,inner,_ in new_profile))[0]
    collector_volume=math.pi*gas_radius**2*length
    return {"schema":"cosmos.preliminary-separable-head-layout.v1","source_graph_id":plan.graph.graph_id,
        "proposal_sha256":digest(proposal),"scope":proposal["scope"],"source":proposal["source"],
        "native_geometry":"NOT_GENERATED","installed":False,"engineering_acceptance":"NOT_PERFORMED","physical_validation":"NOT_PERFORMED",
        "gas_entry_x_m":start,"proposed_collector_x_m":[start,start+length],"proposed_main_chamber_start_x_m":start+length,
        "unchanged_convergent_start_x_m":chamber.profile[1][0],"unchanged_throat_and_divergent_stations":True,
        "gas_bore_radius_m":gas_radius,"old_total_gas_volume_m3":old_gas_volume,
        "new_main_chamber_gas_volume_m3":new_core_volume,"collector_gas_volume_m3":collector_volume,
        "gas_volume_difference_m3":math.fsum((new_core_volume,collector_volume,-old_gas_volume)),
        "mount_outer_radius_m":outer,"bolt_circle_radius_m":ring,"bolt_hole_radius_m":hole,"bolt_count":n,
        "conservative_head_face_land_inner_radius_m":gas_radius,"conservative_head_face_land_outer_radius_m":ring-hole,
        "conservative_head_face_land_width_m":ring-hole-gas_radius,
        "proposed_front_supply_center_radius_m":supply_center,"retained_supply_bore_radius_m":supply_radius,
        "front_supply_to_chamber_outer_clearance_m":exposed_clearance,"minimum_bolt_to_plenum_radial_ligament_m":ring-hole-high,
        "retained_collector_gas_wall_radial_thickness_m":low-gas_radius,
        "remaining_collector_to_chamber_inner_land_m":chamber.cooling.hot_ligament,
        "injector_hydraulic_dimensions":"UNCHANGED_RETAINED_SOURCE_NOT_WARMED_FUEL_SIZING",
        "joint_status":"INCOMPLETE_NO_SELECTED_SEAL_JOINING_PRELOAD_OR_HOT_ALLOWABLES",
        "thermal_limit":"Relocated collector becomes part of the gas-side thermal boundary; matching its coolant plenum/gas wall is not implemented by this geometric planner",
        "native_requirements":["Front-supply cooling-header primitive with explicit port/channel collision checks",
            "Matching bolt cuts on the head and inclined-bore injector plate, preserving hydraulic source dimensions",
            "Revised external fuel return routing that clears the enlarged mounting flange",
            "Explicit collector/chamber joining and pressure-boundary representation; no implicit weld/fuse acceptance",
            "Actual STEP/STL, intersections, gas-route, contact-land and multi-part topology qualification"]}
