"""Distinct implicit component intent and strict numerical admission."""
import json
from dataclasses import replace

import numpy as np
import pytest

from plugins.geometry.pico_components import VERSION, field_graph, fields, validate
from systems.contracts.geometry import (
    GeometryBuildRequest,
    OutputFormat,
    Representation,
)
from systems.geometry.pico_component_builds import PicoLimits
from tests.fixtures.component_geometry import plan


def request_for(p,h=.00025):
    g=field_graph(p);values={v.name:v.value_si for v in p.snapshot.parameters_si}
    return GeometryBuildRequest("pico-request",p.snapshot.snapshot_id,g.graph_id,g.content_sha256,"picogk",VERSION,Representation.IMPLICIT_FIELD,"sparse_volume",values["source_tolerance"],values["export_tolerance"],h,(OutputFormat.STL,),"world","pico-correlation")


def qa(h=.00025):
    return {"voxel_resolution":{"value":h,"unit":"m"},"relative_volume":{"value":.05,"unit":"1"},"centroid":{"value":.001,"unit":"m"},"forward_residual":{"value":.001,"unit":"m"},"reverse_distance":{"value":.001,"unit":"m"},"source":"Predeclared synthetic software geometry QA only; not engine manufacturing tolerances"}


def test_implicit_derivation_does_not_mutate_or_relabel_analytic_source():
    p=plan();before=p.graph.to_json();g=field_graph(p)
    assert p.graph.to_json()==before and g.content_sha256!=p.graph.content_sha256
    assert all(f.representation is Representation.IMPLICIT_FIELD for f in g.features)
    assert validate(request_for(p),p.snapshot,g).parts==p.parts


@pytest.mark.parametrize("kind",["profile.wall","cooling.axial_sector","injector.coaxial","manifold.dual_annular","pipe.elbow"])
def test_complete_source_field_recipe_and_part_frames(kind):
    p=plan(kind);value=fields(p)
    assert [v["part_id"] for v in value]==[v.part_id for v in p.parts]
    assert all(np.isfinite(v["bounds_m"]).all() and len(v["rotation"])==9 for v in value)
    parsed=json.loads(json.dumps(value,allow_nan=False))
    assert parsed[0]["profile"]==[list(row) for row in p.parts[0].profile]


@pytest.mark.parametrize("change",[{"backend_id":"occt"},{"output_formats":(OutputFormat.STEP,)},{"representation":Representation.ANALYTIC_BREP},{"voxel_resolution_m":None},{"voxel_resolution_m":1e-6}])
def test_wrong_representation_format_backend_or_resolution_rejected(change):
    p=plan()
    with pytest.raises(ValueError):validate(replace(request_for(p),**change),p.snapshot,field_graph(p))


def test_explicit_voxel_qa_and_units():
    assert PicoLimits.from_spec(qa()).voxel_m==.00025
    bad=qa();bad["voxel_resolution"]["unit"]="mm"
    with pytest.raises(ValueError):PicoLimits.from_spec(bad)
    with pytest.raises(ValueError):PicoLimits.from_spec({})


def test_field_capacity_rejects_fine_large_render_without_worker():
    p=plan()
    with pytest.raises(ValueError,match="120M"):validate(request_for(p,2.5e-5),p.snapshot,field_graph(p))


def test_display_flap_cleanup_is_combinatorial_not_original_mesh_conditioning():
    from plugins.geometry.display_encoding import remove_dangling_display_flaps
    vertices=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[.5,-.2,0]],dtype=np.float32)
    closed=vertices[[[0,2,1],[0,1,3],[1,2,3],[2,0,3]]];damaged=np.concatenate((closed,vertices[[[0,1,4]]]))
    before=damaged.copy();result,count=remove_dangling_display_flaps(damaged)
    assert count==1 and np.array_equal(result,closed) and np.array_equal(damaged,before)
    assert remove_dangling_display_flaps(closed)[1]==0
    assert remove_dangling_display_flaps(closed[:1])[1]==0


def test_pico_byte_inspection_keeps_its_explicit_separate_artifact_limit(monkeypatch):
    from types import SimpleNamespace

    from plugins.geometry import pico_components as module
    calls=[]
    monkeypatch.setattr(module,"checked_file",lambda *a,**k:calls.append((a,k)) or "verified")
    adapter=object.__new__(module.PicoComponentAdapter)
    assert adapter.inspect("owned",SimpleNamespace(name="export.stl",sha256="1"*64))=="verified"
    assert calls==[(("owned","export.stl","1"*64),{"max_bytes":256*1024**2})]
