"""Synthetic end-to-end evidence preparation; not an experimental campaign."""

import base64
import csv
import io
from uuid import uuid4

from api.authentication import UserRole
from api.project_authority import principal
from tests.fixtures.coupled_cycle import design
from tests.fixtures.propulsion_validation import csv_data, metadata, specification
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


def test_http_plan_empty_template_source_import_comparison_stale_and_restart(tmp_path):
    root = tmp_path / "state"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        source = app.project_api.service.create(
            actor,
            project["project_id"],
            design=design(cooling=True),
            operation_id="candidate",
            command_hash="1" * 64,
        )
        prefix = "/api/projects/" + project["project_id"] + "/propulsion-validation"
        preview = request(
            client,
            base,
            prefix + "/preview?baseline=" + source.commit_id + "&targets=thrust",
        )
        body = {
            "baseline_commit_id": source.commit_id,
            "expected_baseline": preview["expected_baseline"],
            "specification": specification(preview["candidate"]),
            "operation_id": str(uuid4()),
        }
        plan = request(client, base, prefix + "/plans", body)
        plan_commit = plan["authority"]["commit_id"]
        assert plan["record"]["readiness"] == "AWAITING_MEASUREMENTS"
        assert (
            plan["record"]["candidate"]["baseline_canonical_json"].encode()
            == source.payload
        )
        assert request(client, base, prefix + "/plans", body) == plan
        source_path = prefix + "/records/" + plan_commit
        blank = binary(client, base, source_path + "/measurement-template.csv")
        template_rows = list(csv.DictReader(io.StringIO(blank.decode())))
        assert all(
            row["value"] == "" and row["standard_uncertainty"] == ""
            for row in template_rows
        )
        request(
            client,
            base,
            prefix + "/measurements",
            {
                "plan_commit_id": plan_commit,
                "csv_base64": base64.b64encode(blank).decode(),
                "provenance": metadata(),
                "operation_id": str(uuid4()),
            },
            expected=400,
        )
        assert not request(client, base, prefix + "/measurements")["records"]
        raw = csv_data(plan["record"])
        measured = request(
            client,
            base,
            prefix + "/measurements",
            {
                "plan_commit_id": plan_commit,
                "csv_base64": base64.b64encode(raw).decode(),
                "provenance": metadata(),
                "operation_id": str(uuid4()),
            },
        )
        measured_path = prefix + "/records/" + measured["authority"]["commit_id"]
        assert binary(client, base, measured_path + "/measurement-original.csv") == raw
        with client.open(
            base + measured_path + "/measurement-original.csv"
        ) as response:
            assert (
                response.headers["X-COSMOS-Scope"]
                == "unreviewed-propulsion-evidence-not-physical-acceptance"
            )
            assert "unreviewed-evidence" in response.headers["Content-Disposition"]
        assessed = request(
            client,
            base,
            prefix + "/assessments",
            {
                "plan_commit_id": plan_commit,
                "measurement_commit_id": measured["authority"]["commit_id"],
                "operation_id": str(uuid4()),
            },
        )
        assert (
            assessed["record"]["software_comparison_passed"]
            and not assessed["independent_acceptance"]
        )
        assert assessed["physical_validation"] == "NOT_PERFORMED"
        assert "SYNTHETIC_IS_NOT_PHYSICAL_EVIDENCE" in assessed["record"]["blockers"]
        assessment_path = prefix + "/records/" + assessed["authority"]["commit_id"]
        original = binary(client, base, assessment_path + "/record.json")
        context = request(
            client,
            base,
            "/api/projects/"
            + project["project_id"]
            + "/records/"
            + assessed["authority"]["commit_id"],
        )
        assert context["upstream_current"] and len(context["upstream"]) == 2
        request(
            client,
            base,
            source_path + "/accept",
            {"independent_acceptance": True},
            expected=404,
        )
        request(
            client,
            base,
            prefix + "/plans",
            {**body, "physical_validation": "PASSED", "operation_id": str(uuid4())},
            expected=400,
        )
        request(client, base, source_path + "?ignored=authority", expected=400)
        other = new_project(base, client)
        request(
            client,
            base,
            "/api/projects/"
            + other["project_id"]
            + "/propulsion-validation/records/"
            + plan_commit,
            expected=404,
        )
        viewer = app.auth.register_user(
            login_id="validation-viewer",
            password="Synthetic-Validation-Only!",
            display_name="Synthetic viewer",
            designation="Test",
            employee_id="VV-VIEWER",
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
            base, "validation-viewer", "Synthetic-Validation-Only!", "USER"
        )
        assert (
            request(reader, base, source_path)["record"]["readiness"]
            == "AWAITING_MEASUREMENTS"
        )
        request(
            reader,
            base,
            prefix + "/plans",
            {**body, "operation_id": str(uuid4())},
            expected=403,
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
        assert not request(client, base, assessment_path)["upstream_current"]
        assert binary(client, base, assessment_path + "/record.json") == original
    with running(root) as (_, base, client):
        assert binary(client, base, assessment_path + "/record.json") == original
    with running(root, enabled=False) as (_, base, client):
        assert binary(client, base, assessment_path + "/record.json") == original
        request(client, base, prefix + "/plans", body, expected=403)
