"""Read-only source exactness, access control and historical handoff behavior."""
from copy import deepcopy
from uuid import uuid4

from api.project_authority import principal
from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def test_exact_handoff_get_is_source_bound_read_only_and_historical_after_change(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        _, baseline, root, command, saved = capture(app, base, client)
        model_id, commit = saved["authority"]["object_id"], saved["authority"]["commit_id"]
        uri = root + "/component-cooling/" + model_id
        report = request(client, base, uri + "?commit=" + commit)
        assert report["authority"] == {k: saved["authority"][k] for k in ("project_id", "object_id", "commit_id", "head")}
        assert report["baseline_commit_id"] == baseline.commit_id
        assert report["upstream_current"] and not report["persisted"]
        assert len(report["passages"]) == 1 and report["source_graph_sha256"]
        before = request(client, base, root + "/component-geometry/" + model_id)
        request(client, base, uri, expected=400)
        request(client, base, uri + "?commit=" + commit + "&commit=" + commit, expected=400)
        request(client, base, uri + "?commit=" + commit + "&width=1", expected=400)
        request(client, base, uri, {"commit": commit}, expected=404)
        other = new_project(base, client)
        request(client, base, "/api/projects/" + other["project_id"] + "/component-cooling/" + model_id + "?commit=" + commit, expected=404)
        after = request(client, base, root + "/component-geometry/" + model_id)
        assert before["source_canonical_json"] == after["source_canonical_json"]
        changed = deepcopy(command)
        changed.update(expected=saved["authority"]["head"], operation_id=str(uuid4()))
        changed["specification"]["features"][1]["parameters"]["width"]["value"] *= 1.1
        edited = request(client, base, root + "/component-geometry/" + model_id, changed)
        historical = request(client, base, uri + "?commit=" + commit)
        assert not historical["upstream_current"] and historical["passages"] == report["passages"]
        current = request(client, base, uri + "?commit=" + edited["authority"]["commit_id"])
        assert current["upstream_current"] and current["passages"] != report["passages"]
        assert app.project_api.repository.get_snapshot(principal(app.auth.list_users()[0]),
            baseline.project_id, domain=baseline.domain, object_id=baseline.object_id).payload == baseline.payload
