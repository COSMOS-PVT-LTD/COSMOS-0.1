from uuid import uuid4

import pytest

from tests.fixtures.geometry_qualification import pipe_policy
from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa:F401
)


def policy_command(saved, policy=None):
    return {
        "model_commit_id": saved["authority"]["commit_id"],
        "expected_model": saved["authority"]["head"],
        "policy": policy or pipe_policy(),
        "operation_id": str(uuid4()),
    }


def test_r08_disabled_execution_still_serves_policy_and_ui(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        _project, _, root, _, saved = capture(app, base, client, "pipe.circular")
        uri = root + "/geometry-qualifications"
        assert (
            request(client, base, uri + "/capabilities")["runtime_configured"] is False
        )
        with client.open(base + "/assets/geometry-qualification.js", timeout=15) as r:
            assert r.status == 200 and b"CosmosGeometryQualification" in r.read()
        command = policy_command(saved)
        p = request(client, base, uri + "/policies", command)
        assert (
            p["upstream_current"]
            and request(client, base, uri + "/policies", command)["authority"]
            == p["authority"]
        )
        assert len(request(client, base, uri + "/policies")["records"]) == 1
        result = request(
            client,
            base,
            uri + "/evaluate",
            {
                "policy_commit_id": p["authority"]["commit_id"],
                "analytic_job_id": str(uuid4()),
                "implicit_job_ids": [],
                "operation_id": str(uuid4()),
            },
            expected=400,
        )
        assert "runtime" in str(result).lower()
        other = new_project(base, client)
        request(
            client,
            base,
            "/api/projects/"
            + other["project_id"]
            + "/geometry-qualifications/policies/"
            + p["authority"]["object_id"],
            expected=404,
        )


@pytest.mark.parametrize(
    "change", ["unit", "override", "missing-region", "unsaved-head"]
)
def test_r08_rejects_incomplete_policy_or_source_overrides(tmp_path, change):
    with running(tmp_path / "state") as (app, base, client):
        _, _, root, _, saved = capture(app, base, client, "pipe.circular")
        command = policy_command(saved)
        if change == "unit":
            command["policy"]["unit_system"] = "mm"
        elif change == "override":
            command["worker"] = "/tmp/untrusted"
        elif change == "missing-region":
            command["policy"]["regions"] = []
        else:
            command["expected_model"]["version"] = 0
        request(
            client,
            base,
            root + "/geometry-qualifications/policies",
            command,
            expected=409 if change == "unsaved-head" else 400,
        )


def test_r08_viewer_cannot_admit_qualification_even_before_runtime_resolution(tmp_path):
    from api.authentication import UserRole
    from tests.integration_tests.gui.test_project_authority_http import client_for

    with running(tmp_path / "state") as (app, base, client):
        _, _, root, _, saved = capture(app, base, client, "pipe.circular")
        policy = request(
            client,
            base,
            root + "/geometry-qualifications/policies",
            policy_command(saved),
        )
        user = app.auth.register_user(
            login_id="r08-viewer",
            password="Synthetic-Test-Password!",
            display_name="Synthetic R08 viewer fixture",
            designation="Test only",
            employee_id="R08-TEST",
            team="QA",
            role=UserRole.VIEWER,
        )
        request(
            client,
            base,
            root + "/members",
            {
                "user_id": user.user_id,
                "capability": "VIEWER",
                "expected": request(client, base, root)["project"]["head"],
                "operation_id": str(uuid4()),
            },
        )
        viewer = client_for(base, "r08-viewer", "Synthetic-Test-Password!", "USER")
        request(
            viewer,
            base,
            root + "/geometry-qualifications/evaluate",
            {
                "policy_commit_id": policy["authority"]["commit_id"],
                "analytic_job_id": str(uuid4()),
                "implicit_job_ids": [],
                "operation_id": str(uuid4()),
            },
            expected=403,
        )
