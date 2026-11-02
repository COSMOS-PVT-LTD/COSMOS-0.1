import math
from copy import deepcopy

import numpy as np
import pytest

from systems.geometry.component_model import compile_model, from_contracts
from systems.geometry.component_reference import PartReference, ring_integrals
from tests.fixtures.component_geometry import model, plan


@pytest.mark.parametrize("kind",["profile.wall","cooling.axial_sector","injector.showerhead","injector.doublet","injector.biprop_doublet","injector.biprop_radial_doublet","manifold.dual_annular","interface.bolted_flange","injector.triplet","injector.coaxial","injector.pintle"])
def test_typed_roundtrip_positive_analytic_moments_and_true_source_samples(kind):
    value=plan(kind)
    assert from_contracts(value.snapshot,value.graph)==value
    for part in value.parts:
        ref=PartReference(value,part)
        assert ref.volume_m3>0 and np.isfinite(ref.centroid_m).all()
        samples=ref.surface_samples()
        assert len(samples)>20 and np.abs(ref.sdf(samples)).max()<2e-12
        assert np.all(samples>=ref.bounds_m[:3]-1e-12) and np.all(samples<=ref.bounds_m[3:]+1e-12)


def test_channel_void_volumes_exactly_reconcile_uncut_wall_and_metal():
    base=plan(); cooled=plan("cooling.axial_sector")
    volume=PartReference(base,base.parts[0]).volume_m3
    assert sum(PartReference(cooled,p).volume_m3 for p in cooled.parts)==pytest.approx(volume,rel=1e-14)
    assert cooled.parts[0].euler==-8 and all(p.euler==2 for p in cooled.parts[1:])
    assert PartReference(cooled,cooled.parts[0]).volume_m3<volume


def test_showerhead_drilled_plate_matches_separate_closed_form():
    value=plan("injector.showerhead"); ref=PartReference(value,value.parts[0])
    expected=math.pi*.025**2*.004-3*math.pi*.0008**2*.004
    assert ref.volume_m3==pytest.approx(expected,rel=1e-14)
    assert ref.centroid_m==pytest.approx([.002,0.,0.],abs=1e-16)
    assert value.parts[0].euler==-4


def test_biprop_doublet_distinct_roles_areas_and_exact_removed_volume():
    value=plan("injector.biprop_doublet"); part=value.parts[0]
    assert len(part.holes)==6
    for role,radius in (("fuel",.0007),("oxidizer",.0011)):
        holes=[h for h in part.holes if h.role==role]
        assert len(holes)==3 and all(h.radius==radius for h in holes)
        assert sum(math.pi*h.radius**2 for h in holes)==pytest.approx(3*math.pi*radius**2)
    removed=3*math.pi*(.0007**2+.0011**2)*.004/math.cos(.2)
    assert PartReference(value,part).volume_m3==pytest.approx(math.pi*.025**2*.004-removed,rel=1e-13)
    assert part.euler==-10
    changed=model("injector.biprop_doublet")
    changed["features"][0]["parameters"]["fuel_hole_radius"]["value"]*=1.1
    next_=compile_model(changed,value.snapshot.project_id,"r2","2026-10-21T00:00:00Z")
    assert value.graph.impact(value.snapshot,next_.snapshot).stale_features==("body",)


def test_old_doublet_remains_equal_radius_and_unassigned():
    old=plan("injector.doublet").parts[0]
    assert {h.role for h in old.holes}=={"paired-port"}
    assert {h.radius for h in old.holes}=={.0008}


def test_solid_axis_is_not_a_fictitious_surface():
    spec=model(); spec["features"][0]["operation"]="profile.solid"
    for key,val in spec["features"][0]["parameters"].items():
        if key.startswith("inner"): val["value"]=0.
    value=compile_model(spec,"engine-component-solid","r","2026-10-20T00:00:00Z")
    assert PartReference(value,value.parts[0]).sdf([[.02,0.,0.]])[0]<-.01


def test_proper_nested_rigid_frame_and_downstream_impact():
    spec=model("injector.coaxial")
    spec["frames"].append({"id":"rotated","parent":"world","origin":[{"value":v,"unit":"m"} for v in (.1,.2,.3)],"rotation":[0.,-1.,0.,1.,0.,0.,0.,0.,1.]})
    spec["features"].append({"id":"placed","operation":"placement.rigid","frame":"rotated","depends_on":["body"],"parameters":{}}); spec["outputs"]=["placed"]
    value=compile_model(spec,"engine-component-placed","r","2026-10-20T00:00:00Z")
    assert PartReference(value,value.parts[0]).centroid_m==pytest.approx([.1,.21,.3])
    changed=deepcopy(spec); changed["features"][0]["parameters"]["length"]["value"]*=1.1
    next_=compile_model(changed,"engine-component-placed","r2","2026-10-20T00:00:00Z")
    assert value.graph.impact(value.snapshot,next_.snapshot).stale_features==("body","placed")


@pytest.mark.parametrize("defect",["unit","cycle","frame","hole_collision","channel_roof","unknown","negative","hidden"])
def test_invalid_contracts_fail_before_native_admission(defect):
    spec=model("injector.triplet" if defect=="hole_collision" else "cooling.axial_sector" if defect=="channel_roof" else "profile.wall")
    if defect=="unit": spec["source_tolerance"]["unit"]="mm"
    if defect=="cycle": spec["features"][0]["depends_on"]=["body"]
    if defect=="frame": spec["frames"][0]["rotation"][0]=-1.
    if defect=="hole_collision": spec["features"][0]["parameters"]["separation"]["value"]=.001
    if defect=="channel_roof": spec["features"][1]["parameters"]["depth"]["value"]=.003
    if defect=="unknown": spec["features"][0]["operation"]="injector.swirl-unqualified"
    if defect=="negative": spec["features"][0]["parameters"]["outer0"]["value"]=-.1
    if defect=="hidden": spec["features"][0]["parameters"]["hidden"]={"value":1,"unit":"m"}
    with pytest.raises(ValueError): compile_model(spec,"engine-component-invalid","r","2026-10-20T00:00:00Z")


def test_independent_polynomial_integral_matches_numeric_ring_quadrature():
    rows=((0.,.01,.015),(.03,.005,.011))
    integral,moment=ring_integrals(rows)
    x=np.linspace(0,.03,10001); y=(.015+(.011-.015)*x/.03)**2-(.01+(.005-.01)*x/.03)**2
    numeric=np.sum((y[1:]+y[:-1])*np.diff(x)/2)
    assert integral==pytest.approx(numeric,rel=1e-9)
    assert 0<moment/integral<.03
