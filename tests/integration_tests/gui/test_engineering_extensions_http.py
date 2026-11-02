"""Real authority/HTTP/history qualification; native cases in a separate test."""

import csv
import io
import json
from uuid import uuid4

import pytest

from api.authentication import UserRole
from api.project_authority import principal
from tests.fixtures.coupled_cycle import design
from tests.fixtures.engineering_extensions import intent, sensitivity
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    command,
    new_project,
    request,
    route,
    running,
)
from tests.unit_tests.systems_layer.test_engineering_extensions import analytic
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("kind", ["operating-sensitivity", "engine-geometry-intent"])
def test_exact_capture_replay_export_permissions_stale_and_restart(tmp_path, monkeypatch, kind):
    if kind == "operating-sensitivity":
        from systems.cycle.operating_sensitivity import study
        monkeypatch.setattr("api.engineering_extensions.study", lambda d, s: study(d, s, evaluator=analytic))
    with running(tmp_path / "state") as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        source = app.project_api.service.create(actor, project["project_id"], design=design(cooling=True), operation_id="baseline", command_hash="1" * 64)
        prefix = "/api/projects/" + project["project_id"] + "/" + kind
        assert request(client, base, prefix + "/capabilities")["schema"]
        spec = sensitivity() if kind == "operating-sensitivity" else intent()
        body = {"baseline_commit_id": source.commit_id, "expected_baseline": {"version": source.head.version, "content_hash": source.head.content_hash}, "specification": spec, "operation_id": str(uuid4())}
        value = request(client, base, prefix, body)
        assert value["record"]["status"] == "COMPLETED", value["record"]["failure"]
        assert request(client, base, prefix, body)["authority"] == value["authority"]
        a = value["authority"]
        path = prefix + "/" + a["object_id"]
        exact = "?commit=" + a["commit_id"]
        raw = binary(client, base, path + "/record.json" + exact)
        assert raw.decode() == value["source_canonical_json"]
        captured = binary(client, base, path + "/inputs.json" + exact)
        assert json.loads(captured)["command"] == body
        capture = request(client, base, prefix + "/captures/" + a["object_id"])
        assert capture["terminal_commit_id"] == a["commit_id"]
        plots = request(client, base, path + "/plots" + exact)
        assert len(plots["plots"]) == 1
        assert plots["plots"][0]["source"]["domain"] == kind
        assert plots["plots"][0]["source"]["source_canonical_json"] == raw.decode()
        if kind == "operating-sensitivity":
            rows = list(csv.DictReader(io.StringIO(binary(client, base, path + "/residuals.csv" + exact).decode())))
            assert len(rows) == 5 and all(row["commit_id"] == a["commit_id"] for row in rows)
        else:
            with client.open(base + path + "/record.json" + exact) as response:
                assert "unbuilt-engine-intent" in response.headers["Content-Disposition"]
                assert response.headers["X-COSMOS-Scope"] == "unbuilt-engine-geometry-intent-not-cad-acceptance"
            request(client, base, path + "/residuals.csv" + exact, expected=400)
            assert value["record"]["evaluation"]["result"]["outputs"]["artifacts"] == []
        request(client, base, path + exact + "&ignored=true", expected=400)
        request(client, base, prefix, {**body, "independent_acceptance": True}, expected=400)
        other = new_project(base, client)
        request(client, base, "/api/projects/" + other["project_id"] + "/" + kind + "/" + a["object_id"] + exact, expected=404)
        viewer = app.auth.register_user(login_id="extension-viewer", password="Synthetic-Extension-Only!", display_name="Synthetic viewer", designation="Test", employee_id="EX-VIEW", team="QA", role=UserRole.VIEWER)
        project_path = "/api/projects/" + project["project_id"]
        request(client, base, project_path + "/members", {"user_id": viewer.user_id, "capability": "VIEWER", "expected": request(client, base, project_path)["project"]["head"], "operation_id": str(uuid4())})
        reader = client_for(base, "extension-viewer", "Synthetic-Extension-Only!", "USER")
        assert binary(reader, base, path + "/record.json" + exact) == raw
        request(reader, base, prefix, {**body, "operation_id": str(uuid4())}, expected=403)
        # Live-method changes invalidate context, not retained originals.
        service = app.project_api.operating_sensitivity.service if kind == "operating-sensitivity" else app.project_api.engine_geometry.service
        original_methods = service.methods
        service.methods = lambda: {**original_methods(), "synthetic-method-change": "2" * 64}
        assert not request(client, base, path + exact)["upstream_current"]
        assert request(client, base, project_path + "/records/" + a["commit_id"])["upstream_current"] is False
        service.methods = original_methods
        current = request(client, base, project_path + "/designs/" + source.object_id)
        request(client, base, route(project, current) + "/requirements", command(current, updates={"target_chamber_pressure": 6e6}))
        assert not request(client, base, path + exact)["upstream_current"]
        assert request(client, base, path + "/plots" + exact)["plots"] == []
        assert binary(client, base, path + "/record.json" + exact) == raw
        assert app.project_api.repository.resolve_snapshot(actor, project["project_id"], source.commit_id).payload == source.payload
    with running(tmp_path / "state", enabled=False) as (_, base, client):
        assert binary(client, base, path + "/record.json" + exact) == raw
        request(client, base, prefix, body, expected=403)


def test_plot_invalid_gap_is_not_joined_and_singletons_are_not_curves():
    from api.engineering_extensions import sensitivity_plots
    value = {"upstream_current": True, "authority": {"project_id": "p", "commit_id": "c", "head": {"content_hash": "1" * 64}}, "source_canonical_json": "{}", "record": {"status": "COMPLETED", "baseline_commit_id": "b", "method_sources": {"test": "1" * 64}, "command": {"specification": sensitivity()}, "evaluation": {"result": {"model_id": "test", "assumptions": [], "warnings": [], "outputs": {"study_status": "COMPLETED_WITH_INVALID_DOMAINS", "output_unit": "N", "samples": [{"value": 1, "status": "VALID", "output": 1}, {"value": 2, "status": "INVALID", "output": None}, {"value": 3, "status": "VALID", "output": 3}]}}}}}
    plots = sensitivity_plots(value)
    assert plots["plots"] == [] and plots["unavailable"]
