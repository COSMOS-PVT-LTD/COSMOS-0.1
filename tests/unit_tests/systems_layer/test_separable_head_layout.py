from copy import deepcopy

import pytest

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.component_model import IDENTITY, compile_model
from systems.geometry.separable_head_layout import prepare_layout
from tests.fixtures.component_geometry import model


def source():
    spec=model("cooling.axial_sector");q=lambda v,u="m":{"value":v,"unit":u}
    for i in (0,1):
        spec["features"][0]["parameters"]["inner"+str(i)]=q(.026)
        spec["features"][0]["parameters"]["outer"+str(i)]=q(.030)
    header=deepcopy(model("manifold.cooling_annular")["features"][0]);header.update(id="header",frame="header")
    header["parameters"].update(bore_radius=q(.026),outer_radius=q(.05),plenum_inner=q(.0265),port_inner=q(.027),port_outer=q(.028))
    head=deepcopy(model("manifold.dual_annular")["features"][0]);head.update(id="head",frame="head")
    plate=deepcopy(model("injector.biprop_radial_doublet")["features"][0]);plate.update(id="plate",frame="plate");plate["parameters"]["radius"]=q(.026)
    for key in ("ring_radius","separation","count","fuel_hole_radius","oxidizer_hole_radius","phase"):
        plate["parameters"][key]=deepcopy(head["parameters"][key])
    spec["features"] += [header,head,plate];spec["outputs"] += ["header","head","plate"]
    for name,x in (("header",-.013),("head",-.017),("plate",-.004)):
        spec["frames"].append({"id":name,"parent":"world","origin":[q(x),q(0.),q(0.)],"rotation":list(IDENTITY)})
    return spec


def proposal():
    return {"scope":"APPROVED_ISOLATED_CONCEPT_STUDY_NOT_OWNER_INPUTS_OR_HARDWARE_ACCEPTANCE","source":"Synthetic explicit geometric study only",
        "header_part_id":"header","injector_part_id":"plate","head_part_id":"head","chamber_part_id":"channels",
        "mount_outer_radius_m":.075,"collector_plenum_outer_radius_m":.055,"bolt_circle_radius_m":.065,"bolt_hole_radius_m":.002,"bolt_count":6}


def inspect(spec):
    return inspect_interfaces(compile_model(spec,"engine-component-layout-test","synthetic","2026-10-21T00:00:00Z"),1e-6)


def test_layout_preserves_gas_volume_throat_source_and_exposes_return_port_without_installing():
    spec=source();result=prepare_layout(spec,inspect(spec),proposal())
    assert result["gas_volume_difference_m3"]==pytest.approx(0.,abs=1e-18)
    assert result["proposed_collector_x_m"]==pytest.approx([0.,.013])
    assert result["proposed_main_chamber_start_x_m"]==pytest.approx(.013)
    assert result["unchanged_convergent_start_x_m"]==.03 and result["unchanged_throat_and_divergent_stations"]
    assert result["conservative_head_face_land_width_m"]==pytest.approx(.037)
    assert result["front_supply_to_chamber_outer_clearance_m"]>0
    assert result["remaining_collector_to_chamber_inner_land_m"]==.001
    assert result["native_geometry"]=="NOT_GENERATED" and not result["installed"]
    assert result["joint_status"].startswith("INCOMPLETE") and len(result["native_requirements"])==5
    assert spec==source()


@pytest.mark.parametrize("key,value",[("mount_outer_radius_m",float("nan")),("bolt_count",True),("bolt_count",2),
    ("collector_plenum_outer_radius_m",.037),("bolt_circle_radius_m",.056),("mount_outer_radius_m",.064)])
def test_layout_rejects_unsupported_dimensions_blocked_supply_and_ligaments(key,value):
    spec=source()
    with pytest.raises(ValueError):prepare_layout(spec,inspect(spec),{**proposal(),key:value})


def test_stale_source_hidden_allowable_and_unconnected_head_are_not_accepted():
    spec=source();read=inspect(spec)
    with pytest.raises(ValueError):prepare_layout(spec,{**read,"source_graph_id":"wrong"},proposal())
    with pytest.raises(ValueError):prepare_layout(spec,read,{**proposal(),"allowable_pa":1e9})
    other=source();other["features"][-1]["parameters"]["phase"]["value"]+=.2
    with pytest.raises(ValueError,match="already match"):prepare_layout(other,inspect(other),proposal())
