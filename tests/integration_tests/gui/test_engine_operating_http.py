"""Real pinned NASA coupled-model HTTP/persistence/permission qualification."""

import csv
import io
import json
from uuid import uuid4

import pytest

pytest.importorskip("cea", reason="Explicit pinned NASA CEA runtime required for operating HTTP qualification")

from api.authentication import UserRole
from api.project_authority import principal
from tests.fixtures.engine_operating import design, specification
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    command,
    new_project,
    request,
    route,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_saved_solved_candidate_exact_plots_exports_replay_restart_stale_and_permissions(tmp_path, cycle):
    root = tmp_path / "state"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        baseline = design(cycle)
        spec, _ = specification(baseline,cooling=True)
        source = app.project_api.service.create(actor, project["project_id"],design=baseline,operation_id="baseline",command_hash="1"*64)
        prefix = "/api/projects/"+project["project_id"]+"/engine-operating"
        capability = request(client,base,prefix+"/capabilities")
        assert capability["runtime_installed"] and capability["schema"] == spec["schema"]
        body = {"baseline_commit_id":source.commit_id,"expected_baseline":{"version":source.head.version,"content_hash":source.head.content_hash},"specification":spec,"operation_id":str(uuid4())}
        value = request(client,base,prefix,body)
        assert value["usable_current_solved_candidate"]
        result = value["record"]["evaluation"]["result"]
        assert result["outputs"]["candidate"]["cooling"]["total_heat_w"] > 0
        a = value["authority"]
        path = prefix+"/"+a["object_id"]+"?commit="+a["commit_id"]
        download = prefix+"/"+a["object_id"]+"/record.json?commit="+a["commit_id"]
        original = binary(client,base,download)
        assert original.decode() == value["source_canonical_json"]
        replay = request(client,base,prefix,body)
        assert replay["authority"] == a and replay["source_canonical_json"] == original.decode()
        inputs = binary(client,base,prefix+"/"+a["object_id"]+"/inputs.json?commit="+a["commit_id"])
        assert json.loads(inputs)["command"] == body
        assert app.project_api.repository.resolve_snapshot(actor,project["project_id"],source.commit_id).payload == source.payload
        with client.open(base+download) as response:
            assert response.headers["X-COSMOS-Scope"] == "selected-operating-model-not-physical-validation"
            assert "preliminary-model" in response.headers["Content-Disposition"]
        csv_raw = binary(client,base,prefix+"/"+a["object_id"]+"/residuals.csv?commit="+a["commit_id"])
        rows = list(csv.DictReader(io.StringIO(csv_raw.decode())))
        assert rows and all(row["commit_id"] == a["commit_id"] for row in rows)
        for row, original_row in zip(rows,result["outputs"]["residuals"],strict=True):
            assert float(row["value"]) == original_row["value"] and row["unit"] == original_row["unit"]
        plots = request(client,base,prefix+"/"+a["object_id"]+"/plots?commit="+a["commit_id"])
        assert len(plots["plots"]) == 3
        for plot in plots["plots"]:
            assert plot["source"]["domain"] == "engine-operating-point"
            assert plot["source"]["source_canonical_json"].encode() == original
        context = request(client,base,"/api/projects/"+project["project_id"]+"/records/"+a["commit_id"])
        assert context["upstream_current"] and len(context["upstream"]) == 2
        request(client,base,prefix,{**body,"independent_acceptance":True},expected=400)
        request(client,base,path+"&ignored=true",expected=400)
        other = new_project(base,client)
        request(client,base,"/api/projects/"+other["project_id"]+"/engine-operating/"+a["object_id"]+"?commit="+a["commit_id"],expected=404)
        viewer = app.auth.register_user(login_id="operating-viewer",password="Synthetic-Operating-Only!",display_name="Synthetic viewer",designation="Test",employee_id="OP-VIEW",team="QA",role=UserRole.VIEWER)
        project_path = "/api/projects/"+project["project_id"]
        request(client,base,project_path+"/members",{"user_id":viewer.user_id,"capability":"VIEWER","expected":request(client,base,project_path)["project"]["head"],"operation_id":str(uuid4())})
        reader = client_for(base,"operating-viewer","Synthetic-Operating-Only!","USER")
        assert request(reader,base,path)["record"]["physical_validation"] == "NOT_PERFORMED"
        request(reader,base,prefix,{**body,"operation_id":str(uuid4())},expected=403)
        # Nonconvergence is retained, but it cannot become a usable candidate.
        bad = json.loads(json.dumps(body))
        bad["operation_id"] = str(uuid4())
        bad["specification"]["solver"]["max_iterations"] = 1
        failed = request(client,base,prefix,bad)
        assert not failed["usable_current_solved_candidate"]
        assert failed["record"]["evaluation"]["result"]["outputs"]["candidate"] is None
        current = request(client,base,project_path+"/designs/"+source.object_id)
        request(client,base,route(project,current)+"/requirements",command(current,updates={"target_chamber_pressure":6e6}))
        assert not request(client,base,path)["usable_current_solved_candidate"]
        assert binary(client,base,download) == original
    with running(root) as (_, base, client):
        assert binary(client,base,download) == original
    with running(root,enabled=False) as (_,base,client):
        assert binary(client,base,download) == original
        request(client,base,prefix,body,expected=403)
