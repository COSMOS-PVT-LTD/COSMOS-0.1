"""Exact local-X planar areas of the explicitly supported component feature solids.

These are source-formula sections bound to a QA-verified CAD revision, not a
kernel intersection query, arbitrary plane capability or display-pixel metrology.
"""
from __future__ import annotations

import math

import numpy as np

from systems.contracts.geometry._wire import require


def section(plan,part_id,x_m):
    require(type(part_id) is str and type(x_m) in {int,float} and math.isfinite(x_m),"SECTION_INPUT","Explicit part and finite local axial position [m] required")
    part=next((p for p in plan.parts if p.part_id==part_id),None)
    require(part is not None,"SECTION_PART","Part must belong to the exact retained component revision")
    assert part is not None
    require(part.pipe is None or part.pipe.bend_radius is None,"SECTION_UNSUPPORTED","Toroidal elbow sections need an explicit curve-normal method; local-X axial-profile metrology is not applicable")
    require(part.profile[0][0]<x_m<part.profile[-1][0],"SECTION_PLANE","Plane must lie strictly inside this part's local axial extent; end/tangent sections are not this metrology profile")
    points=np.array(part.profile); inner=float(np.interp(x_m,points[:,0],points[:,1])); outer=float(np.interp(x_m,points[:,0],points[:,2]))
    angle=2*math.pi if part.sector is None else part.sector[1]
    area=angle*(outer**2-inner**2)/2
    boundaries=[{"kind":"annular-sector" if part.sector else "annulus" if inner else "disk","inner_radius_m":inner,"outer_radius_m":outer,"phase_rad":part.sector[0] if part.sector else 0.,"width_rad":angle}]
    if part.cooling:
        c=part.cooling; low=inner+c.hot_ligament; high=low+c.depth
        for index in range(c.count):
            area-=c.width_rad*(high**2-low**2)/2
            boundaries.append({"kind":"removed-cooling-sector","inner_radius_m":low,"outer_radius_m":high,"phase_rad":c.phase_rad+index*2*math.pi/c.count,"width_rad":c.width_rad})
    for hole in part.holes:
        if hole.axial_range is not None:
            require(x_m not in hole.axial_range,"SECTION_PLANE","Finite-bore transition planes require one-sided interpretation; choose an interior cap/plenum plane")
            if not hole.axial_range[0]<x_m<hole.axial_range[1]: continue
        slope=np.array(hole.slope_yz); major=hole.radius*math.sqrt(1+float(slope@slope))
        area-=math.pi*hole.radius*major
        boundaries.append({"kind":"removed-ellipse","center_yz_m":(np.array(hole.center_yz)+slope*x_m).tolist(),"semimajor_m":major,"semiminor_m":hole.radius,"slope_yz":list(hole.slope_yz),"role":hole.role})
    for cavity in part.cavities:
        (start,low,high),(end,_,_) = cavity.profile
        require(x_m not in (start,end),"SECTION_PLANE","Plenum/web transition is not a unique interior section; select a side explicitly")
        if start<x_m<end:
            width=2*math.pi if cavity.sector is None else cavity.sector[1]
            area-=width*(high*high-low*low)/2
            boundaries.append({"kind":"removed-sector-port" if cavity.sector else "removed-annular-plenum","inner_radius_m":low,"outer_radius_m":high,"role":cavity.role,
                               **({"phase_rad":cavity.sector[0],"width_rad":width} if cavity.sector else {})})
    require(area>0,"SECTION_AREA","No positive supported interior section remains")
    rotation,translation=plan.placement(part.frame_id)
    return {"part_id":part_id,"feature_id":part.feature_id,"frame_id":part.frame_id,"local_x_m":float(x_m),"world_plane_origin_m":(rotation@np.array([x_m,0.,0.])+translation).tolist(),"world_plane_normal":rotation[:,0].tolist(),"area_m2":area,"boundaries":boundaries,"method":"EXACT_SOURCE_FORMULA_FOR_SUPPORTED_LOCAL_AXIAL_PLANE","scope":"Analytic profile/sector/through-bore section of this source-bound CAD candidate, not arbitrary-plane kernel intersection, a tessellation measurement or structural/flow capacity acceptance"}
