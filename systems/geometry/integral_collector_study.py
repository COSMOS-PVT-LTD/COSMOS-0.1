"""Read-only, source-bound preparation for an UNQUALIFIED integral concept probe.

Not a generic union feature, manufactured bimetal or accepted component model.
Only the exact coaxial header/cooled-wall contact is within this study.
"""
import math

import numpy as np

from systems.contracts.geometry._wire import require
from systems.geometry.component_reference import PartReference, ring_integrals


def prepare_probe(plan,inspection,*,collector_id,chamber_id):
    require(inspection.get("source_graph_id")==plan.graph.graph_id,"INTEGRAL_SOURCE","Exact saved opening inspection required")
    parts={p.part_id:p for p in plan.parts}
    require(collector_id!=chamber_id and {collector_id,chamber_id}<=set(parts),"INTEGRAL_SOURCE","Two distinct exact metal parts required")
    header,wall=parts[collector_id],parts[chamber_id]
    require(header.role==wall.role=="metal" and header.pipe is None and header.cooling is None and wall.cooling is not None
        and not wall.holes and not wall.cavities and header.profile[0][1:]==header.profile[-1][1:],
        "INTEGRAL_SCOPE","Uniform axial collector and unmodified cooled wall required; no arbitrary body fusion")
    translations=[]
    for part in (header,wall):
        r,t=plan.placement(part.frame_id)
        require(np.array_equal(r,np.eye(3)) and np.linalg.norm(t[1:])<=1e-12,"INTEGRAL_FRAME","This probe supports coaxial +X source only")
        translations.append(t)
    ht,wt=translations
    end=header.profile[-1][0]+ht[0];start=wall.profile[0][0]+wt[0]
    require(abs(end-start)<=1e-12 and header.profile[-1][1]==wall.profile[0][1],
        "INTEGRAL_CONTACT","Exact coincident gas bore and axial contact required; no bridge, snap or healing")
    c=wall.cooling
    sectors=[v for v in header.cavities if v.sector and v.open_passage]
    plenums=[v for v in header.cavities if v.sector is None and not v.open_face]
    require(len(sectors)==c.count and len(plenums)==1 and len(header.cavities)==c.count+1,
        "INTEGRAL_CAVITIES","Exact single plenum and complete source channel openings required")
    port_parts={p["id"]:p["part_id"] for p in inspection["ports"]}
    relevant=[m for m in inspection["matches"] if {port_parts[m["from"]],port_parts[m["to"]]}=={collector_id,chamber_id}
        and m.get("opening")=="MATCHING_WORLD_ANNULAR_SECTORS"]
    require(len(relevant)==c.count,"INTEGRAL_CONTACT","Every exact source channel/header aperture must already mate")
    bore,outer=wall.profile[0][1:];low=bore+c.hot_ligament;high=low+c.depth
    overlap_outer=min(outer,header.profile[-1][2])
    require(bore<low<high<overlap_outer,"INTEGRAL_CONTACT","Every coolant section must lie inside the actual common annular face")
    contact=math.pi*(overlap_outer**2-bore**2)-c.count*c.width_rad/2*(high**2-low**2)
    require(contact>0,"INTEGRAL_CONTACT","Positive source metal contact area required")
    # Explicit source profiles, no cutter padding or fictitious passage drilling.
    profiles=[]
    for cavity in header.cavities:
        profiles.append({"profile":[[float(x+ht[0]),ri,ro] for x,ri,ro in cavity.profile],
            "sector":cavity.sector,"role":cavity.role})
    channel_profile=[[float(x+wt[0]),r+c.hot_ligament,r+c.hot_ligament+c.depth] for x,r,_ in wall.profile]
    for i in range(c.count):profiles.append({"profile":channel_profile,"sector":[c.phase_rad+2*math.pi*i/c.count,c.width_rad],"role":"channel-"+str(i)})
    holes=[]
    for h in header.holes:
        if h.role=="fastener-clearance":continue
        require(h.slope_yz==(0.,0.) and h.axial_range is not None and h.role=="coolant-outlet",
            "INTEGRAL_SUPPLY","This probe requires an actual axial front coolant outlet")
        holes.append({"radius":h.radius,"origin":[float(h.axial_range[0]+ht[0]),*h.center_yz],"length":h.axial_range[1]-h.axial_range[0]})
    require(len(holes)==1,"INTEGRAL_SUPPLY","One explicit collector outlet required")
    fluid_volume=math.fsum((math.pi if v["sector"] is None else v["sector"][1]/2)*ring_integrals(v["profile"])[0] for v in profiles)
    fluid_volume+=math.fsum(math.pi*h["radius"]**2*h["length"] for h in holes)
    refs=[PartReference(plan,p) for p in (header,wall)]
    return {"scope":"UNQUALIFIED_INTEGRAL_COLLECTOR_GEOMETRY_FEASIBILITY_ONLY",
        "source_graph_id":plan.graph.graph_id,"collector_id":collector_id,"chamber_id":chamber_id,
        "contact_x_m":float(end),"expected_contact_area_m2":contact,
        "expected_parts":[{"part_id":p.part_id,"volume_m3":ref.volume_m3,"centroid_m":ref.centroid_m.tolist()} for p,ref in zip((header,wall),refs,strict=True)],
        "expected_fused_metal_volume_m3":math.fsum(ref.volume_m3 for ref in refs),
        "fluid_profiles":profiles,"fluid_holes":holes,"expected_connected_fluid_volume_m3":fluid_volume,
        "gas_wall_minimum_radial_thickness_m":min(row[1] for v in plenums for row in v.profile)-bore,
        "remaining_pressure_interfaces":["Injector plate / integral collector face seal and bolt load path",
            "Nozzle-end header / cooled wall seam (not selected for this probe)","Collector outlet / fuel return pipe joint","Remaining pipe and feed interfaces"],
        "material_partition":"NOT_DESIGNED_GEOMETRIC_UNION_IS_NOT_A_BIMETALLIC_BOND",
        "manufacturing_acceptance":"NOT_PERFORMED","physical_validation":"NOT_PERFORMED"}
