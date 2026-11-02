from copy import deepcopy

import pytest

from systems.geometry.driving_constraints import SCHEMA,resolve
from systems.geometry.component_model import compile_model
from tests.fixtures.component_geometry import model


def constrained(rules):
    spec=model("pipe.circular");spec["constraints"]={"schema":SCHEMA,"rules":rules};return spec


def ref(key):return {"feature":model("pipe.circular")["features"][0]["id"],"parameter":key}


def rule(target,source=None,**extra):
    return {"id":target,"type":"affine","target":ref(target),"source":ref(source),"factor":1.,"offset":{"value":0.,"unit":"m"},**extra} if source else {"id":target,"type":"fixed","target":ref(target),"value":{"value":.04,"unit":"m"},**extra}


def test_fixed_dimension_regenerates_real_feature_plan_without_mutating_source():
    spec=constrained([rule("length",value={"value":.065,"unit":"m"})]);before=deepcopy(spec)
    resolved=resolve(spec);assert resolved["specification"]["features"][0]["parameters"]["length"]["value"]==.065
    assert spec==before
    plan=compile_model(spec,"engine-component-constraint-test","r1","2026-10-24T00:00:00Z")
    assert plan.parts[0].profile[-1][0]==pytest.approx(.065)


def test_affine_dependencies_solve_in_topological_order_and_react_to_driver_edits():
    spec=constrained([rule("length","wall_thickness",factor=10,offset={"value":.01,"unit":"m"}),rule("wall_thickness",value={"value":.002,"unit":"m"})])
    assert resolve(spec)["specification"]["features"][0]["parameters"]["length"]["value"]==pytest.approx(.03)
    spec["constraints"]["rules"][1]["value"]["value"]=.003
    assert resolve(spec)["specification"]["features"][0]["parameters"]["length"]["value"]==pytest.approx(.04)


def test_diameter_drives_radius_not_arbitrary_length():
    spec=constrained([rule("bore_radius",type="diameter",value={"value":.008,"unit":"m"})]);assert resolve(spec)["specification"]["features"][0]["parameters"]["bore_radius"]["value"]==.004
    spec["constraints"]["rules"][0]["target"]=ref("length")
    with pytest.raises(ValueError,match="radial"):resolve(spec)


@pytest.mark.parametrize("rules",[
    [rule("length","wall_thickness"),rule("wall_thickness","length")],
    [rule("length"),rule("length",id="duplicate")],
    [rule("length",value={"value":40,"unit":"mm"})],
    [rule("missing")],
    [rule("length",value={"value":float("inf"),"unit":"m"})],
    [rule("length","wall_thickness",factor="__import__('os')")],
])
def test_conflicts_cycles_bad_units_and_code_like_input_are_rejected(rules):
    with pytest.raises(ValueError):resolve(constrained(rules))


def test_constraints_remain_in_resolved_source_and_idempotently_re_evaluate():
    spec=constrained([rule("length")]);first=resolve(spec)["specification"];assert first["constraints"]==spec["constraints"]
    assert resolve(first)["specification"]==first


def test_no_rules_preserves_existing_model_and_method_identity():
    spec=model("pipe.circular");assert resolve(spec)["specification"]==spec;assert resolve(spec)["report"]["rule_count"]==0


def test_same_parent_frame_origin_offset_is_explicit_local_coordinate_constraint():
    spec=constrained([]);world=deepcopy(spec["frames"][0]);a={**world,"id":"a","parent":"world"};b=deepcopy(a);b["id"]="b";a["origin"][0]["value"]=.02
    spec["frames"] += [a,b];spec["constraints"]["rules"]=[{"id":"axial-gap","type":"affine","target":{"frame":"b","axis":"x"},"source":{"frame":"a","axis":"x"},"factor":1,"offset":{"value":.003,"unit":"m"}}]
    assert resolve(spec)["specification"]["frames"][-1]["origin"][0]["value"]==pytest.approx(.023)
    spec["frames"][-1]["parent"]="a"
    with pytest.raises(ValueError,match="common parent"):resolve(spec)


def test_driving_rules_cannot_bypass_exact_hydraulic_diameter_binding(monkeypatch):
    from systems.geometry import component_authority as authority
    spec=model("injector.biprop_doublet");p=spec["features"][0]["parameters"]
    expected={key:deepcopy(p[key]) for key in ("fuel_hole_radius","oxidizer_hole_radius","count")}
    monkeypatch.setattr(authority,"injector_dimensions",lambda design:(expected,"synthetic-source-binding-test"))
    authority.validate_injector_binding(object(),spec)
    spec["constraints"]={"schema":SCHEMA,"rules":[{"id":"illegal-independent-resize","type":"fixed","target":{"feature":spec["features"][0]["id"],"parameter":"fuel_hole_radius"},"value":{"value":.0009,"unit":"m"}}]}
    with pytest.raises(authority.InvalidRecord,match="exact CURRENT hydraulic"):authority.validate_injector_binding(object(),spec)


def test_fractional_count_rule_is_not_silently_rounded():
    spec=model("injector.showerhead");spec["constraints"]={"schema":SCHEMA,"rules":[{"id":"count","type":"fixed","target":{"feature":"body","parameter":"count"},"value":{"value":3.5,"unit":"1"}}]}
    with pytest.raises(ValueError,match="exact integers"):resolve(spec)
