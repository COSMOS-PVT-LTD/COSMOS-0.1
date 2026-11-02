import math
from copy import deepcopy

import numpy as np
import pytest

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from tests.fixtures.component_geometry import model, plan


def compile(spec):
    return compile_model(spec,"engine-component-revised-joint-test","synthetic","2026-10-21T00:00:00Z")


@pytest.mark.parametrize("face",[-1,1])
def test_blind_groove_volume_opening_and_retained_floor_are_independent(face):
    spec=model("interface.face_groove");spec["features"][-1]["parameters"]["face"]["value"]=face
    value=compile(spec);part=value.parts[0];ref=PartReference(value,part)
    old=plan("interface.bolted_flange");r=.0195
    assert ref.volume_m3==pytest.approx(PartReference(old,old.parts[0]).volume_m3-math.pi*(.021**2-.018**2)*.001,rel=1e-13)
    cap=0. if face<0 else .004;floor=.001 if face<0 else .003
    assert ref.sdf([[cap,r,0.]])[0]>0  # No fictitious metal cap across the opening.
    assert abs(ref.sdf([[floor,r,0.]])[0])<1e-15
    metal=floor+(1 if face<0 else -1)*.0001
    assert ref.sdf([[metal,r,0.]])[0]<0
    assert np.max(np.abs(ref.sdf(ref.surface_samples())))<1e-12
    assert part.euler==old.parts[0].euler


def test_inclined_source_bores_and_bolts_stay_exact_after_groove_cuts():
    original=plan("injector.biprop_radial_doublet");value=plan("grooved-bolted-injector");part=value.parts[0]
    assert part.holes[:6]==original.parts[0].holes
    assert sum(h.role=="fastener-clearance" for h in part.holes)==6 and part.euler==-22
    assert inspect_interfaces(value,1e-6)["flange_candidates"][0]["bolt_count"]==6
    assert not inspect_interfaces(value,1e-6)["geometry_route_complete"]


@pytest.mark.parametrize("key,value",[("depth",.00395),("inner_radius",.01501),("outer_radius",.026),("face",0),("depth",.00001)])
def test_groove_rejects_broken_floor_bore_fastener_lands_and_hidden_face(key,value):
    spec=model("interface.face_groove");spec["features"][-1]["parameters"][key]["value"]=value
    with pytest.raises(ValueError):compile(spec)


def test_groove_does_not_open_into_a_closed_plenum():
    spec=model("manifold.dual_annular");groove=deepcopy(model("interface.face_groove")["features"][-1])
    groove["depends_on"]=["body"];groove["parameters"].update(inner_radius={"value":.006,"unit":"m"},outer_radius={"value":.009,"unit":"m"},depth={"value":.004,"unit":"m"})
    spec["features"].append(groove);spec["outputs"]=["grooved"]
    with pytest.raises(ValueError,match="floor/land"):compile(spec)


def test_front_supply_is_actual_exterior_port_not_a_channel_or_blind_cap():
    value=plan("manifold.cooling_front_supply");read=inspect_interfaces(value,1e-6);supply=next(p for p in read["ports"] if p["kind"]=="COOLING_HEADER_SUPPLY")
    assert supply["normal"]==[1.,0.,0.] and supply["position_m"][0]==pytest.approx(.013)
    assert supply["aperture"]["minor_radius_m"]==.003
    assert PartReference(value,value.parts[0]).sdf([supply["position_m"]])[0]>0
    spec=model("manifold.cooling_front_supply");spec["features"][0]["parameters"]["plenum_outer"]["value"]=.034
    with pytest.raises(ValueError,match="outside every channel"):compile(spec)


def test_full_length_inclined_hole_envelope_prevents_near_exit_bolt_collision():
    spec=model("bolted-injector");p=spec["features"][-1]["parameters"]
    p["bolt_circle_radius"]["value"]=.015;p["bolt_hole_radius"]["value"]=.001
    # Even if the x=0 centers happened to clear, the whole inclined port must clear.
    with pytest.raises(ValueError,match="fluid ports"):compile(spec)
