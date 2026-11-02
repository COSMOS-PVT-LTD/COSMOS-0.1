import math
from copy import deepcopy

import numpy as np
import pytest

from systems.geometry.component_cooling import geometry_handoff
from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.projects.authority import StoreUnavailable
from tests.fixtures.component_geometry import model, plan


def test_actual_fluid_domains_match_separately_implemented_cad_volume_reference():
    p = plan("cooling.axial_sector")
    report = geometry_handoff(p)
    passage = report["passages"][0]
    fluids = [PartReference(p, part).volume_m3 for part in p.parts if part.sector]
    assert len(fluids) == passage["channel_count"]
    assert all(v == pytest.approx(passage["volume_per_channel_m3"], rel=1e-13) for v in fluids)
    assert sum(fluids) == pytest.approx(passage["total_channel_volume_m3"], rel=1e-13)
    assert len(passage["stations"]) == 5 and len(passage["segments"]) == 4
    assert passage["segments"][1]["shape"] == "CONVERGING"
    assert passage["segments"][-1]["shape"] == "DIVERGING"
    assert not report["thermally_sized"] and report["thermal_mapping"] == "UNSUPPORTED_SECTOR_TO_RECTANGULAR"
    assert report["physical_validation"] == "NOT_PERFORMED"


def test_cylindrical_lateral_surfaces_and_volume_independent_closed_forms():
    value = model("cooling.axial_sector")
    rows = value["features"][0]["parameters"]
    for i in range(5):
        rows["inner" + str(i)]["value"] = .02
        rows["outer" + str(i)]["value"] = .024
    p = compile_model(value, "engine-component-cylinder", "r1", "2026-10-21T00:00:00Z")
    passage = geometry_handoff(p)["passages"][0]
    a, b, theta, length = .021, .022, .3, .08
    assert passage["volume_per_channel_m3"] == pytest.approx(theta * (b*b-a*a) * length / 2, rel=1e-14)
    segments = passage["segments"]
    assert sum(s["inner_lateral_area_per_channel_m2"] for s in segments) == pytest.approx(theta * a * length)
    assert sum(s["outer_lateral_area_per_channel_m2"] for s in segments) == pytest.approx(theta * b * length)
    assert sum(s["radial_side_area_per_channel_m2"] for s in segments) == pytest.approx(2 * (b-a) * length)


def test_segment_volumes_against_dense_axial_quadrature():
    passage = geometry_handoff(plan("cooling.axial_sector"))["passages"][0]
    for start, end, segment in zip(passage["stations"], passage["stations"][1:], passage["segments"], strict=False):
        x = np.linspace(start["x_m"], end["x_m"], 10001)
        inner = np.linspace(start["channel_inner_radius_m"], end["channel_inner_radius_m"], len(x))
        outer = inner + passage["radial_depth_m"]
        areas = passage["angular_width_rad"] * (outer**2-inner**2) / 2
        numeric = np.sum((areas[1:]+areas[:-1]) * np.diff(x) / 2)
        assert segment["volume_per_channel_m3"] == pytest.approx(numeric, rel=1e-12)


def test_unexported_voids_and_rigid_placement_do_not_remove_or_resize_passages():
    value = model("cooling.axial_sector", fluids=False)
    p = compile_model(value, "engine-component-nofluid", "r1", "2026-10-21T00:00:00Z")
    original = geometry_handoff(p)["passages"][0]
    assert not original["fluid_domains_exported"] and original["total_channel_volume_m3"] > 0
    changed = deepcopy(value)
    changed["frames"].append({"id":"rotated", "parent":"world", "origin":[{"value": v,"unit":"m"} for v in (.1,.2,.3)],
                               "rotation":[0.,-1.,0.,1.,0.,0.,0.,0.,1.]})
    changed["features"].append({"id":"placed", "operation":"placement.rigid", "frame":"rotated", "depends_on":["channels"], "parameters":{}})
    changed["outputs"] = ["placed"]
    moved = geometry_handoff(compile_model(changed, p.snapshot.project_id, "r2", "2026-10-21T00:00:00Z"))["passages"][0]
    for key in ("volume_per_channel_m3", "total_channel_volume_m3", "stations", "segments"):
        assert moved[key] == original[key]
    assert moved["frame_id"] == "rotated"


def test_changed_channel_width_changes_handoff_and_uncut_model_has_none():
    value = model("cooling.axial_sector")
    value["features"][1]["parameters"]["width"]["value"] *= 2
    changed = geometry_handoff(compile_model(value, "engine-component-changed", "r2", "2026-10-21T00:00:00Z"))
    original = geometry_handoff(plan("cooling.axial_sector"))
    assert changed["passages"][0]["total_channel_volume_m3"] == pytest.approx(2 * original["passages"][0]["total_channel_volume_m3"])
    assert not math.isclose(changed["passages"][0]["minimum_axial_hydraulic_diameter_m"], original["passages"][0]["minimum_axial_hydraulic_diameter_m"])
    empty = geometry_handoff(plan())
    assert empty["passages"] == [] and empty["thermal_mapping"] == "NO_SECTOR_PASSAGES"


def test_loaded_analysis_cannot_claim_new_on_disk_method_hashes(monkeypatch):
    from systems.geometry import component_cooling
    monkeypatch.setattr(component_cooling, "method_sources", lambda: {"changed": "0" * 64})
    with pytest.raises(StoreUnavailable, match="changed after loading"):
        component_cooling.geometry_handoff(plan("cooling.axial_sector"))
