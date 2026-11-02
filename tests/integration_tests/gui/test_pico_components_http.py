"""Authorized saved intent -> genuine PicoGK -> retained originals and shared preview."""
from uuid import uuid4

from api.pico_components import PicoComponentsAPI
from api.project_authority import principal
from systems.geometry.pico_component_builds import PicoWorkspace
from tests.integration_tests.geometry.test_pico_components_native import command
from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_engine_nozzle_projects_http import wait
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pico_components import qa
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa:F401
)


def compose(app):
    c=command();cfg={"worker":{"argv":list(c.argv),"environment":dict(c.environment)},"sha256":{"explicit-native-test":"1"*64},"manifest_sha256":"2"*64}
    workspace=PicoWorkspace(app.root/"pico-native-test",lambda:cfg);app._pico_component_workspace=workspace
    app.project_api.pico_components=PicoComponentsAPI(app.project_api.repository,app._project_authority.jobs,lambda:workspace,lambda uid:principal(app.auth.get_user_by_id(uid)),app.project_api.components.models)


def test_picogk_capability_disabled_without_explicit_qualification(tmp_path):
    with running(tmp_path/"state") as (_app,base,client):
        project=new_project(base,client)
        value=request(client,base,"/api/projects/"+project["project_id"]+"/picogk-component-builds/capabilities")
        assert value["runtime_configured"] is False and value["analytic_step_available"] is False
        with client.open(base+"/assets/pico-components.js",timeout=15) as response:
            assert response.status==200
            asset=response.read()
        assert b"CosmosPicoComponents" in asset and b"Generate saved components with PicoGK" in asset


def test_real_pico_component_source_export_preview_and_scope(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        compose(app);_project,_,root,_,saved=capture(app,base,client,"pipe.circular");uri=root+"/picogk-component-builds"
        body={"model_commit_id":saved["authority"]["commit_id"],"expected_model":saved["authority"]["head"],"qa_specification":qa(),"output_formats":["stl"],"operation_id":str(uuid4())}
        start=request(client,base,uri,body);path=uri+"/"+start["object_id"]+"/jobs/"+start["job_id"]
        job=wait(client,base,path);assert job["state"]=="COMPLETED",job
        assert request(client,base,uri,body)["job_id"]==job["job_id"]
        ctx=request(client,base,path+"/mesh-context");assert ctx["representation"]=="implicit_field" and not ctx["analytic_metrology_available"]
        assert ctx["measurements"][0]["pass"]
        raw=binary(client,base,path+"/blobs/export.stl");assert b"UNITS= m" in raw[:80]
        vdb=binary(client,base,path+"/blobs/source.vdb");assert len(vdb)>0
        display=binary(client,base,path+"/preview");assert 0<len(display)<=7200000
        request(client,base,path+"/blobs/export.step",expected=400)
        bad={**body,"operation_id":str(uuid4()),"output_formats":["step"]};request(client,base,uri,bad,expected=400)
        foreign=new_project(base,client)
        request(client,base,"/api/projects/"+foreign["project_id"]+"/picogk-component-builds/"+start["object_id"]+"/jobs/"+start["job_id"]+"/mesh-context",expected=404)


def test_pico_stale_model_and_unspecified_voxel_rejected_before_admission(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        compose(app);_,_,root,_,saved=capture(app,base,client,"pipe.circular")
        settings=qa();del settings["voxel_resolution"]
        body={"model_commit_id":saved["authority"]["commit_id"],"expected_model":saved["authority"]["head"],"qa_specification":settings,"output_formats":["stl"],"operation_id":str(uuid4())}
        request(client,base,root+"/picogk-component-builds",body,expected=400)
        body["qa_specification"]=qa();body["expected_model"]={"version":0,"content_hash":"0"*64}
        request(client,base,root+"/picogk-component-builds",body|{"operation_id":str(uuid4())},expected=409)
