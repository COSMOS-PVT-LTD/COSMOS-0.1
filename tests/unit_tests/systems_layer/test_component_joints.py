import math
from copy import deepcopy

import numpy as np
import pytest

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_joints import inspect_joints
from systems.geometry.component_model import IDENTITY, compile_model, profile_parameters
from systems.geometry.component_reference import PartReference
from systems.geometry.joint_layout import append_header_bolts
from tests.fixtures.component_geometry import model, plan


def fixture():
    spec=model("manifold.cooling_annular");spec["features"][0]["parameters"]["outer_radius"]["value"]=.05
    collar=deepcopy(model("interface.bolted_flange")["features"][0]);collar.update(id="collar",frame="collar")
    q=lambda v,u="m":{"value":v,"unit":u}
    collar["parameters"].update(bore_radius=q(.035),outer_radius=q(.05),bolt_circle_radius=q(.042))
    spec["features"].append(collar);spec["outputs"].append("collar")
    spec["frames"].append({"id":"collar","parent":"world","origin":[q(.013),q(0.),q(0.)],"rotation":list(IDENTITY)})
    return spec


def compile(spec):
    return compile_model(spec,"engine-component-joint-test","synthetic","2026-10-21T00:00:00Z")


def proposal():
    return {"scope":"ISOLATED_GEOMETRY_HYPOTHESIS_NOT_INSTALLED_ENGINE_INPUTS","source":"Synthetic bolt alignment fixture; no engineering acceptance",
        "header_part_id":"body","collar_part_id":"collar","feature_id":"bolted"}


def test_exact_source_bolt_cuts_preserve_all_plenums_and_match_collar_axes():
    spec=fixture();before=compile(spec);read=inspect_interfaces(before,1e-6)
    candidate=append_header_bolts(spec,read,proposal());value=compile(candidate);result=inspect_interfaces(value,1e-6)
    a,b=before.parts[0],value.parts[0];assert b.cavities==a.cavities and b.holes[:1]==a.holes
    assert len(b.holes)==7 and b.euler==a.euler-12
    removed=math.pi*.002**2*.013*6
    assert PartReference(value,b).volume_m3==pytest.approx(PartReference(before,a).volume_m3-removed,rel=1e-13)
    joint=result["mechanical_joints"]["header_joints"][0];contact=joint["contacts"][0]
    assert contact["part_id"]=="collar" and contact["bolt_axes_complete"] and len(contact["matched_bolt_axes"])==6
    assert joint["minimum_outer_bolt_to_cavity_radial_ligament_m"]==pytest.approx(.006)
    assert not result["mechanical_joints"]["complete_engine_pressure_joints"]
    assert joint["seal_selection"]=="NOT_SUPPLIED" and joint["gland_geometry"]=="NOT_GENERATED"
    assert result["flange_candidates"][0]["bolt_count"]==6  # Supply hole is not a bolt.
    assert spec==fixture()  # Preparation cannot mutate the retained source.


def test_continuous_lands_exclude_entire_hole_band_not_just_sampled_azimuth():
    value=compile(fixture());read=inspect_interfaces(value,1e-6);joint=read["mechanical_joints"]["header_joints"][0]
    assert joint["gas_to_coolant_radial_land_m"]==pytest.approx(.007)
    assert not joint["contacts"][0]["bolt_axes_complete"]
    lands=joint["contacts"][0]["continuous_annular_lands_m"]
    assert np.array([[r["inner_radius_m"],r["outer_radius_m"]] for r in lands])==pytest.approx(np.array([[.035,.04],[.044,.05]]))


@pytest.mark.parametrize("key,value",[("bolt_circle_radius",.033),("bolt_circle_radius",.049),("bolt_hole_radius",.00001),("count",2),("phase",7)])
def test_bolt_feature_rejects_cavity_edge_resolution_and_capacity_violations(key,value):
    spec=model("interface.bolt_pattern");spec["features"][-1]["parameters"][key]["value"]=value
    with pytest.raises(ValueError):compile(spec)


def test_bolt_cut_cannot_silently_repattern_an_existing_flange():
    # Existing flange cannot be patterned twice, preserving non-overlap integral assumptions.
    spec=model("interface.bolt_pattern");spec["features"][0]=deepcopy(model("interface.bolted_flange")["features"][0])
    with pytest.raises(ValueError,match="no existing fastener pattern"):compile(spec)


def test_joint_proposal_rejects_stale_inspection_unknown_dimensions_and_missing_contacts():
    spec=fixture();read=inspect_interfaces(compile(spec),1e-6)
    with pytest.raises(ValueError,match="Exact current opening"):append_header_bolts(spec,{**read,"source_graph_id":"stale"},proposal())
    with pytest.raises(ValueError,match="Explicit isolated matching"):append_header_bolts(spec,read,{**proposal(),"preload":100})
    changed=fixture();changed["frames"][-1]["origin"][1]["value"]=.001
    with pytest.raises(ValueError,match="One actual coaxial"):
        append_header_bolts(changed,inspect_interfaces(compile(changed),1e-6),proposal())


def test_azimuth_mismatch_is_not_a_matching_bolt_pattern():
    spec=fixture();spec=append_header_bolts(spec,inspect_interfaces(compile(spec),1e-6),proposal())
    spec["features"][-1]["parameters"]["phase"]["value"]+=.2
    contacts=inspect_interfaces(compile(spec),1e-6)["mechanical_joints"]["header_joints"][0]["contacts"]
    assert not contacts[0]["bolt_axes_complete"] and not contacts[0]["matched_bolt_axes"]


def test_joint_inspection_rejects_wrong_source_and_tolerance():
    value=plan("manifold.cooling_annular");read=inspect_interfaces(value,1e-6)
    with pytest.raises(ValueError,match="exact saved opening source"):inspect_joints(value,{**read,"source_graph_id":"wrong"},1e-6)
    for tolerance in (True,float("nan"),0,.01):
        with pytest.raises(ValueError):inspect_joints(value,read,tolerance)


@pytest.mark.parametrize("bore,land,connected",[(.025,0.,True),(.024,.001,True),(.005,.004,False)])
def test_discharge_alignment_does_not_invent_an_injector_pressure_attachment(bore,land,connected):
    spec=model("injector.biprop_radial_doublet");spec["features"].append({"id":"wall","operation":"profile.wall","frame":"world",
        "depends_on":[],"parameters":profile_parameters(((.004,bore,bore+.004),(.03,bore,bore+.004)))})
    spec["outputs"].append("wall");report=inspect_interfaces(compile(spec),1e-6)
    contact=report["mechanical_joints"]["injector_chamber_interfaces"][0]
    assert contact["discharge_geometry_connected"] is connected and not contact["pressure_boundary_complete"]
    assert contact["wall_contacts"][0]["annular_face_overlap_width_m"]==pytest.approx(land)
    assert contact["wall_contacts"][0]["mechanical_seal_and_attachment"]=="NOT_DESIGNED"
    if land==0:assert contact["wall_contacts"][0]["face_attachment_geometry"]=="ZERO_ANNULAR_FACE_LAND"


def test_discharge_geometry_cannot_bridge_a_gap_or_reverse_the_injector():
    spec=model("injector.biprop_radial_doublet");spec["features"].append({"id":"wall","operation":"profile.wall","frame":"world",
        "depends_on":[],"parameters":profile_parameters(((.005,.025,.03),(.04,.025,.03)))})
    spec["outputs"].append("wall");report=inspect_interfaces(compile(spec),1e-6)
    assert report["injector_discharge_to_chamber"]=="NOT_PROVEN_CONNECTED"
    assert report["mechanical_joints"]["injector_chamber_interfaces"][0]["wall_contacts"]==[]
