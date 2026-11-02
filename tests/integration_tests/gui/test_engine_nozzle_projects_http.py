"""Actual pinned native nozzle through authenticated managed authority and restart."""

import json
import time
from dataclasses import asdict
from uuid import uuid4

from api.authentication import UserRole
from api.project_authority import principal
from systems.geometry.nozzle_workspace import NozzleWorkspace
from tests.fixtures.coupled_cycle import design
from tests.fixtures.engineering_extensions import intent
from tests.fixtures.nozzle_geometry import qa_spec
from tests.integration_tests.geometry.test_engine_nozzle_native import commands
from tests.integration_tests.gui.test_pressure_fed_projects_http import binary
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    new_project,
    request,
    running,
)
from tests.unit_tests.systems_layer.test_pressure_fed_assessment import (
    isolated_catalog,  # noqa: F401
)


def wait(client, base, path):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        value = request(client, base, path)
        if value["state"] in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
            return value
        time.sleep(.1)
    raise AssertionError("Bounded native nozzle attempt did not reach terminal state")


def compose(app):
    worker, reader = commands()
    config = {"sha256": {"test-explicit-runtime": "1" * 64}, "manifest_sha256": "2" * 64,
              "engine_nozzle": {"worker": {"argv": list(worker.argv), "environment": dict(worker.environment)}, "reader": {"argv": list(reader.argv), "environment": dict(reader.environment)}}}
    workspace = NozzleWorkspace(app.root / "nozzle-test-candidates", lambda: config)
    app._nozzle_workspace = workspace
    app.project_api.engine_builds.coordinator.factory = lambda: workspace
    return workspace


def captured(app, base, client):
    project = new_project(base, client)
    actor = principal(app.auth.list_users()[0])
    source = app.project_api.service.create(actor, project["project_id"], design=design(cooling=True), operation_id="baseline", command_hash="1" * 64)
    root = "/api/projects/" + project["project_id"]
    saved = request(client, base, root + "/engine-geometry-intent", {"baseline_commit_id": source.commit_id, "expected_baseline": asdict(source.head), "specification": intent(), "operation_id": str(uuid4())})
    assert saved["usable_current_assessment"], saved
    body = {"intent_commit_id": saved["authority"]["commit_id"], "expected_intent": saved["authority"]["head"], "qa_specification": qa_spec(), "output_formats": ["step", "stl"], "operation_id": str(uuid4())}
    return project, source, root + "/engine-geometry-builds", body


def test_real_saved_81_station_nozzle_build_exact_bytes_access_stale_restart(tmp_path):
    commands()  # Explicit optional native campaign, not a mock-builder full-suite test.
    with running(tmp_path / "state") as (app, base, client):
        compose(app)
        project, baseline, prefix, body = captured(app, base, client)
        assert request(client, base, prefix + "/capabilities")["runtime_configured"]
        request(client, base, prefix, {**body, "engineering_acceptance": True}, expected=400)
        initial = request(client, base, prefix, body)
        assert request(client, base, prefix, body)["job_id"] == initial["job_id"]
        path = prefix + "/" + initial["object_id"] + "/jobs/" + initial["job_id"]
        result = wait(client, base, path)
        assert result["state"] == "COMPLETED", result["source_canonical_json"]
        assert result["current_generated_candidate"] and not result["engineering_export_eligible"]
        source_path = prefix + "/" + initial["object_id"]
        saved = request(client, base, source_path)
        assert len(json.loads(saved["inputs"]["snapshot_json"])["parameters_si"]) == 165  # 81 paired stations + three explicit length inputs.
        originals = {name: binary(client, base, path + "/blobs/" + name) for name in ("source.brep", "export.step", "export.stl")}
        raw = binary(client, base, path + "/record.json")
        display = binary(client, base, path + "/preview")
        assert display and len(display) % 36 == 0
        with client.open(base + path + "/blobs/export.step") as response:
            assert "unreviewed-engine-candidate" in response.headers["Content-Disposition"]
        stages = request(client, base, path + "/stages")["stages"]
        assert stages[0]["state"] == "draft" and stages[-1]["state"] == "accepted"
        request(client, base, path + "?ignored=true", expected=400)
        other = new_project(base, client)
        request(client, base, "/api/projects/" + other["project_id"] + "/engine-geometry-builds/" + initial["object_id"], expected=404)
        viewer = app.auth.register_user(login_id="nozzle-viewer", password="Synthetic-Nozzle-Only!", display_name="Synthetic viewer", designation="Test", employee_id="NZ-VIEW", team="QA", role=UserRole.VIEWER)
        project_path = "/api/projects/" + project["project_id"]
        request(client, base, project_path + "/members", {"user_id": viewer.user_id, "capability": "VIEWER", "expected": request(client, base, project_path)["project"]["head"], "operation_id": str(uuid4())})
        reader = client_for(base, "nozzle-viewer", "Synthetic-Nozzle-Only!", "USER")
        assert binary(reader, base, path + "/blobs/export.step") == originals["export.step"]
        request(reader, base, prefix, {**body, "operation_id": str(uuid4())}, expected=403)
        coordinator = app.project_api.engine_builds.coordinator
        captured_methods = coordinator.loaded_methods
        coordinator.loaded_methods = {**captured_methods, "test-change": "3" * 64}
        assert not request(client, base, path)["current_generated_candidate"]
        coordinator.loaded_methods = captured_methods
        factory = coordinator.factory
        coordinator.factory = lambda: (_ for _ in ()).throw(RuntimeError("Synthetic removed runtime"))
        assert not request(client, base, path)["runtime_current"]
        assert not request(client, base, path)["current_generated_candidate"]
        assert binary(client, base, path + "/blobs/export.step") == originals["export.step"]
        coordinator.factory = factory
        assert app.project_api.repository.resolve_snapshot(principal(app.auth.list_users()[0]), project["project_id"], baseline.commit_id).payload == baseline.payload
        from tests.integration_tests.gui.test_project_authority_http import (
            command,
            route,
        )
        current = request(client, base, project_path + "/designs/" + baseline.object_id)
        request(client, base, route(project, current) + "/requirements", command(current, updates={"target_chamber_pressure": 6e6}))
        assert not request(client, base, path)["current_generated_candidate"]
        assert request(client, base, project_path + "/records/" + saved["authority"]["commit_id"])["upstream_current"] is False
        assert binary(client, base, path + "/record.json") == raw
    with running(tmp_path / "state", enabled=False) as (_, base, client):
        assert binary(client, base, path + "/record.json") == raw
        for name, original in originals.items():
            assert binary(client, base, path + "/blobs/" + name) == original
        assert binary(client, base, path + "/preview") == display
        assert not request(client, base, path)["current_generated_candidate"]


def test_native_failed_qa_has_no_candidate_download_and_cancellation_is_not_success(tmp_path):
    commands()
    with running(tmp_path / "state") as (app, base, client):
        workspace = compose(app)
        _, _, prefix, body = captured(app, base, client)
        body["qa_specification"]["relative_volume"]["value"] = 1e-14
        first = request(client, base, prefix, body)
        path = prefix + "/" + first["object_id"] + "/jobs/" + first["job_id"]
        failed = wait(client, base, path)
        assert failed["state"] == "FAILED" and not failed["blobs"] and not failed["current_generated_candidate"]
        request(client, base, path + "/blobs/export.step", expected=400)
        request(client, base, path + "/preview", expected=400)
        # The exact cancelled input remains inspectable; retry never inherits acceptance.
        body["qa_specification"] = qa_spec(); body["operation_id"] = str(uuid4())
        entered = []
        coordinator = app.project_api.engine_builds.coordinator
        original = coordinator.reference
        def cancelling_reference(revision):
            live = next(iter(coordinator.live))
            current = coordinator.jobs.get(principal(app.auth.list_users()[0]), first["project_id"], live)
            coordinator.cancel(principal(app.auth.list_users()[0]), first["project_id"], live, expected=current.head, operation_id="test-cancel-exact", request_hash="6" * 64)
            entered.append(live)
            return original(revision)
        coordinator.reference = cancelling_reference
        second = request(client, base, prefix, body)
        path2 = prefix + "/" + second["object_id"] + "/jobs/" + second["job_id"]
        cancelled = wait(client, base, path2)
        assert entered and cancelled["state"] == "CANCELLED" and not cancelled["blobs"] and not cancelled["selected_attempt"]
        assert workspace.supervisor is not None
