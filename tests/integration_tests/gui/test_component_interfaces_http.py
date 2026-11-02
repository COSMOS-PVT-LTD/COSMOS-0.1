from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def test_exact_read_only_interface_inspection_project_scope_and_no_inferred_pipes(tmp_path):
    with running(tmp_path/"state") as (app,base,client):
        _,baseline,root,_,saved=capture(app,base,client)
        uri=root+"/component-interfaces/"+saved["authority"]["object_id"]
        query="?commit="+saved["authority"]["commit_id"]+"&tolerance_m=0.000001"
        value=request(client,base,uri+query)
        assert value["upstream_current"] and not value["persisted"] and len(value["ports"])==8
        assert value["baseline_commit_id"]==baseline.commit_id and not value["geometry_route_complete"]
        assert value["mechanical_joints"]["source_graph_id"]==value["source_graph_id"]
        assert not value["mechanical_joints"]["complete_engine_pressure_joints"]
        request(client,base,uri+"?commit="+saved["authority"]["commit_id"],expected=400)
        request(client,base,uri+query+"&fluid=fuel",expected=400)
        request(client,base,uri+query+"&fuel_boundary=invented",expected=400)
        request(client,base,uri+query+"&fuel_boundary=invented&oxidizer_boundary=invented",expected=400)
        request(client,base,uri+query.replace("0.000001","nan"),expected=400)
        request(client,base,uri,{"commit":saved["authority"]["commit_id"]},expected=404)
        other=new_project(base,client)
        request(client,base,"/api/projects/"+other["project_id"]+"/component-interfaces/"+saved["authority"]["object_id"]+query,expected=404)
        assert request(client,base,root+"/component-geometry/"+saved["authority"]["object_id"])["source_canonical_json"]==saved["source_canonical_json"]
