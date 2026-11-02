"""Explicit isolated meridional U-return proposal, not universal auto-plumbing.

All dimensions are proposal inputs. Bore sizes/port locations come from the
exact inspection, not target thrust scaling. Unsupported layouts fail closed.
This creates separate connected tube bodies; welding/sealing is not inferred.
"""
import math
from copy import deepcopy

import numpy as np

from systems.contracts.geometry._wire import digest, require


def append_engine_pipes(specification,inspection,proposal):
    require(inspection.get("source_graph_id")=="components-"+digest(specification),
        "PIPE_SOURCE","Opening inspection must bind this exact component specification; no unrelated/stale port table")
    expected={"scope","source","lower_header_port","upper_header_port","fuel_manifold_port","oxidizer_manifold_port",
        "wall_thickness_m","return_bend_radius_m","return_stub_length_m","fuel_supply_length_m","oxidizer_supply_length_m"}
    require(type(proposal) is dict and set(proposal)==expected
        and proposal["scope"]=="ISOLATED_GEOMETRY_HYPOTHESIS_NOT_INSTALLED_ENGINE_INPUTS",
        "PIPE_PROPOSAL","Exact separately labelled isolated geometry proposal required")
    for key in ("wall_thickness_m","return_bend_radius_m","return_stub_length_m","fuel_supply_length_m","oxidizer_supply_length_m"):
        require(type(proposal[key]) in {int,float} and math.isfinite(proposal[key]) and proposal[key]>0,
            "PIPE_PROPOSAL","Explicit finite positive pipe layout dimensions required")
    require(type(proposal["source"]) is str and 0<len(proposal["source"])<=2048,"PIPE_PROPOSAL","Explicit source and applicability required")
    ports={p["id"]:p for p in inspection["ports"]}; open_ends={p["port_id"] for p in inspection["unconnected_ports"]}
    names=[proposal[k] for k in ("lower_header_port","upper_header_port","fuel_manifold_port","oxidizer_manifold_port")]
    require(len(set(names))==4 and all(key in open_ends for key in names),"PIPE_PROPOSAL","Four distinct actual unconnected source openings required")
    lower,upper,fuel,oxidizer=[ports[key] for key in names]
    require(lower["kind"]==upper["kind"]=="COOLING_HEADER_SUPPLY"
        and fuel["kind"]==oxidizer["kind"]=="MANIFOLD_INLET" and fuel["fluid"]=="fuel" and oxidizer["fluid"]=="oxidizer",
        "PIPE_ROLE","Explicit separate lower/upper headers and segregated injector-head fuel/oxidizer ports required")
    require(all(p["aperture"]["kind"]=="CIRCLE" for p in (lower,upper,fuel,oxidizer))
        and np.allclose(lower["normal"],[1,0,0],rtol=0,atol=1e-12)
        and all(np.allclose(p["normal"],[-1,0,0],rtol=0,atol=1e-12) for p in (upper,fuel,oxidizer)),
        "PIPE_LAYOUT_UNSUPPORTED","This explicit proposal supports axial circular ports only; no guessed arbitrary routing")
    a,b=np.array(upper["position_m"]),np.array(fuel["position_m"])
    require(abs(a[0]-b[0])<=1e-12 and abs(a[2]-b[2])<=1e-12
        and upper["aperture"]["minor_radius_m"]==fuel["aperture"]["minor_radius_m"],
        "PIPE_LAYOUT_UNSUPPORTED","Coplanar equal-bore upper/fuel ports required; reducer not silently invented")
    radius=proposal["return_bend_radius_m"]; stub=proposal["return_stub_length_m"]; span=a[1]-b[1]-2*radius
    require(span>4*max(specification["source_tolerance"]["value"],specification["export_tolerance"]["value"]),
        "PIPE_LAYOUT_UNSUPPORTED","Port spacing cannot accommodate the declared U-return bend radius and resolved span")
    result=deepcopy(specification);result["source"]=proposal["source"]
    q=lambda value,unit="m":{"value":float(value),"unit":unit}
    def append(name,origin,x,y,bore,*,length=None,bend=False):
        rotation=np.column_stack((x,y,np.cross(x,y)))
        result["frames"].append({"id":name,"parent":"world","origin":[q(v) for v in origin],"rotation":rotation.flatten().tolist()})
        parameters={"bore_radius":q(bore),"wall_thickness":q(proposal["wall_thickness_m"])}
        parameters.update({"bend_radius":q(radius),"angle":q(math.pi/2,"rad")} if bend else {"length":q(length)})
        result["features"].append({"id":name,"operation":"pipe.elbow" if bend else "pipe.circular","frame":name,"depends_on":[],"parameters":parameters})
        result["outputs"].append(name)
    bore=upper["aperture"]["minor_radius_m"]
    append("fuel-return-upper",a,[-1,0,0],[0,-1,0],bore,length=stub)
    append("fuel-return-elbow-a",a+[-stub,0,0],[-1,0,0],[0,-1,0],bore,bend=True)
    mid=a+[-stub-radius,-radius,0]
    append("fuel-return-span",mid,[0,-1,0],[1,0,0],bore,length=span)
    append("fuel-return-elbow-b",mid+[0,-span,0],[0,-1,0],[1,0,0],bore,bend=True)
    append("fuel-return-head",b+[-stub,0,0],[1,0,0],[0,1,0],bore,length=stub)
    append("fuel-supply",np.array(lower["position_m"]),[1,0,0],[0,1,0],lower["aperture"]["minor_radius_m"],length=proposal["fuel_supply_length_m"])
    length=proposal["oxidizer_supply_length_m"]
    append("oxidizer-supply",np.array(oxidizer["position_m"])-[length,0,0],[1,0,0],[0,1,0],oxidizer["aperture"]["minor_radius_m"],length=length)
    return result,{"fuel_boundary":"fuel-supply.end-b","oxidizer_boundary":"oxidizer-supply.end-a"}
