import math
from copy import deepcopy

import pytest

from systems.geometry.component_circuits import assess_circuits
from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import compile_model
from systems.geometry.separable_head_cad import prepare_cad
from tests.fixtures.component_geometry import model
from tests.unit_tests.systems_layer.test_separable_head_layout import (
    proposal,
    source,
)


def inputs():
    spec=source();q=lambda v,u="m":{"value":v,"unit":u}
    header=next(f for f in spec["features"] if f["id"]=="header")
    header["parameters"].update(supply_hole_radius=q(.0015),supply_phase=q(0.,"rad"))
    head=next(f for f in spec["features"] if f["id"]=="head")
    head["parameters"].update(fuel_inlet_phase=q(0.,"rad"),oxidizer_inlet_phase=q(math.pi,"rad"))
    lower=deepcopy(model("manifold.cooling_annular")["features"][0]);lower.update(id="lower",frame="lower")
    lower["parameters"].update(plenum_inner=q(.0155),port_inner=q(.016),port_outer=q(.017),phase=q(-.4,"rad"))
    spec["features"].append(lower);spec["outputs"].append("lower")
    spec["frames"].append({"id":"lower","parent":"world","origin":[q(.093),q(0.),q(0.)],"rotation":[-1.,0.,0.,0.,1.,0.,0.,0.,-1.]})
    collar=deepcopy(model("interface.bolted_flange")["features"][0]);collar["id"]="collar"
    spec["features"].append(collar);spec["outputs"].append("collar")
    settings={"scope":"ISOLATED_REVISED_CAD_STUDY_NOT_OWNER_INPUTS_OR_HARDWARE_ACCEPTANCE","source":"Synthetic explicit revised-CAD fixture only",
        "suppressed_mount_feature":"collar","export_coolant_domains":False,"pipe_wall_m":.0012,"bend_radius_m":.008,
        "stub_length_m":.015,"return_outer_center_radius_m":.085,"fuel_supply_length_m":.04,"oxidizer_supply_length_m":.04,"grooves":[]}
    return spec,proposal(),settings


def compile(spec):return compile_model(spec,"engine-component-revised-cad-test","synthetic","2026-10-21T00:00:00Z")


def test_revised_concept_preserves_source_fluid_bores_connects_circuits_and_mounting_stack():
    spec,layout,settings=inputs();old=deepcopy(spec)
    result,bindings,dimensions=prepare_cad(spec,inspect_interfaces(compile(spec),1e-6),layout,settings)
    value=compile(result);read=inspect_interfaces(value,1e-6);circuits=assess_circuits(value,read,**bindings)
    assert circuits["topology_complete"],circuits["issues"]
    assert len(value.parts)==16 and all(p.role=="metal" for p in value.parts)
    assert len([p for p in value.parts if p.pipe])==11
    mounts=read["mechanical_joints"]["mounting_stack_contacts"]
    assert {(p["from_part"],p["to_part"]) for p in mounts}=={("head-mount-bolts","injector-mount-bolts"),("injector-mount-bolts","collector-mount-bolts")}
    assert all(p["bolt_axes_complete"] and len(p["matched_bolt_axes"])==6 for p in mounts)
    assert read["mechanical_joints"]["injector_chamber_interfaces"][0]["wall_contacts"][0]["annular_face_overlap_width_m"]>0
    assert dimensions["gas_volume_difference_m3"]==pytest.approx(0.,abs=1e-18)
    assert spec==old
    for name in ("head","plate"):
        source_feature=next(f for f in spec["features"] if f["id"]==name)
        target=next(f for f in result["features"] if f["id"]==name)
        for key in ("count","fuel_hole_radius","oxidizer_hole_radius","ring_radius","separation","phase"):
            assert target["parameters"][key]==source_feature["parameters"][key]


@pytest.mark.parametrize("key,value",[("return_outer_center_radius_m",.074),("bend_radius_m",.03),("pipe_wall_m",.012),("suppressed_mount_feature","head"),("export_coolant_domains",1)])
def test_revised_layout_rejects_flange_interference_wrong_suppression_and_unsupported_routing(key,value):
    spec,layout,settings=inputs()
    with pytest.raises(ValueError):prepare_cad(spec,inspect_interfaces(compile(spec),1e-6),layout,{**settings,key:value})


def test_explicit_groove_is_generated_without_seal_or_joint_acceptance():
    spec,layout,settings=inputs();settings["grooves"]=[{"id":"plate-groove","part_feature_id":"plate",
        "inner_radius_m":.030,"outer_radius_m":.034,"depth_m":.001,"face":1}]
    result,bindings,_=prepare_cad(spec,inspect_interfaces(compile(spec),1e-6),layout,settings)
    value=compile(result);read=inspect_interfaces(value,1e-6)
    assert assess_circuits(value,read,**bindings)["topology_complete"]
    assert read["mechanical_joints"]["native_grooves"][0]["seal_selection"]=="NOT_SUPPLIED"
    assert not read["mechanical_joints"]["complete_engine_pressure_joints"]


def test_five_grooves_chain_on_one_plate_without_losing_previous_cuts_or_source_bores():
    spec,layout,settings=inputs();original=deepcopy(spec)
    ranges=((.002,.004,-1),(.021,.023,-1),(.030,.032,-1),(.035,.037,-1),(.040,.042,1))
    settings["grooves"]=[{"id":"groove-"+str(i),"part_feature_id":"plate","inner_radius_m":lo,
        "outer_radius_m":hi,"depth_m":.001,"face":face} for i,(lo,hi,face) in enumerate(ranges)]
    result,bindings,_=prepare_cad(spec,inspect_interfaces(compile(spec),1e-6),layout,settings)
    value=compile(result);read=inspect_interfaces(value,1e-6)
    assert assess_circuits(value,read,**bindings)["topology_complete"]
    grooves=read["mechanical_joints"]["native_grooves"]
    assert len(grooves)==5 and {g["part_id"] for g in grooves}=={"groove-4"}
    assert sum(g["face"]=="start" for g in grooves)==4
    assert sum(g["face"]=="end" for g in grooves)==1
    assert len(value.parts)==16 and spec==original
    plate=next(p for p in value.parts if p.part_id=="groove-4")
    assert len(plate.cavities)==5 and len([h for h in plate.holes if h.role in {"fuel","oxidizer"}])==6
    assert all(p["bolt_axes_complete"] for p in read["mechanical_joints"]["mounting_stack_contacts"])


def test_six_grooves_exceed_this_explicit_study_envelope():
    spec,layout,settings=inputs();settings["grooves"]=[{}]*6
    with pytest.raises(ValueError,match="Exact explicit"):
        prepare_cad(spec,inspect_interfaces(compile(spec),1e-6),layout,settings)
