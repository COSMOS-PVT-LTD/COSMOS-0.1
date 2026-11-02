"""Real solved candidate into blank evidence workflow; not physical evidence."""

import base64
import csv
import io

import pytest

pytest.importorskip("cea", reason="Pinned NASA CEA needed for solved-candidate validation preparation")

from api.project_authority import principal
from tests.fixtures.engine_operating import design, specification
from tests.fixtures.propulsion_validation import csv_data, metadata
from tests.fixtures.propulsion_validation import specification as plan_specification
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


@pytest.mark.parametrize("cycle", ["PRESSURE_FED", "GAS_GENERATOR"])
def test_solved_predictions_exact_context_plan_blank_template_import_and_stale_guard(tmp_path, cycle):
    with running(tmp_path / "state") as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        baseline = design(cycle)
        recipe, _ = specification(baseline, cooling=True)
        source = app.project_api.service.create(actor, project["project_id"], design=baseline, operation_id="baseline", command_hash="1" * 64)
        saved = app.project_api.engine_operating.service.create(actor, source.project_id, source.commit_id, source.head, recipe, "operating", "2" * 64)
        targets = ["solved_chamber_pressure", "coolant_heat_pickup"] + (["solved_shaft_speed"] if cycle == "GAS_GENERATOR" else [])
        prefix = "/api/projects/" + project["project_id"] + "/propulsion-validation"
        preview = request(client, base, prefix + "/preview?baseline=" + saved.commit_id + "&targets=" + ",".join(targets))
        candidate = preview["candidate"]
        expected = app.project_api.engine_operating.service.read(actor, saved)["record"]["evaluation"]["result"]["outputs"]["candidate"]
        assert candidate["predictions"]["solved_chamber_pressure"]["value"] == expected["unknowns"]["chamber_pressure"]["value"]
        assert candidate["predictions"]["coolant_heat_pickup"]["value"] == expected["cooling"]["total_heat_w"]
        assert candidate["conditions"]["fuel_temperature"]["value"] == recipe["feeds"]["fuel"]["temperature"]["value"]
        assert candidate["properties"]["wall_thickness_m"]["value"] == baseline.subsystem_inputs["cooling"]["wall_thickness_m"]
        assert "chamber_pressure" not in candidate["conditions"]  # solved output, not an imposed matching input
        body = {"baseline_commit_id": saved.commit_id, "expected_baseline": preview["expected_baseline"], "specification": plan_specification(candidate, unknown=True), "operation_id": "plan"}
        plan = request(client, base, prefix + "/plans", body)
        assert plan["record"]["physical_validation"] == "NOT_PERFORMED" and plan["record"]["readiness"] == "AWAITING_MEASUREMENTS"
        assert plan["record"]["candidate"]["baseline_canonical_json"].encode() == saved.payload
        path = prefix + "/records/" + plan["authority"]["commit_id"]
        original = binary(client, base, path + "/record.json")
        rows = list(csv.DictReader(io.StringIO(binary(client, base, path + "/measurement-template.csv").decode())))
        assert rows and all(row["value"] == "" and row["standard_uncertainty"] == "" for row in rows)
        assert not request(client, base, prefix + "/measurements")["records"]
        # Shared comparison still labels synthetic fixtures and missing prediction U.
        measured = request(client, base, prefix + "/measurements", {"plan_commit_id": plan["authority"]["commit_id"], "csv_base64": base64.b64encode(csv_data(plan["record"])).decode(), "provenance": metadata(), "operation_id": "synthetic-measurements"})
        comparison = request(client, base, prefix + "/assessments", {"plan_commit_id": plan["authority"]["commit_id"], "measurement_commit_id": measured["authority"]["commit_id"], "operation_id": "comparison"})
        assert comparison["record"]["physical_validation"] == "NOT_PERFORMED"
        assert comparison["record"]["independent_acceptance"] is False
        if cycle == "PRESSURE_FED":
            request(client, base, prefix + "/preview?baseline=" + saved.commit_id + "&targets=solved_shaft_speed", expected=400)
        original_methods = app.project_api.engine_operating.service.methods
        app.project_api.engine_operating.service.methods = lambda: {**original_methods(), "synthetic-change": "3" * 64}
        request(client, base, prefix + "/preview?baseline=" + saved.commit_id + "&targets=thrust", expected=400)
        request(client, base, prefix + "/plans", {**body, "operation_id": "stale-plan"}, expected=400)
        assert binary(client, base, path + "/record.json") == original
    with running(tmp_path / "state") as (_, base, client):
        assert binary(client, base, path + "/record.json") == original
