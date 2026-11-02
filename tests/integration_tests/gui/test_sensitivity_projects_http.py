"""Actual authenticated managed sensitivity, source retention and restart."""

from __future__ import annotations

from uuid import uuid4

from tests.integration_tests.gui.test_project_authority_http import (
    command,
    configured,
    new_design,
    new_project,
    request,
    route,
    running,
)
from tests.unit_tests.systems_layer.test_propulsion_sensitivity import specification


def test_exact_saved_sensitivity_restart_plots_replay_stale_and_cross_project(tmp_path):
    root = tmp_path / "application"
    with running(root) as (_app, base, client):
        project = new_project(base, client)
        original = configured(base, client, project, new_design(base, client, project))
        source = request(
            client,
            base,
            route(project, original) + "/run/phase3",
            command(
                original,
                chamber_temperature_k=3000.0,
                gamma=1.2,
                molecular_weight_kg_per_mol=0.022,
                throat_area_m2=0.001,
                expansion_ratio=10.0,
            ),
        )
        prefix = "/api/projects/" + project["project_id"]
        body = {
            "baseline_commit_id": source["authority"]["commit_id"],
            "expected_baseline": source["authority"]["head"],
            "specification": specification(),
            "operation_id": str(uuid4()),
        }
        saved = request(client, base, prefix + "/sensitivity", body)
        assert saved["upstream_current"] and saved["record"]["status"] == "COMPLETED"
        assert (
            request(client, base, route(project, source))["source_canonical_json"]
            == source["source_canonical_json"]
        )
        key = saved["authority"]["object_id"]
        assert (
            request(client, base, prefix + "/sensitivity", body)["authority"]
            == saved["authority"]
        )
        assert (
            len(
                request(client, base, prefix + "/sensitivity/" + key + "/plots")[
                    "plots"
                ]
            )
            == 1
        )
        assert request(
            client, base, prefix + "/records/" + saved["authority"]["commit_id"]
        )["upstream_current"]
        other = new_project(base, client, "Other private project")
        request(
            client,
            base,
            "/api/projects/" + other["project_id"] + "/sensitivity/" + key,
            expected=404,
        )
        request(
            client,
            base,
            prefix + "/sensitivity",
            {**body, "operation_id": str(uuid4()), "role": "ADMIN"},
            expected=400,
        )
        request(
            client,
            base,
            prefix + "/sensitivity",
            {
                **body,
                "operation_id": str(uuid4()),
                "specification": specification(unit="bar"),
            },
            expected=400,
        )
        edited = request(
            client,
            base,
            route(project, source) + "/requirements",
            command(source, updates={"target_chamber_pressure": 6e6}),
        )
        assert edited["authority"]["commit_id"] != source["authority"]["commit_id"]
        assert not request(client, base, prefix + "/sensitivity/" + key)[
            "upstream_current"
        ]
        request(client, base, prefix + "/sensitivity/" + key + "/plots", expected=400)
        request(
            client,
            base,
            prefix + "/sensitivity",
            {**body, "operation_id": str(uuid4())},
            expected=409,
        )
    with running(root, enabled=False) as (_app, base, client):
        retained = request(client, base, prefix + "/sensitivity/" + key)
        assert retained["source_canonical_json"] == saved["source_canonical_json"]
        request(client, base, prefix + "/sensitivity", body, expected=403)
