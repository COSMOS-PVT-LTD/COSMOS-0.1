"""Managed HTTP/storage contracts; native-success qualification is separate."""
from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from hashlib import sha256
from uuid import uuid4

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter
from systems.geometry.authority import decode_source
from systems.geometry.service import GeometryBuildService
from systems.persistence.job_repository import BlobAttachment, JobState
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import Head
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)

SETTINGS = {"operation": "sphere", "backend": "occt", "voxel_m": 0.0005}


def create(base, client, project):
    return request(client, base, f"/api/projects/{project['project_id']}/geometry", {
        "settings": SETTINGS, "expected": asdict(Head.absent()), "operation_id": str(uuid4())})


def url(project, saved):
    return f"/api/projects/{project['project_id']}/geometry/{saved['authority']['object_id']}"


def test_managed_geometry_source_history_restart_and_flag_off(tmp_path):
    root = tmp_path / "app"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        saved = create(base, client, project)
        route = url(project, saved)
        original = saved["source_canonical_json"]
        assert saved["source_namespace"] == "p07-software-fixtures"
        source = app._project_authority.repository.get_snapshot(
            app.project_api.geometry.coordinator.resolve_actor(project["owner_user_id"]), project["project_id"],
            domain="geometry-fixture", object_id=saved["authority"]["object_id"])
        assert decode_source(source).snapshot.project_id != project["project_id"]
        edited = request(client, base, route, {"settings": {**SETTINGS, "operation": "union"},
            "expected": saved["authority"]["head"], "operation_id": str(uuid4())})
        assert edited["authority"]["input_revision"] == 1
        historical = request(client, base, route + "?commit=" + saved["authority"]["commit_id"])
        assert historical["source_canonical_json"] == original and not historical["authority"]["is_current"]
        assert len(request(client, base, route + "/history")["commits"]) == 2
        request(client, base, route, {"settings": SETTINGS, "expected": saved["authority"]["head"], "operation_id": str(uuid4())}, expected=409)
    with running(root, enabled=False) as (_app, base, client):
        assert request(client, base, route)["source_canonical_json"] == edited["source_canonical_json"]
        assert request(client, base, route + "?commit=" + saved["authority"]["commit_id"])["source_canonical_json"] == original
        request(client, base, route, {"settings": SETTINGS, "expected": edited["authority"]["head"], "operation_id": str(uuid4())}, expected=403)


@pytest.mark.parametrize("extra", [{"owner_user_id": "forged"}, {"worker_command": "forbidden"}, {"path": "/tmp"}])
def test_geometry_rejects_posted_authority_or_runtime_paths(tmp_path, extra):
    with running(tmp_path / "app") as (_app, base, client):
        project = new_project(base, client)
        request(client, base, f"/api/projects/{project['project_id']}/geometry", {
            "settings": SETTINGS, "expected": {"version": 0, "content_hash": "0"*64}, "operation_id": str(uuid4()), **extra}, expected=400)


def test_geometry_creation_denies_unknown_primitives(tmp_path):
    with running(tmp_path / "app") as (_app, base, client):
        project = new_project(base, client)
        request(client, base, f"/api/projects/{project['project_id']}/geometry", {
            "settings": {**SETTINGS, "radius_m": 0.1}, "expected": {"version": 0, "content_hash": "0"*64}, "operation_id": str(uuid4())}, expected=400)


def test_existing_worker_crash_retained_and_does_not_repeat_on_retry(tmp_path):
    root = tmp_path / "app"
    with WorkerSupervisor() as supervisor:
        candidates = tmp_path / "candidates"
        candidates.mkdir()
        # Real supervised process crash, not a native-kernel or successful-QA claim.
        service = GeometryBuildService(OCCTAdapter(WorkerCommand((sys.executable, "-c", "raise SystemExit(7)")), supervisor, enabled=True), candidates)
        with running(root) as (app, base, client):
            project = new_project(base, client)
            saved = create(base, client, project)
            route = url(project, saved)
            app.project_api.geometry.coordinator.services = lambda: {"occt": service}
            body = {"expected": saved["authority"]["head"], "operation_id": str(uuid4())}
            admitted = request(client, base, route + "/jobs", body)
            job_route = route + "/jobs/" + admitted["job_id"]
            deadline = time.monotonic() + 5
            while (job := request(client, base, job_route))["state"] not in {"COMPLETED", "FAILED"}:
                assert time.monotonic() < deadline
                time.sleep(0.01)
            assert job["state"] == "FAILED" and not job["blobs"] and not job["engineering_export_eligible"]
            original_receipt = json.loads(job["source_canonical_json"])
            assert json.loads(original_receipt["record_json"])["events"][-1]["code"] == "WORKER_CRASH"
            stages = request(client, base, job_route + "/stages")["stages"]
            assert [item["sequence"] for item in stages] == list(range(len(stages)))
            assert stages[-1]["state"] == "failed"
            for item in stages:
                exact = request(client, base, job_route + "/stages/" + str(item["sequence"]))
                assert sha256(exact["source_canonical_json"].encode()).hexdigest() == item["content_hash"]
            request(client, base, job_route + "/stages?limit=101", expected=400)
            replay = request(client, base, route + "/jobs", body)
            assert replay["job_id"] == admitted["job_id"]
            request(client, base, route, {"settings": {**SETTINGS, "operation": "union"},
                "expected": saved["authority"]["head"], "operation_id": str(uuid4())})
            assert request(client, base, route + "/jobs", body)["job_id"] == admitted["job_id"]
            assert len(request(client, base, route + "/jobs")["attempts"]) == 1
        service.close()
    with running(root) as (_app, base, client):
        reopened = request(client, base, job_route)
        assert reopened["state"] == "FAILED" and reopened["source_canonical_json"] == job["source_canonical_json"]
        assert request(client, base, job_route + "/stages")["stages"] == stages
        assert len(request(client, base, route + "/jobs")["attempts"]) == 1


def test_geometry_source_access_is_project_scoped_not_hash_scoped(tmp_path):
    with running(tmp_path / "app") as (_app, base, client):
        project = new_project(base, client)
        saved = create(base, client, project)
        other_project = new_project(base, client, "Other authorized project")
        wrong = url(other_project, saved)
        request(client, base, wrong + "?commit=" + saved["authority"]["commit_id"], expected=404)
        # Authentication still required even when a caller knows the exact object/hash.
        import urllib.request
        anonymous = urllib.request.build_opener()
        request(anonymous, base, url(project, saved), expected=401)


def test_exact_binary_source_headers_and_corruption_refusal(tmp_path):
    with running(tmp_path / "app") as (app, base, client):
        project = new_project(base, client)
        saved = create(base, client, project)
        actor = app.project_api.geometry.coordinator.resolve_actor(project["owner_user_id"])
        repo, jobs = app._project_authority.repository, app._project_authority.jobs
        source = repo.get_snapshot(actor, project["project_id"], domain="geometry-fixture", object_id=saved["authority"]["object_id"])
        job = jobs.admit(actor, source, operation_id="synthetic-attachment-test", request_hash="1"*64)
        receipt = RecordPayload(b'{"synthetic_storage_contract_only":true}', "test.synthetic.v1")
        jobs.advance(job.job_id, JobState.RUNNING, receipt)
        data = b"synthetic exact bytes - not a real STEP file"
        digest = sha256(data).hexdigest()
        jobs.advance(job.job_id, JobState.COMPLETED, receipt, actor=actor,
            attachments=(BlobAttachment("export.step", data, digest, "artifact"),))
        route = url(project, saved) + "/jobs/" + job.job_id
        with client.open(base + route + "/blobs/export.step/binary") as response:
            assert response.read() == data
            assert response.headers["X-COSMOS-SHA256"] == digest
            assert response.headers["Cache-Control"] == "no-store" and response.headers["Vary"] == "Cookie"
            assert "not-engineering-publication" in response.headers["X-COSMOS-Scope"]
        listed = request(client, base, url(project, saved) + "/jobs")["attempts"]
        assert "source_canonical_json" not in listed[0]  # List is metadata, not project-sized receipts.
        assert request(client, base, route + "/inspect")["byte_integrity"] is True
        (repo.files.blobs / digest).write_bytes(b"corrupt disposable test blob")
        request(client, base, route + "/inspect", expected=503)
        request(client, base, route + "/blobs/export.step/binary", expected=503)
