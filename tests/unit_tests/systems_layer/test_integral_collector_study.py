import math
from copy import deepcopy

import pytest

from systems.geometry.component_interfaces import inspect_interfaces
from systems.geometry.integral_collector_study import prepare_probe
from systems.geometry.separable_head_cad import prepare_cad
from tests.unit_tests.systems_layer.test_separable_head_cad import compile, inputs


def candidate():
    original,layout,settings=inputs()
    spec,_,_=prepare_cad(original,inspect_interfaces(compile(original),1e-6),layout,settings)
    plan=compile(spec);return spec,plan,inspect_interfaces(plan,1e-6)


def test_integral_probe_preserves_source_sections_and_accounts_for_contact_and_voids():
    _,plan,read=candidate();original=deepcopy(read)
    result=prepare_probe(plan,read,collector_id="collector-mount-bolts",chamber_id="channels")
    # Analytic annulus minus four actual sector openings, not sampled contact.
    expected=math.pi*(.030**2-.026**2)-4*.3/2*(.028**2-.027**2)
    assert result["expected_contact_area_m2"]==pytest.approx(expected,rel=1e-14)
    assert len(result["fluid_profiles"])==9 and len(result["fluid_holes"])==1
    assert result["expected_fused_metal_volume_m3"]==pytest.approx(sum(v["volume_m3"] for v in result["expected_parts"]),rel=1e-14)
    assert result["gas_wall_minimum_radial_thickness_m"]==pytest.approx(.0005)
    assert result["expected_connected_fluid_volume_m3"]>0
    assert result["material_partition"].startswith("NOT_DESIGNED") and result["physical_validation"]=="NOT_PERFORMED"
    assert read==original


def test_probe_rejects_stale_source_missing_mates_and_unrelated_parts():
    _,plan,read=candidate()
    for changed in ({**read,"source_graph_id":"stale"},{**read,"matches":[]}):
        with pytest.raises(ValueError):prepare_probe(plan,changed,collector_id="collector-mount-bolts",chamber_id="channels")
    for header,wall in (("head-mount-bolts","channels"),("collector-mount-bolts","fuel-supply"),("missing","channels")):
        with pytest.raises(ValueError):prepare_probe(plan,read,collector_id=header,chamber_id=wall)


def test_probe_does_not_bridge_a_gap_or_invent_a_changed_gas_bore():
    spec,_,_=candidate()
    for change in ("gap","bore"):
        modified=deepcopy(spec)
        if change=="gap":next(f for f in modified["frames"] if f["id"]=="header")["origin"][0]["value"]-=.001
        else:next(f for f in modified["features"] if f["id"]=="header")["parameters"]["bore_radius"]["value"]-=.001
        plan=compile(modified)
        with pytest.raises(ValueError,match="coincident"):
            prepare_probe(plan,inspect_interfaces(plan,1e-6),collector_id="collector-mount-bolts",chamber_id="channels")
