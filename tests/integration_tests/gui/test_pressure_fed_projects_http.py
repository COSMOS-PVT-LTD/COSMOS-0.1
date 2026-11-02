"""Authenticated pressure-fed input/result/source/export/restart journey."""

from __future__ import annotations

import csv
import io
import json
from hashlib import sha256
from uuid import uuid4

import pytest

from api.authentication import UserRole
from systems.projects.models import PropulsionDesign
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    command,
    configured,
    new_design,
    new_project,
    request,
    route,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import specification


def prepared(base, client, project):
    current = configured(base, client, project, new_design(base, client, project))
    current = request(
        client,
        base,
        route(project, current) + "/save",
        command(
            current,
            cycle_type="PRESSURE_FED",
            requirements={"mixture_ratio": 2.0},
            propellants={"oxidizer_id": "LOX", "fuel_id": "RP-1", "mixture_ratio": 2.0},
        ),
    )
    return request(
        client,
        base,
        route(project, current) + "/run/phase3",
        command(
            current,
            chamber_temperature_k=3000.0,
            gamma=1.2,
            molecular_weight_kg_per_mol=0.022,
            throat_area_m2=0.001,
            expansion_ratio=10.0,
        ),
    )


def assessment_command(source):
    return {
        "baseline_commit_id": source["authority"]["commit_id"],
        "expected_baseline": source["authority"]["head"],
        "specification": specification(
            PropulsionDesign.from_canonical_dict(source["design"])
        ),
        "operation_id": str(uuid4()),
    }


def binary(client, base, path):
    with client.open(base + path, timeout=15) as response:
        raw = response.read()
        assert response.headers["Content-Disposition"].startswith("attachment;")
        assert response.headers["X-COSMOS-SHA256"] == sha256(raw).hexdigest()
        return raw


def test_saved_source_replay_exports_context_stale_history_and_restart(tmp_path):
    root = tmp_path / "managed"
    with running(root) as (_app, base, client):
        project = new_project(base, client)
        source = prepared(base, client, project)
        prefix = "/api/projects/" + project["project_id"] + "/pressure-fed"
        body = assessment_command(source)
        saved = request(client, base, prefix, body)
        assert (
            saved["record"]["status"] == "COMPLETED"
            and saved["usable_current_assessment"]
        )
        assert saved["record"]["evaluation"]["result"]["outputs"][
            "assessment_balances_closed_within_declared_tolerances"
        ]
        assert saved["record"]["evaluation"]["result"]["stage_id"] is None
        assert not saved["record"]["workflow_cycle_complete"]
        assert (
            request(client, base, route(project, source))["source_canonical_json"]
            == source["source_canonical_json"]
        )
        assert request(client, base, prefix, body) == saved
        path = prefix + "/" + saved["authority"]["object_id"]
        assert (
            request(client, base, path + "?commit=" + saved["authority"]["commit_id"])
            == saved
        )
        raw = binary(client, base, path + "/record.json")
        assert raw == saved["source_canonical_json"].encode()
        captured = json.loads(binary(client, base, path + "/inputs.json"))
        assert captured["baseline_canonical_json"] == source["source_canonical_json"]
        assert captured["command"] == body
        rows = list(
            csv.DictReader(
                io.StringIO(binary(client, base, path + "/residuals.csv").decode())
            )
        )
        assert len(rows) == 2
        for row in rows:
            original = saved["record"]["evaluation"]["result"]["outputs"]["streams"][
                row["stream"]
            ]
            assert (
                float(row["pressure_residual_pa"]) == original["pressure_residual_pa"]
            )
            assert float(row["mass_residual_kg_s"]) == original["mass_residual_kg_s"]
            assert row["commit_id"] == saved["authority"]["commit_id"]
            assert row["content_sha256"] == sha256(raw).hexdigest()
        context = request(
            client,
            base,
            "/api/projects/"
            + project["project_id"]
            + "/records/"
            + saved["authority"]["commit_id"],
        )
        assert context["upstream_current"] and len(context["upstream"]) == 2
        capture_id = request(client, base, prefix + "/captures")["captures"][0][
            "object_id"
        ]
        assert (
            request(client, base, prefix + "/captures/" + capture_id)[
                "terminal_commit_id"
            ]
            == saved["authority"]["commit_id"]
        )
        request(
            client,
            base,
            route(project, source) + "/requirements",
            command(source, updates={"target_chamber_pressure": 6e6}),
        )
        assert not request(client, base, path)["upstream_current"]
        assert binary(client, base, path + "/record.json") == raw
        assert "False" in binary(client, base, path + "/residuals.csv").decode()
        request(
            client, base, prefix, {**body, "operation_id": str(uuid4())}, expected=409
        )
    with running(root, enabled=False) as (_app, base, client):
        retained = request(client, base, path)
        assert retained["source_canonical_json"] == saved["source_canonical_json"]
        assert not retained["upstream_current"]
        assert binary(client, base, path + "/record.json") == raw
        request(client, base, prefix, body, expected=403)


def test_foreign_project_readers_and_posted_authority_are_denied(tmp_path):
    with running(tmp_path / "managed") as (app, base, client):
        project = new_project(base, client)
        source = prepared(base, client, project)
        prefix = "/api/projects/" + project["project_id"] + "/pressure-fed"
        body = assessment_command(source)
        saved = request(client, base, prefix, body)
        other = new_project(base, client)
        other_prefix = "/api/projects/" + other["project_id"] + "/pressure-fed"
        request(
            client,
            base,
            other_prefix + "/" + saved["authority"]["object_id"],
            expected=404,
        )
        request(
            client,
            base,
            other_prefix,
            {**body, "operation_id": str(uuid4())},
            expected=404,
        )
        request(
            client,
            base,
            prefix,
            {**body, "role": "ADMIN", "operation_id": str(uuid4())},
            expected=400,
        )
        viewer = app.auth.register_user(
            login_id="pressure-viewer",
            display_name="Synthetic viewer",
            password="Synthetic-Pressure-Only!",
            designation="Test",
            employee_id="PF-VIEWER",
            team="QA",
            role=UserRole.VIEWER,
        )
        request(
            client,
            base,
            "/api/projects/" + project["project_id"] + "/members",
            {
                "user_id": viewer.user_id,
                "capability": "VIEWER",
                "expected": request(
                    client, base, "/api/projects/" + project["project_id"]
                )["project"]["head"],
                "operation_id": str(uuid4()),
            },
        )
        reader = client_for(base, "pressure-viewer", "Synthetic-Pressure-Only!", "USER")
        assert (
            request(reader, base, prefix + "/" + saved["authority"]["object_id"])[
                "record"
            ]["status"]
            == "COMPLETED"
        )
        request(
            reader, base, prefix, {**body, "operation_id": str(uuid4())}, expected=403
        )


@pytest.mark.parametrize(
    "query", ["?unknown=1", "?commit=x&commit=y", "?commit=not-a-commit", "?limit=20"]
)
def test_exact_assessment_queries_do_not_ignore_context(tmp_path, query):
    with running(tmp_path / "managed") as (_app, base, client):
        project = new_project(base, client)
        source = prepared(base, client, project)
        prefix = "/api/projects/" + project["project_id"] + "/pressure-fed"
        saved = request(client, base, prefix, assessment_command(source))
        request(
            client,
            base,
            prefix + "/" + saved["authority"]["object_id"] + query,
            expected=404 if query == "?commit=not-a-commit" else 400,
        )


def test_scientific_failure_is_retained_but_never_exported_as_numeric_answer(tmp_path):
    with running(tmp_path / "managed") as (_app, base, client):
        project = new_project(base, client)
        source = prepared(base, client, project)
        source = request(
            client,
            base,
            route(project, source) + "/cycle",
            command(source, cycle_type="GAS_GENERATOR"),
        )
        prefix = "/api/projects/" + project["project_id"] + "/pressure-fed"
        saved = request(client, base, prefix, assessment_command(source))
        assert (
            saved["record"]["status"] == "FAILED"
            and saved["record"]["evaluation"] is None
        )
        path = prefix + "/" + saved["authority"]["object_id"]
        request(client, base, path + "/residuals.csv", expected=400)
        assert (
            json.loads(binary(client, base, path + "/record.json"))["failure"]["code"]
            == "OutOfRangeError"
        )
