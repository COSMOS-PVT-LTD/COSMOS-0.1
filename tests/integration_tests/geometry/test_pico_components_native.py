"""Real PicoGK component construction, field/mesh round trip and independent QA."""
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.pico_components import PicoComponentAdapter, field_graph, fields
from systems.contracts.geometry import BuildState
from systems.geometry.component_model import compile_model
from systems.geometry.component_reference import PartReference
from systems.geometry.pico_component_builds import (
    PicoBuildService,
    PicoLimits,
    PicoReference,
)
from tests.fixtures.component_geometry import model, plan
from tests.unit_tests.systems_layer.test_pico_components import qa, request_for


def command():
    value=os.environ.get("PICO_COMPONENT_RUNTIME_ROOT")
    if not value:pytest.skip("Explicit pinned PicoGK component native campaign required")
    root=Path(value).resolve()
    return WorkerCommand((str(root/"dotnet9/dotnet"),str(root/"worker/PicoComponents.dll")),(("DOTNET_ROOT",str(root/"dotnet9")),("DOTNET_CLI_TELEMETRY_OPTOUT","1")))


@pytest.mark.parametrize("kind",["profile.wall","profile.solid","cooling.axial_sector","injector.showerhead","injector.doublet","injector.biprop_radial_doublet","injector.coaxial","injector.pintle","manifold.dual_annular","manifold.cooling_annular","manifold.cooling_front_supply","interface.bolted_flange","five-grooved-bolted-injector","pipe.circular","pipe.elbow"])
def test_cross_language_field_recipe_matches_independent_python(kind):
    if kind=="profile.solid":
        spec=model();spec["features"][0]["operation"]="profile.solid"
        for k,v in spec["features"][0]["parameters"].items():
            if k.startswith("inner"):v["value"]=0
        p=compile_model(spec,"engine-component-solid-qa","solid-qa","2026-10-24T00:00:00Z")
    else:p=plan(kind)
    c=command();rng=np.random.default_rng(712)
    for part,data in zip(p.parts,fields(p),strict=True):
        ref=PartReference(p,part);bounds=ref.bounds_m
        samples=rng.uniform(bounds[:3]-.001,bounds[3:]+.001,size=(256,3))
        proc=subprocess.run([*c.argv,"--sample"],input=json.dumps({"part":data,"points":samples.tolist()}).encode(),capture_output=True,timeout=15,check=False,env={**os.environ,**dict(c.environment)})
        assert proc.returncode==0,proc.stdout.decode()+proc.stderr.decode()
        assert np.allclose(json.loads(proc.stdout),ref.sdf(samples),atol=1e-12,rtol=1e-10)


@pytest.mark.parametrize("kind",["profile.wall","cooling.axial_sector","injector.showerhead","injector.doublet","injector.biprop_doublet","injector.biprop_radial_doublet","injector.triplet","injector.coaxial","injector.pintle","manifold.dual_annular","manifold.cooling_annular","manifold.cooling_front_supply","interface.bolted_flange","interface.bolt_pattern","interface.face_groove","five-grooved-bolted-injector","pipe.circular","pipe.elbow"])
def test_actual_implicit_component_generation_and_independent_mesh_qa(tmp_path,kind):
    p=plan(kind);h=.0003125 if kind=="cooling.axial_sector" else .0005 if kind=="profile.wall" else .00025;r=request_for(p,h);c=command()
    with WorkerSupervisor(timeout_s=120) as supervisor:
        service=PicoBuildService(PicoComponentAdapter("picogk",c,supervisor,enabled=True),tmp_path,PicoLimits.from_spec(qa(h)))
        try:
            _,future=service.submit(r,p.snapshot,field_graph(p),PicoReference(p))
            candidate=future.result(timeout=160)
            assert candidate.record.state is BuildState.ACCEPTED,candidate.evidence_json
            proof=json.loads(candidate.evidence_json)
            assert proof["qa-stl"]["pass"] and proof["worker_observations"]["native_allocations_after"]==0
            assert 0<proof["worker_observations"]["zero_isovalue_max_bound_m"]<1e-12
            assert candidate.record.artifacts[0].representation.value=="implicit_field"
            assert (candidate.directory/"source.vdb").is_file()
        finally:service.close()


@pytest.mark.parametrize("h",[.0002,.000125])
def test_grid_aligned_pintle_caps_remain_closed_without_mesh_welding(tmp_path,h):
    p=plan("injector.pintle");c=command()
    with WorkerSupervisor(timeout_s=120) as supervisor:
        s=PicoBuildService(PicoComponentAdapter("picogk",c,supervisor,enabled=True),tmp_path,PicoLimits.from_spec(qa(h)))
        try:
            _,f=s.submit(request_for(p,h),p.snapshot,field_graph(p),PicoReference(p));candidate=f.result(timeout=160)
            assert candidate.record.state is BuildState.ACCEPTED,candidate.evidence_json
            proof=json.loads(candidate.evidence_json)
            assert all(p["components"]==1 and p["nonmanifold_edges"]==0 for p in proof["qa-stl"]["parts"])
            if h==.000125:assert proof["worker_observations"]["triangle_count"]>200_000
        finally:s.close()


def test_three_resolution_pipe_study_records_convergence(tmp_path,record_property):
    rows=[];p=plan("pipe.circular");c=command()
    with WorkerSupervisor(timeout_s=120) as supervisor:
        for i,h in enumerate((.0005,.00025,.000125)):
            root=tmp_path/str(i);root.mkdir();s=PicoBuildService(PicoComponentAdapter("picogk",c,supervisor,enabled=True),root,PicoLimits.from_spec(qa(h)))
            try:
                _,f=s.submit(request_for(p,h),p.snapshot,field_graph(p),PicoReference(p));candidate=f.result(timeout=160)
                evidence=json.loads(candidate.evidence_json);part=evidence["qa-stl"]["parts"][0]
                rows.append({"voxel_m":h,"state":candidate.record.state.value,"relative_volume_error":part["relative_volume_error"],"forward_max_m":part["forward_max_m"],"reverse_max_m":part["reverse_max_m"],"native_seconds":evidence["process"]["elapsed_s"],"observed_native_rss":evidence["process"]["observed_rss_bytes"]})
            finally:s.close()
    record_property("resolution_study",json.dumps(rows))
    assert rows[-1]["state"]=="accepted" and rows[-1]["relative_volume_error"]<rows[0]["relative_volume_error"]
    assert rows[-1]["forward_max_m"]<rows[0]["forward_max_m"]


def test_native_timeout_cannot_publish_candidate(tmp_path):
    p=plan("profile.wall");c=command();r=request_for(p)
    with WorkerSupervisor(timeout_s=.05) as supervisor:
        adapter=PicoComponentAdapter("picogk",c,supervisor,enabled=True)
        result=adapter.build("pico-timeout",r,p.snapshot,field_graph(p),tmp_path).result(timeout=5)
        assert result.code=="TIMEOUT"
        with pytest.raises(ValueError):adapter.decode(result,r,tmp_path)
