"""Real optional kernels through managed HTTP; no engineering/hardware claim."""
from __future__ import annotations

import json
import time
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from infrastructure.geometry import WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter, PicoGKAdapter
from systems.contracts.geometry import BuildState, GeometryBuildEvent
from systems.geometry.service import GeometryBuildService
from tests.integration_tests.gui.test_geometry_project_http import url
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)

from .conftest import command


@pytest.mark.parametrize("backend", ["occt", "picogk"])
@pytest.mark.parametrize("boundary", ["current", "edited-before-completion", "cancelled-after-qa"])
def test_actual_native_qa_exact_retention_restart_and_late_gates(native_config, tmp_path, monkeypatch, backend, boundary):
    root, candidates = tmp_path / "application", tmp_path / "candidates"
    candidates.mkdir()
    settings = {"operation": "difference", "backend": backend, "voxel_m": .0005}
    with WorkerSupervisor(timeout_s=45) as supervisor:
        service = GeometryBuildService((OCCTAdapter if backend == "occt" else PicoGKAdapter)(
            command(native_config, backend), supervisor, enabled=True), candidates,
            step_reader=command(native_config, "step_reader") if backend == "occt" else None)
        try:
            with running(root) as (app, base, client):
                project = new_project(base, client, "R05.3 actual native software fixtures")
                created = request(client, base, f"/api/projects/{project['project_id']}/geometry", {
                    "settings": settings, "expected": {"version": 0, "content_hash": sha256(b"").hexdigest()}, "operation_id": str(uuid4())})
                route = url(project, created)
                coordinator = app.project_api.geometry.coordinator
                coordinator.services = lambda: {backend: service}
                jobs, repo = app._project_authority.jobs, app._project_authority.repository
                actor = coordinator.resolve_actor(project["owner_user_id"])
                append = jobs.append_stage
                def observed_stage(job_id, payload):
                    receipt = append(job_id, payload)
                    event = GeometryBuildEvent.from_json(payload.data.decode())
                    if event.state is BuildState.ACCEPTED:
                        if boundary == "edited-before-completion":
                            source = repo.get_snapshot(actor, project["project_id"], domain="geometry-fixture", object_id=created["authority"]["object_id"])
                            coordinator.save(actor, project["project_id"], source.object_id,
                                settings={**settings, "operation": "union"}, expected=source.head, operation_id="late-edit", command_hash="2"*64)
                        elif boundary == "cancelled-after-qa":
                            job = jobs.get(actor, project["project_id"], job_id)
                            jobs.cancel(actor, project["project_id"], job_id, expected=job.head, operation_id="late-cancel", request_hash="3"*64)
                    return receipt
                monkeypatch.setattr(jobs, "append_stage", observed_stage)
                admitted = request(client, base, route + "/jobs", {"expected": created["authority"]["head"], "operation_id": str(uuid4())})
                job_route = route + "/jobs/" + admitted["job_id"]
                deadline = time.monotonic() + 90
                while (done := request(client, base, job_route))["state"] not in {"COMPLETED", "FAILED", "CANCELLED"}:
                    assert time.monotonic() < deadline, done
                    time.sleep(.02)
                assert done["state"] == ("CANCELLED" if boundary == "cancelled-after-qa" else "COMPLETED"), done
                assert not done["published"] and not done["engineering_export_eligible"] and not done["physical_validation"]
                assert done["selected_attempt"] is (boundary == "current")
                assert done["input_current"] is (boundary != "edited-before-completion")
                stages = request(client, base, job_route + "/stages")["stages"]
                exact_stages = [request(client, base, job_route + "/stages/" + str(item["sequence"]))["source_canonical_json"] for item in stages]
                assert json.loads(exact_stages[-1])["state"] == "accepted"
                record = json.loads(done["source_canonical_json"])
                if boundary == "cancelled-after-qa":
                    record = json.loads(record["candidate_receipt"])
                    assert not done["blobs"]
                events = json.loads(record["record_json"])["events"]
                assert [json.loads(value) for value in exact_stages] == events
                assert json.loads(record["evidence_json"])["qa-step" if backend == "occt" else "qa-stl"]["pass"]
                retained = {}
                for blob in done["blobs"]:
                    with client.open(base + job_route + "/blobs/" + blob["name"] + "/binary") as response:
                        data = response.read()
                        assert sha256(data).hexdigest() == blob["content_hash"] == response.headers["X-COSMOS-SHA256"]
                        retained[blob["name"]] = data
                if boundary != "cancelled-after-qa":
                    assert ("source.brep" if backend == "occt" else "source.vdb") in retained
                    assert ("export.step" if backend == "occt" else "export-conditioned.stl") in retained
            with running(root) as (_reopened, base, client):
                restarted = request(client, base, job_route)
                assert restarted["source_canonical_json"] == done["source_canonical_json"]
                assert restarted["head"] == done["head"] and restarted["state"] == done["state"]
                assert request(client, base, job_route + "/stages")["stages"] == stages
                for name, data in retained.items():
                    with client.open(base + job_route + "/blobs/" + name + "/binary") as response:
                        assert response.read() == data
                assert len(request(client, base, route + "/jobs")["attempts"]) == 1
                evidence = Path(native_config["evidence_directory"]) / "managed"
                evidence.mkdir(exist_ok=True)
                (evidence / f"{backend}-{boundary}.json").write_text(json.dumps({
                    "backend": backend, "boundary": boundary, "state": restarted["state"],
                    "selected_attempt": restarted["selected_attempt"], "input_current": restarted["input_current"],
                    "job_id": restarted["job_id"], "record_sha256": sha256(done["source_canonical_json"].encode()).hexdigest(),
                    "stages": stages, "blobs": done["blobs"], "exact_restart_bytes_verified": True,
                    "software_only": True, "engineering_publication": False, "physical_validation": False}, indent=2) + "\n")
        finally:
            service.close()
