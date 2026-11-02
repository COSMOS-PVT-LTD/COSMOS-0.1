"""Independent isolated-plenum/finite-port/reference checks, not seal approval."""
import math

import numpy as np
import pytest

from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.component_sections import section
from tests.fixtures.component_geometry import model, plan


def test_manifold_independent_removed_volumes_and_axial_moments():
    p=plan("manifold.dual_annular"); part=p.parts[0]; ref=PartReference(p,part)
    radius,back,length,front=.025,.003,.008,.002
    total=back+length+front
    gross=math.pi*radius**2*total
    void=math.pi*((.011**2-.005**2)+(.021**2-.013**2))*length
    ports_back=math.pi*(.0015**2+.002**2)*back
    ports_front=3*math.pi*(.0007**2+.0011**2)*front
    expected=gross-void-ports_back-ports_front
    moment=gross*total/2-void*(back+length/2)-ports_back*back/2-ports_front*(back+length+front/2)
    assert ref.volume_m3==pytest.approx(expected,rel=1e-13)
    assert ref.centroid_m[0]==pytest.approx(moment/expected,rel=1e-13)
    assert part.euler==2-4*(3+1)
    assert len(part.cavities)==2 and len(part.holes)==8


def test_plenums_are_disjoint_ports_open_and_partition_stays_solid():
    p=plan("manifold.dual_annular"); part=p.parts[0]; ref=PartReference(p,part)
    for cavity in part.cavities:
        (a,lo,hi),(b,_,_)=cavity.profile
        assert ref.sdf([[(a+b)/2,(lo+hi)/2,0.]])[0]>0
        for h in [h for h in part.holes if h.role.startswith(cavity.role+"-")]:
            r=math.hypot(*h.center_yz)
            assert lo+h.radius<r<hi-h.radius
            assert ref.sdf([[h.axial_range[0],*h.center_yz],[h.axial_range[1],*h.center_yz]]).min()>0
    assert ref.sdf([[.007,.012,0.]])[0]<0
    samples=ref.surface_samples()
    assert len(samples)>200 and np.abs(ref.sdf(samples)).max()<1e-12


def test_sections_distinguish_inlet_web_cavities_and_outlet_web():
    p=plan("manifold.dual_annular"); radius=.025
    a=section(p,"body",.0015); b=section(p,"body",.007); c=section(p,"body",.012)
    assert a["area_m2"]==pytest.approx(math.pi*(radius**2-.0015**2-.002**2))
    assert b["area_m2"]==pytest.approx(math.pi*(radius**2-(.011**2-.005**2)-(.021**2-.013**2)))
    assert c["area_m2"]==pytest.approx(math.pi*(radius**2-3*(.0007**2+.0011**2)))
    assert {v.get("role") for v in b["boundaries"]} >= {"fuel","oxidizer"}
    with pytest.raises(ValueError): section(p,"body",.003)


@pytest.mark.parametrize("offset",[-.3416666666666667,.7,-2.4])
def test_translated_open_ports_never_invent_zero_residual_metal_disks(offset):
    spec=model("manifold.dual_annular")
    spec["frames"].append({"id":"mounted","parent":"world",
        "origin":[{"value":offset,"unit":"m"},{"value":0.,"unit":"m"},{"value":0.,"unit":"m"}],
        "rotation":[1.,0.,0.,0.,1.,0.,0.,0.,1.]})
    spec["features"][0]["frame"]="mounted"
    p=compile_model(spec,"engine-component-translated-port","r","2026-10-21T00:00:00Z")
    part=p.parts[0];ref=PartReference(p,part)
    for h in part.holes:
        for x in h.axial_range:
            for factor in (0.,.5):
                world=np.array([x+offset,h.center_yz[0]+factor*h.radius,h.center_yz[1]])
                assert ref.sdf([world])[0]>.49*h.radius
    # Every retained cap sample remains on metal, not inside a removed port.
    samples=ref.surface_samples();local=ref.local(samples)
    for h in part.holes:
        for x in h.axial_range:
            cap=np.abs(local[:,0]-x)<1e-14
            distances=np.linalg.norm(local[cap,1:]-h.center_yz,axis=1)
            assert (distances>=h.radius-1e-14).all()


def test_radial_pair_really_has_distinct_feed_ring_radii_and_external_impingement():
    p=plan("injector.biprop_radial_doublet"); part=p.parts[0]
    for h in part.holes:
        assert math.hypot(*h.center_yz)==pytest.approx(.009 if h.role=="fuel" else .015)
    fuel,ox=part.holes[:2]
    impact=.006/(2*math.tan(.2))
    assert impact>part.profile[-1][0]
    assert np.array(fuel.center_yz)+impact*np.array(fuel.slope_yz)==pytest.approx(np.array(ox.center_yz)+impact*np.array(ox.slope_yz))
    old=plan("injector.biprop_doublet")
    assert math.hypot(*old.parts[0].holes[0].center_yz)==pytest.approx(math.hypot(.012,.003))


def test_bolted_flange_exact_volume_holes_and_genus():
    p=plan("interface.bolted_flange"); part=p.parts[0]
    assert PartReference(p,part).volume_m3==pytest.approx(math.pi*(.035**2-.015**2-6*.002**2)*.004)
    assert part.euler==-12 and {h.role for h in part.holes}=={"fastener-clearance"}


@pytest.mark.parametrize("kind,key,value",[("manifold.dual_annular","fuel_outer",.014),
    ("manifold.dual_annular","fuel_inlet_radius",.004),("manifold.dual_annular","ring_radius",.02),
    ("manifold.dual_annular","back_web",1e-7),("manifold.dual_annular","phase",9.),
    ("interface.bolted_flange","bolt_circle_radius",.016),("interface.bolted_flange","bolt_hole_radius",.01)])
def test_crossfeed_blind_unresolved_and_edge_collision_reject(kind,key,value):
    spec=model(kind); spec["features"][0]["parameters"][key]["value"]=value
    with pytest.raises(ValueError): compile_model(spec,"engine-component-invalid","r","2026-10-21T00:00:00Z")
