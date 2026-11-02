"""Actual authorized CAD-tool routes; native cases require an explicit campaign."""
import os
from copy import deepcopy
from uuid import uuid4

import pytest

from systems.geometry.driving_constraints import SCHEMA
from tests.fixtures.component_geometry import qa_spec
from tests.integration_tests.gui.test_component_projects_http import capture, compose
from tests.integration_tests.gui.test_engine_nozzle_projects_http import wait
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa:F401
)


def test_driving_constraint_preview_save_history_and_no_implicit_write(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        _project,_baseline,root,command,saved=capture(app,base,client,"pipe.circular")
        spec=deepcopy(command["specification"]);feature=spec["features"][0]["id"]
        spec["constraints"]={"schema":SCHEMA,"rules":[{"id":"axial-length","type":"fixed","target":{"feature":feature,"parameter":"length"},"value":{"value":.065,"unit":"m"}}]}
        before=saved["authority"]["commit_id"]
        preview=request(client,base,root+"/cad-tools/constraints",{"specification":spec})
        assert not preview["persisted"] and preview["body_count"]==1
        uri=root+"/component-geometry/"+saved["authority"]["object_id"]
        assert request(client,base,uri)["authority"]["commit_id"]==before
        assert preview["resolved_specification"]["features"][0]["parameters"]["length"]["value"]==.065
        posted={**command,"expected":saved["authority"]["head"],"operation_id":str(uuid4()),"specification":spec}
        result=request(client,base,uri,posted)
        assert result["model"]["specification"]["constraints"]==spec["constraints"]
        assert result["model"]["specification"]["features"][0]["parameters"]["length"]["value"]==.065
        assert request(client,base,uri+"?commit="+before)["model"]["specification"]==command["specification"]
        request(client,base,uri,posted|{"operation_id":str(uuid4())},expected=409)
        bad=deepcopy(spec);bad["constraints"]["rules"]*=2
        request(client,base,root+"/cad-tools/constraints",{"specification":bad},expected=400)


def test_native_runtime_is_explicitly_disabled_without_qualification(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        project=new_project(base,client);app.project_api.cad_tools.path=None
        value=request(client,base,"/api/projects/"+project["project_id"]+"/cad-tools/capabilities")
        assert not value["enabled"] and value["driving_constraints"]


def test_occt_only_profile_does_not_attempt_or_enable_combined_fixture_runtime(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        app.ngg_enabled=True;app.component_only_runtime=True
        value=request(client,base,"/api/ngg/context",expected=404)
        assert value["error"]["code"]=="FIXTURE_PROFILE_DISABLED"
        with client.open(base+"/app/workbench/native-geometry") as response:html=response.read()
        assert b'PicoGK disabled by the separately qualified OCCT-only' in html
        assert b'<script src="/assets/ngg/view.js"></script>' not in html


def test_real_native_clearance_drawing_and_project_boundary(tmp_path):
    cfg=os.environ.get("CAD_TOOLS_CONFIG")
    if not cfg:pytest.skip("Explicit separately qualified native CAD tools campaign required")
    with running(tmp_path/"state") as (app,base,client):
        compose(app);app.project_api.cad_tools.path=cfg
        _project,_,root,_command,saved=capture(app,base,client,"injector.coaxial")
        start=request(client,base,root+"/component-geometry-builds",{"model_commit_id":saved["authority"]["commit_id"],"expected_model":saved["authority"]["head"],"qa_specification":qa_spec(),"output_formats":["step","stl"],"operation_id":str(uuid4())})
        path=root+"/component-geometry-builds/"+start["object_id"]+"/jobs/"+start["job_id"]
        job=wait(client,base,path);assert job["state"]=="COMPLETED",job
        context=request(client,base,path+"/review-context");a,b=[p["part_id"] for p in context["parts"]]
        native=root+"/cad-tools/jobs/"+job["job_id"]
        query=f"?a={a}&b={b}&linear_tolerance_m=1e-8&volume_resolution_m3=1e-15&required_clearance_m=0.0001"
        value=request(client,base,native+"/clearance"+query)
        assert value["inspection"]["relation"]=="DISJOINT"
        assert value["source"]["source_sha256"]==context["artifact_sha256"]["source.brep"]
        assert value["inspection"]["minimum_distance_m"]>0
        request(client,base,native+"/clearance"+query+"&a="+a,expected=400)
        request(client,base,native+"/clearance"+query.replace("linear_tolerance_m=1e-8","linear_tolerance_m=NaN"),expected=400)
        from urllib.parse import urlencode
        declaration={"part_id":a,"title":"Synthetic test part - not hardware approval","number":"QA1","revision":"A","author":"Software test","material":"NOT SPECIFIED","process":"NOT SPECIFIED","tolerance_note":"NOT SPECIFIED","finish_note":"NOT SPECIFIED","scale_denominator":1,"curve_deflection_m":1e-5}
        raw=binary(client,base,native+"/drawing.pdf?"+urlencode(declaration))
        assert raw.startswith(b"%PDF-")
        svg=binary(client,base,native+"/drawing.svg?"+urlencode(declaration));assert b"UNRELEASED" in svg
        report=request(client,base,native+"/drawing.json?"+urlencode(declaration))
        assert report["source"]["job_id"]==job["job_id"] and len(report["drawing"]["views"])==3
        with client.open(base+native+"/drawing.json?"+urlencode(declaration),timeout=15) as response:
            assert "attachment" in response.headers["Content-Disposition"]
            assert "COSMOS-source-bound-unreleased-" in response.headers["Content-Disposition"]
            assert response.headers["X-COSMOS-Scope"]=="source-bound-unreleased-drawing-not-manufacturing-or-physical-acceptance"
        request(client,base,native+"/drawing.pdf?"+urlencode(declaration|{"scale_denominator":0}),expected=400)
        foreign=new_project(base,client)
        request(client,base,"/api/projects/"+foreign["project_id"]+"/cad-tools/jobs/"+job["job_id"]+"/clearance"+query,expected=404)


def test_changed_driving_dimension_reaches_native_rebuild(tmp_path):
    if not os.environ.get("CAD_TOOLS_CONFIG"):
        pytest.skip("Explicit separately qualified native CAD tools campaign required")
    with running(tmp_path/"state") as (app,base,client):
        compose(app)
        _,_,root,command,saved=capture(app,base,client,"pipe.circular")
        spec=deepcopy(command["specification"]);feature=spec["features"][0]["id"]
        spec["constraints"]={"schema":SCHEMA,"rules":[{"id":"native-length","type":"fixed","target":{"feature":feature,"parameter":"length"},"value":{"value":.065,"unit":"m"}}]}
        uri=root+"/component-geometry/"+saved["authority"]["object_id"]
        result=request(client,base,uri,{**command,"expected":saved["authority"]["head"],"operation_id":str(uuid4()),"specification":spec})
        start=request(client,base,root+"/component-geometry-builds",{"model_commit_id":result["authority"]["commit_id"],"expected_model":result["authority"]["head"],"qa_specification":qa_spec(),"output_formats":["step","stl"],"operation_id":str(uuid4())})
        path=root+"/component-geometry-builds/"+start["object_id"]+"/jobs/"+start["job_id"]
        job=wait(client,base,path);assert job["state"]=="COMPLETED",job
        context=request(client,base,path+"/review-context");part=context["parts"][0]
        assert part["bounds_m"][3]-part["bounds_m"][0]==pytest.approx(.065,abs=1e-6)
        assert result["model"]["specification"]["constraints"]==spec["constraints"]
