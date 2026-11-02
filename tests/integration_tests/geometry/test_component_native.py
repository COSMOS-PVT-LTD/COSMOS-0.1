"""Explicit optional real component worker, no mock geometry/hardware claims."""

import json
import os
import time
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.component_adapter import ComponentAdapter
from systems.contracts.geometry import (
    GeometryBuildRequest,
    OutputFormat,
    Representation,
)
from systems.geometry.component_model import VERSION
from systems.geometry.component_reference import PartReference
from tests.fixtures.component_geometry import plan, qa_spec
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def commands():
    path=os.environ.get("R07_COMPONENT_CONFIG")
    if not path: pytest.skip("Explicit pinned component native campaign required; no autodetection")
    cfg=json.loads(Path(path).read_bytes()); root=Path(__file__).resolve().parents[3]
    return WorkerCommand((cfg["occt"]["argv"][0],str(root/"plugins/geometry/workers/component_worker.py")),tuple(cfg["occt"]["environment"].items()))


def request_for(value):
    values={p.name:p.value_si for p in value.snapshot.parameters_si}
    return GeometryBuildRequest("component-request",value.snapshot.snapshot_id,value.graph.graph_id,value.graph.content_sha256,"occt",VERSION,Representation.ANALYTIC_BREP,"none",values["source_tolerance"],values["export_tolerance"],None,(OutputFormat.STEP,OutputFormat.STL),"world","component-correlation")


@pytest.mark.parametrize("kind",["profile.wall","pipe.circular","pipe.elbow","cooling.axial_sector","injector.showerhead","injector.doublet","injector.biprop_doublet","injector.biprop_radial_doublet","manifold.dual_annular","manifold.cooling_annular","manifold.cooling_front_supply","interface.bolted_flange","interface.bolt_pattern","interface.face_groove","bolted-injector","grooved-bolted-injector","five-grooved-bolted-injector","injector.triplet","injector.coaxial","injector.pintle"])
def test_actual_component_worker_builds_each_supported_family(tmp_path,kind):
    value=plan(kind); request=request_for(value)
    with WorkerSupervisor(timeout_s=120) as supervisor:
        adapter=ComponentAdapter("occt",commands(),supervisor,enabled=True)
        result=adapter.build("component-native",request,value.snapshot,value.graph,tmp_path).result(timeout=130)
        response=adapter.decode(result,request,tmp_path)
        assert len(response.exports)==2 and len(response.metrics["parts"])==len(value.parts)
        for part,actual in zip(value.parts,response.metrics["parts"],strict=True):
            ref=PartReference(value,part)
            assert actual["part_id"]==part.part_id
            assert actual["volume_m3"]==pytest.approx(ref.volume_m3,rel=1e-8)
            assert actual["centroid_m"]==pytest.approx(ref.centroid_m,abs=1e-9)
            assert actual["faces"]
            assert not {f["semantic"] for f in actual["faces"]} & {"UNRESOLVED","AMBIGUOUS"}, actual["faces"]
            if kind in {"injector.biprop_doublet","injector.biprop_radial_doublet"}:
                semantics={f["semantic"] for f in actual["faces"]}
                assert sum(name.startswith("injector-fuel-port-") for name in semantics)==3
                assert sum(name.startswith("injector-oxidizer-port-") for name in semantics)==3
            if kind=="manifold.dual_annular":
                semantics={f["semantic"] for f in actual["faces"]}
                for name in ("fuel","oxidizer"):
                    assert any(s.startswith("manifold-"+name+"-plenum.") for s in semantics)
                    assert sum(s.startswith("manifold-"+name+"-inlet-port-") for s in semantics)==1
                    assert sum(s.startswith("manifold-"+name+"-outlet-port-") for s in semantics)==3


@pytest.mark.parametrize("kind",["profile.wall","pipe.circular","pipe.elbow","cooling.axial_sector","injector.showerhead","injector.doublet","injector.biprop_doublet","injector.biprop_radial_doublet","manifold.dual_annular","manifold.cooling_annular","manifold.cooling_front_supply","interface.bolted_flange","interface.bolt_pattern","interface.face_groove","bolted-injector","grooved-bolted-injector","five-grooved-bolted-injector","injector.triplet","injector.coaxial","injector.pintle"])
def test_actual_component_independent_step_stl_topology_semantics_and_formulas(tmp_path,kind):
    from systems.contracts.geometry import BuildState
    from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
    from systems.geometry.component_reference import ComponentReference
    worker=commands()
    reader=WorkerCommand((worker.argv[0],str(Path(worker.argv[1]).with_name("component_step_reader.py"))),worker.environment)
    value=plan(kind)
    with WorkerSupervisor(timeout_s=120) as supervisor:
        service=ComponentBuildService(ComponentAdapter("occt",worker,supervisor,enabled=True),tmp_path,step_reader=reader,limits=ComponentQALimits.from_spec(qa_spec()))
        try:
            _,future=service.submit(request_for(value),value.snapshot,value.graph,ComponentReference(value))
            candidate=future.result(timeout=240)
            assert candidate.record.state is BuildState.ACCEPTED,candidate.evidence_json
            evidence=json.loads(candidate.evidence_json)
            assert evidence["qa-step"]["pass"] and evidence["qa-stl"]["pass"]
            assert evidence["qa-step"]["semantic_mapping_pass"]
            assert len(evidence["qa-step"]["parts"])==len(value.parts)
        finally:
            service.close()


def test_independent_reader_resolves_displaced_slender_pipes_at_large_assembly_extent(tmp_path):
    from copy import deepcopy

    from systems.contracts.geometry import BuildState
    from systems.geometry.component_model import compile_model
    from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
    from systems.geometry.component_reference import ComponentReference
    from tests.fixtures.component_geometry import model
    worker=commands();reader=WorkerCommand((worker.argv[0],str(Path(worker.argv[1]).with_name("component_step_reader.py"))),worker.environment)
    spec=model("pipe.circular");spec["features"]=[];spec["outputs"]=[]
    for name,origin,length in (("short",(-.366666666667,.05677878992845,0.),.025),
            ("fuel",(.0398143755,.04180443251876,0.),.08),("oxidizer",(-.421666666667,-.041,0.),.08)):
        feature=deepcopy(model("pipe.circular")["features"][0]);feature.update(id=name,frame=name)
        feature["parameters"]["length"]["value"]=length
        spec["features"].append(feature);spec["outputs"].append(name)
        spec["frames"].append({"id":name,"parent":"world","origin":[{"value":v,"unit":"m"} for v in origin],"rotation":[1.,0.,0.,0.,1.,0.,0.,0.,1.]})
    value=compile_model(spec,"engine-component-slender-pipe-regression","synthetic","2026-10-21T00:00:00+00:00")
    with WorkerSupervisor(timeout_s=120) as supervisor:
        service=ComponentBuildService(ComponentAdapter("occt",worker,supervisor,enabled=True),tmp_path,step_reader=reader,limits=ComponentQALimits.from_spec(qa_spec()))
        try:
            _,future=service.submit(request_for(value),value.snapshot,value.graph,ComponentReference(value))
            result=future.result(timeout=240);assert result.record.state is BuildState.ACCEPTED,result.evidence_json
            evidence=json.loads(result.evidence_json)
            assert evidence["qa-step"]["topology_pass"] and evidence["qa-stl"]["pass"]
            assert all(p["euler_characteristic"]==0 for p in evidence["qa-step"]["parts"])
        finally:service.close()


def test_independent_reader_resolves_long_header_bolt_bores_in_large_extent(tmp_path):
    from copy import deepcopy

    from systems.contracts.geometry import BuildState
    from systems.geometry.component_model import compile_model
    from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
    from systems.geometry.component_reference import ComponentReference
    from tests.fixtures.component_geometry import model
    spec=model("manifold.cooling_annular");q=lambda v,u="m":{"value":v,"unit":u}
    spec["features"][0].update(frame="header")
    spec["features"][0]["parameters"]={k:q(v) for k,v in {"bore_radius":.0514287899284541,"outer_radius":.075,
        "back_web":.004,"plenum_length":.020,"front_web":.003,"plenum_inner":.0521287899284541,
        "plenum_outer":.0614287899284541,"port_inner":.0529287899284541,"port_outer":.0554287899284541,"supply_hole_radius":.0035}.items()}
    spec["features"][0]["parameters"].update(count=q(6,"1"),width=q(.14,"rad"),phase=q(.1,"rad"),supply_phase=q(0.,"rad"))
    spec["features"].append({"id":"bolted","operation":"interface.bolt_pattern","frame":"header","depends_on":["body"],
        "parameters":{"bolt_circle_radius":q(.066),"bolt_hole_radius":q(.0032),"count":q(8,"1"),"phase":q(0.,"rad")}})
    pipe=deepcopy(model("pipe.circular")["features"][0]);pipe.update(id="pipe",frame="pipe");spec["features"].append(pipe)
    spec["frames"] += [{"id":name,"parent":"world","origin":[q(v) for v in origin],"rotation":[1.,0.,0.,0.,1.,0.,0.,0.,1.]}
        for name,origin in (("header",(-.341666666667,0.,0.)),("pipe",(.12,-.2,0.)))]
    spec["outputs"]=["bolted","pipe"]
    value=compile_model(spec,"engine-component-long-bolt-regression","synthetic","2026-10-21T00:00:00Z")
    worker=commands();reader=WorkerCommand((worker.argv[0],str(Path(worker.argv[1]).with_name("component_step_reader.py"))),worker.environment)
    with WorkerSupervisor(timeout_s=120) as supervisor:
        service=ComponentBuildService(ComponentAdapter("occt",worker,supervisor,enabled=True),tmp_path,step_reader=reader,limits=ComponentQALimits.from_spec(qa_spec()))
        try:
            _,future=service.submit(request_for(value),value.snapshot,value.graph,ComponentReference(value))
            candidate=future.result(timeout=240);assert candidate.record.state is BuildState.ACCEPTED,candidate.evidence_json
            evidence=json.loads(candidate.evidence_json)
            assert evidence["qa-step"]["topology_pass"] and evidence["qa-stl"]["pass"]
            assert {p["part_id"]:p["euler_characteristic"] for p in evidence["qa-step"]["parts"]}=={"bolted":-30,"pipe":0}
        finally:service.close()


@pytest.mark.parametrize("positioned",[False,True])
def test_real_saved_engine_chamber_throat_nozzle_internal_channels_and_fluid_domains(tmp_path,positioned):
    """Actual 81-station saved source, not a replacement toy nozzle contour."""
    from api.project_authority import principal
    from systems.geometry.component_authority import ComponentModels
    from systems.geometry.component_model import compile_model
    from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
    from systems.geometry.component_reference import ComponentReference
    from tests.fixtures.coupled_cycle import design
    from tests.integration_tests.gui.test_project_authority_http import (
        new_project,
        running,
    )
    commands()
    q=lambda v,u="m":{"value":v,"unit":u}
    with running(tmp_path/"state") as (app,base,client):
        project=new_project(base,client); actor=principal(app.auth.list_users()[0])
        source=app.project_api.service.create(actor,project["project_id"],design=design(cooling=True),operation_id="source",command_hash="1"*64)
        saved=ComponentModels(app.project_api.repository).seed(actor,project["project_id"],source.commit_id,{"wall_thickness":q(.006),"convergent_length":q(.04),"throat_land_length":q(.004),"source_tolerance":q(1e-6),"export_tolerance":q(.0002),"source":"Explicit real saved engine contour mapped to test-only CAD dimensions; NOT engineering qualification"})
    spec=saved["specification"]
    assert spec["features"][0]["parameters"]["point_count"]["value"]==84  # 81 divergent stations plus three upstream stations.
    spec["features"].append({"id":"channels","operation":"cooling.axial_sector","frame":"world","depends_on":["thrust-chamber"],"parameters":{"count":q(3,"1"),"width":q(.3,"rad"),"hot_ligament":q(.002),"depth":q(.002),"phase":q(.1,"rad"),"fluid_domains":q(1,"1")}})
    spec["outputs"]=["channels"]
    if positioned:
        spec["frames"].append({"id":"mount","parent":"world","origin":[q(.12),q(.04),q(-.03)],"rotation":[0.,0.,1.,0.,1.,0.,-1.,0.,0.]})
        spec["features"].append({"id":"placed","operation":"placement.rigid","frame":"mount","depends_on":["channels"],"parameters":{}});spec["outputs"]=["placed"]
    value=compile_model(spec,"engine-component-full-engine-test","real-contour-software-test","2026-10-20T00:00:00+00:00")
    limits=qa_spec()
    for key in ("centroid","implicit_residual","reverse_distance"): limits[key]["value"]=.0004
    worker=commands();reader=WorkerCommand((worker.argv[0],str(Path(worker.argv[1]).with_name("component_step_reader.py"))),worker.environment)
    (tmp_path/"candidate").mkdir(mode=0o700)
    with WorkerSupervisor(timeout_s=120) as supervisor:
        service=ComponentBuildService(ComponentAdapter("occt",worker,supervisor,enabled=True),tmp_path/"candidate",step_reader=reader,limits=ComponentQALimits.from_spec(limits))
        try:
            _,future=service.submit(request_for(value),value.snapshot,value.graph,ComponentReference(value))
            candidate=future.result(timeout=245)
            assert candidate.record.state.value=="accepted",candidate.evidence_json
            evidence=json.loads(candidate.evidence_json)
            assert len(evidence["qa-step"]["parts"])==4 and evidence["qa-step"]["semantic_mapping_pass"]
            assert evidence["worker_observations"]["triangle_count"]<=200000
        finally: service.close()


def test_component_actual_health_uses_pinned_native_runtime(tmp_path):
    value=plan();worker=commands()
    with WorkerSupervisor(timeout_s=60) as supervisor:
        result=ComponentAdapter("occt",worker,supervisor,enabled=True).health("component-health",request_for(value),value.snapshot,value.graph,tmp_path).result(timeout=10)
        assert result.code=="OK" and json.loads(result.stdout)["native_version"]=="7.8.1.1"


def test_component_actual_process_failure_retains_no_accepted_or_partial_cad(tmp_path):
    from systems.geometry.component_qa import ComponentBuildService, ComponentQALimits
    from systems.geometry.component_reference import ComponentReference
    value=plan();worker=commands();broken=WorkerCommand((worker.argv[0],str(tmp_path/"missing-component-worker.py")),worker.environment)
    reader=WorkerCommand((worker.argv[0],str(Path(worker.argv[1]).with_name("component_step_reader.py"))),worker.environment)
    with WorkerSupervisor(timeout_s=60) as supervisor:
        service=ComponentBuildService(ComponentAdapter("occt",broken,supervisor,enabled=True),tmp_path,step_reader=reader,limits=ComponentQALimits.from_spec(qa_spec()))
        try:
            _,future=service.submit(request_for(value),value.snapshot,value.graph,ComponentReference(value));failed=future.result(timeout=10)
            assert failed.record.state.value=="failed" and not failed.record.artifacts and not failed.record.published_artifacts
        finally: service.close()


def test_component_actual_timeout_is_not_success_or_fallback(tmp_path):
    value=plan();worker=commands()
    with WorkerSupervisor(timeout_s=.05) as supervisor:
        result=ComponentAdapter("occt",worker,supervisor,enabled=True).health("component-timeout",request_for(value),value.snapshot,value.graph,tmp_path).result(timeout=5)
        assert result.code=="TIMEOUT" and result.pid is not None


def test_component_actual_launched_process_cancellation(tmp_path):
    value=plan("cooling.axial_sector");worker=commands()
    with WorkerSupervisor(timeout_s=60) as supervisor:
        adapter=ComponentAdapter("occt",worker,supervisor,enabled=True)
        future=adapter.build("component-cancel",request_for(value),value.snapshot,value.graph,tmp_path)
        time.sleep(.08)  # Launch-boundary observation, NOT an in-kernel cooperative callback.
        assert supervisor.cancel("component-cancel")
        result=future.result(timeout=5)
        assert result.code=="CANCELLED" and result.pid is not None
        with pytest.raises(ValueError): adapter.decode(result,request_for(value),tmp_path)
