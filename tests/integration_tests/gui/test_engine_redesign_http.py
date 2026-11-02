"""Real authenticated isolated-store boundary checks, not engine qualification."""

import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from api.project_authority import principal
from systems.geometry.component_model import compile_model
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import Head
from tests.integration_tests.gui.test_component_projects_http import capture
from tests.integration_tests.gui.test_project_authority_http import request, running


def compact_source(app, base, client):
    _, baseline, root, _, saved = capture(app, base, client)
    value = json.loads(saved["source_canonical_json"])
    specification = json.loads(
        (Path(__file__).parents[2] / "fixtures/compact_engine_source.json").read_text()
    )
    plan = compile_model(
        specification,
        "engine-component-software-fixture",
        "software-only",
        "2026-10-28T00:00:00+00:00",
    )
    value.update(
        specification=specification,
        snapshot_json=plan.snapshot.to_json(),
        graph_json=plan.graph.to_json(),
    )
    actor = principal(app.auth.list_users()[0])
    # Test-only source installation bypasses hydraulic sizing. It exercises the
    # redesign authority, not the engine operating solver or old source editor.
    repo = app.project_api.repository
    source = repo.save_snapshot(
        actor,
        baseline.project_id,
        domain="engine-component-model",
        object_id=saved["authority"]["object_id"],
        input_revision=1,
        payload=RecordPayload.from_mapping(
            value,
            "cosmos.engine-component-model.v1",
            source_namespace=plan.snapshot.project_id,
        ),
        expected=Head(**saved["authority"]["head"]),
        operation_id=str(uuid4()),
        command_hash="a" * 64,
        dependencies=(Dependency("engine-baseline", baseline.commit_id),),
        purpose="save",
    )
    return root, source, baseline, actor


def seed_and_command(client, base, root, source):
    seed = request(
        client,
        base,
        root + "/engine-redesign/seed",
        {"source_commit_id": source.commit_id},
    )
    command = {
        "title": "Isolated compact engine fixture; not hardware",
        "source_commit_id": source.commit_id,
        "expected_source": asdict(source.head),
        "specification": seed["specification"],
        "expected": asdict(Head.absent()),
        "operation_id": str(uuid4()),
    }
    return seed, command


def test_seed_preview_save_replay_cas_and_restart(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        app.ngg_enabled = True
        root, source, baseline, actor = compact_source(app, base, client)
        with client.open(base + "/app/workbench/native-geometry") as response:
            assert b"/assets/engine-redesign.js" in response.read()
        with client.open(base + "/assets/engine-redesign.js") as response:
            assert response.status == 200
            assert b"Compact engine" in response.read()
        seed, command = seed_and_command(client, base, root, source)
        assert seed["inspection"]["candidate_metal_groups"] == 6
        preview = request(
            client,
            base,
            root + "/engine-redesign/preview",
            {
                "source_commit_id": source.commit_id,
                "specification": seed["specification"],
            },
        )
        assert preview["persisted"] is False
        assert request(client, base, root + "/engine-redesign")["candidates"] == []
        saved = request(client, base, root + "/engine-redesign", command)
        path = root + "/engine-redesign/" + saved["authority"]["object_id"]
        assert saved["upstream_current"] is True
        assert saved["record"]["baseline_replacement"] is False
        assert (
            request(client, base, root + "/engine-redesign", command)["authority"]
            == saved["authority"]
        )
        request(
            client,
            base,
            root + "/engine-redesign",
            {**command, "title": "Reused op"},
            expected=409,
        )
        second = {
            **command,
            "expected": saved["authority"]["head"],
            "operation_id": str(uuid4()),
        }
        second["specification"]["stations"][12]["depth"]["value"] *= 0.8
        updated = request(client, base, path, second)
        request(
            client, base, path, {**second, "operation_id": str(uuid4())}, expected=409
        )
        historical = request(
            client, base, path + "?commit=" + saved["authority"]["commit_id"]
        )
        assert historical["upstream_current"] is False
        assert len(request(client, base, path + "/history")["commits"]) == 2
        recipe = request(
            client, base, path + "/recipe?commit=" + updated["authority"]["commit_id"]
        )
        assert recipe["recipe"]["recipe_sha256"] == updated["record"]["recipe_sha256"]
        repo = app.project_api.repository
        assert (
            repo.get_snapshot(
                actor,
                source.project_id,
                domain=source.domain,
                object_id=source.object_id,
            ).head
            == source.head
        )
        assert (
            repo.resolve_snapshot(actor, baseline.project_id, baseline.commit_id).head
            == baseline.head
        )
    with running(tmp_path / "state") as (_, base, client):
        assert request(client, base, path)["authority"] == updated["authority"]
        assert request(client, base, path)["upstream_current"] is True


def test_input_rejections_and_stale_source(tmp_path):
    with running(tmp_path / "state") as (app, base, client):
        root, source, _, actor = compact_source(app, base, client)
        _, command = seed_and_command(client, base, root, source)
        request(
            client,
            base,
            root + "/engine-redesign",
            {**command, "output_path": "/tmp/not-permitted"},
            expected=400,
        )
        request(client, base, root + "/engine-redesign?commit=x", command, expected=400)
        saved = request(client, base, root + "/engine-redesign", command)
        project2 = request(
            client,
            base,
            "/api/projects",
            {"title": "Other project", "operation_id": str(uuid4())},
        )["project"]
        request(
            client,
            base,
            "/api/projects/" + project2["project_id"] + "/engine-redesign/seed",
            {"source_commit_id": source.commit_id},
            expected=404,
        )
        value = json.loads(source.payload)
        value["title"] = "Changed source"
        app.project_api.repository.save_snapshot(
            actor,
            source.project_id,
            domain=source.domain,
            object_id=source.object_id,
            input_revision=2,
            payload=RecordPayload.from_mapping(
                value,
                source.schema_id,
                source_namespace="engine-component-software-fixture",
            ),
            expected=source.head,
            operation_id=str(uuid4()),
            command_hash="b" * 64,
            purpose="save",
        )
        request(
            client,
            base,
            root + "/engine-redesign/preview",
            {
                "source_commit_id": source.commit_id,
                "specification": command["specification"],
            },
            expected=400,
        )
        path = root + "/engine-redesign/" + saved["authority"]["object_id"]
        assert request(client, base, path)["upstream_current"] is False
        request(client, base, path + "/activate", command, expected=404)
