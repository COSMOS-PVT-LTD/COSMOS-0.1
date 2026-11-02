"""Actual authenticated coupled-cycle HTTP/source/export/restart qualification."""

import csv
import io
import json
from uuid import uuid4

from api.authentication import UserRole
from api.project_authority import principal
from systems.projects.propulsion_authority import decode_design
from tests.fixtures.coupled_cycle import design, specification
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


def test_real_http_coupling_bytes_plots_invalidation_denial_and_restart(tmp_path):
    root = tmp_path / "state"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        source = app.project_api.service.create(
            actor,
            project["project_id"],
            design=design(cooling=True, film=True),
            operation_id="baseline",
            command_hash="1" * 64,
        )
        prefix = "/api/projects/" + project["project_id"] + "/cycle-assessments"
        capabilities = request(client, base, prefix + "/capabilities")
        assert capabilities["cycles"] == ["PRESSURE_FED", "GAS_GENERATOR"]
        body = {
            "baseline_commit_id": source.commit_id,
            "expected_baseline": {
                "version": source.head.version,
                "content_hash": source.head.content_hash,
            },
            "operation_id": str(uuid4()),
            "specification": specification(
                decode_design(source), cooling=True, film=True
            ),
        }
        saved = request(client, base, prefix, body)
        assert saved["usable_current_balanced_assessment"], saved["record"]["failure"]
        path = prefix + "/" + saved["authority"]["object_id"]
        raw = binary(client, base, path + "/record.json")
        assert raw == saved["source_canonical_json"].encode()
        assert request(client, base, prefix, body) == saved
        capture = json.loads(binary(client, base, path + "/inputs.json"))
        assert (
            capture["command"] == body
            and capture["baseline_canonical_json"].encode() == source.payload
        )
        rows = list(
            csv.DictReader(
                io.StringIO(binary(client, base, path + "/residuals.csv").decode())
            )
        )
        originals = saved["record"]["evaluation"]["result"]["outputs"]["residuals"]
        assert len(rows) == len(originals)
        for row, original in zip(rows, originals, strict=True):
            assert (
                float(row["value"]) == original["value"]
                and row["unit"] == original["unit"]
            )
            assert row["commit_id"] == saved["authority"]["commit_id"]
        plots = request(client, base, path + "/plots")["plots"]
        assert plots[0]["source"]["source_canonical_json"].encode() == raw
        assert plots[0]["rows"][0]["raw_value"] == originals[0]["value"]
        context = request(
            client,
            base,
            "/api/projects/"
            + project["project_id"]
            + "/records/"
            + saved["authority"]["commit_id"],
        )
        assert context["upstream_current"] and len(context["upstream"]) == 2
        viewer = app.auth.register_user(
            login_id="cycle-viewer",
            display_name="Synthetic cycle viewer",
            password="Synthetic-Cycle-Viewer-Only!",
            designation="Test",
            employee_id="CYCLE-VIEWER",
            team="QA",
            role=UserRole.VIEWER,
        )
        project_path = "/api/projects/" + project["project_id"]
        request(
            client,
            base,
            project_path + "/members",
            {
                "user_id": viewer.user_id,
                "capability": "VIEWER",
                "expected": request(client, base, project_path)["project"]["head"],
                "operation_id": str(uuid4()),
            },
        )
        reader = client_for(
            base, "cycle-viewer", "Synthetic-Cycle-Viewer-Only!", "USER"
        )
        assert request(reader, base, path)["record"]["status"] == "COMPLETED"
        request(
            reader, base, prefix, {**body, "operation_id": str(uuid4())}, expected=403
        )
        request(client, base, prefix, {**body, "role": "ADMIN"}, expected=400)
        other = new_project(base, client)
        request(
            client,
            base,
            "/api/projects/"
            + other["project_id"]
            + "/cycle-assessments/"
            + saved["authority"]["object_id"],
            expected=404,
        )
        request(client, base, path + "?ignored=context", expected=400)
        body["operation_id"] = str(uuid4())
        body["specification"]["gas_generator"]["maximum_flow"]["value"] = 1e-12
        failure = request(client, base, prefix, body)
        assert (
            failure["record"]["status"] == "FAILED"
            and failure["record"]["evaluation"] is None
        )
        request(
            client,
            base,
            prefix + "/" + failure["authority"]["object_id"] + "/residuals.csv",
            expected=400,
        )
        current = request(
            client,
            base,
            "/api/projects/" + project["project_id"] + "/designs/" + source.object_id,
        )
        request(
            client,
            base,
            route(project, current) + "/requirements",
            command(current, updates={"target_chamber_pressure": 6e6}),
        )
        assert not request(client, base, path)["upstream_current"]
        assert not request(client, base, path + "/plots")["plots"]
        assert binary(client, base, path + "/record.json") == raw
    with running(root) as (_, base, client):
        assert binary(client, base, path + "/record.json") == raw
        assert not request(client, base, path)["usable_current_balanced_assessment"]
    with running(root, enabled=False) as (_, base, client):
        assert binary(client, base, path + "/record.json") == raw
        request(client, base, prefix, body, expected=403)
