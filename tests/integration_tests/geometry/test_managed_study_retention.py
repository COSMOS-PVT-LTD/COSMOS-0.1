"""Actual OCCT sphere → unchanged radial solver → project retention/restart."""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from api.authentication import UserRole
from api.project_authority import principal
from infrastructure.geometry import WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter
from systems.geometry.service import GeometryBuildService
from systems.persistence.job_repository import JobState
from systems.projects.authority import Head, Membership
from tests.integration_tests.gui.test_geometry_project_http import create, url
from tests.integration_tests.gui.test_project_authority_http import (
    client_for,
    new_project,
    request,
    running,
)

from .conftest import command

SETTINGS = {"conductivity_w_m_k": 10., "generation_w_m3": 1e6, "surface_k": 300., "cells": 16,
            "relative_residual": 1e-8, "max_iterations": 10_000}


def terminal(client, base, route):
    deadline = time.monotonic()+60
    while (value := request(client, base, route))["state"] not in {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}:
        assert time.monotonic() < deadline, value
        time.sleep(.01)
    return value


def retained_monitors(client, base, route):
    values, after = [], -1
    while True:
        page = request(client, base, route+f"/monitors?limit=100&after={after}")["monitors"]
        values.extend(page)
        assert len(values) <= 1024
        if len(page) < 100:
            return values
        after = page[-1]["sequence"]


@pytest.mark.parametrize("boundary", ["current", "edited-study", "edited-geometry", "cancel-at-monitor", "late-cancel", "nonconverged", "membership-downgraded"])
def test_actual_managed_geometry_study_solver_restart(native_config, tmp_path, monkeypatch, boundary):
    root = tmp_path / "application"
    candidates = tmp_path / "native"
    candidates.mkdir()
    with WorkerSupervisor(timeout_s=45) as supervisor:
        service = GeometryBuildService(OCCTAdapter(command(native_config, "occt"), supervisor, enabled=True), candidates,
            step_reader=command(native_config, "step_reader"))
        try:
            with running(root) as (app, base, owner_client):
                project = new_project(base, owner_client, "R05.4 actual software sphere study")
                geometry = create(base, owner_client, project)
                geometry_route = url(project, geometry)
                app.project_api.geometry.coordinator.services = lambda: {"occt": service}
                native = request(owner_client, base, geometry_route+"/jobs", {"expected": geometry["authority"]["head"], "operation_id": str(uuid4())})
                assert terminal(owner_client, base, geometry_route+"/jobs/"+native["job_id"])["state"] == "COMPLETED"
                coordinator = app.project_api.studies.coordinator
                repo, jobs = app._project_authority.repository, app._project_authority.jobs
                owner = coordinator.resolve_actor(project["owner_user_id"])
                actor, client = owner, owner_client
                if boundary == "membership-downgraded":
                    user = app.auth.register_user(login_id="r054-editor", display_name="Synthetic editor", password="Synthetic-R054-Editor!",
                        designation="Test", employee_id="TEST-R054", team="Software QA", role=UserRole.ENGINEER)
                    actor = principal(user)
                    repo.set_member(owner, project["project_id"], member=actor, capability=Membership.EDITOR,
                        expected=repo.get_project(owner, project["project_id"]).head, operation_id="grant-editor")
                    client = client_for(base, "r054-editor", "Synthetic-R054-Editor!", "ENGINEER")
                values = {**SETTINGS, "max_iterations": 1} if boundary == "nonconverged" else SETTINGS
                saved = request(client, base, f"/api/projects/{project['project_id']}/studies", {"geometry_job_id": native["job_id"],
                    "settings": values, "expected": asdict(Head.absent()), "operation_id": str(uuid4())})
                route = f"/api/projects/{project['project_id']}/studies/{saved['authority']['object_id']}"
                assert saved["source_namespace"] == "p07-software-fixtures" and saved["upstream_current"] and saved["methods_current"]
                first = True
                original_monitor = jobs.append_monitor
                def monitor(job_id, payload):
                    nonlocal first
                    result = original_monitor(job_id, payload)
                    if first:
                        first = False
                        if boundary == "edited-study":
                            coordinator.save(actor, project["project_id"], saved["authority"]["object_id"], values={**values, "surface_k": 325.},
                                expected=Head(**saved["authority"]["head"]), operation_id="late-study", command_hash="3"*64)
                        elif boundary == "edited-geometry":
                            app.project_api.geometry.coordinator.save(owner, project["project_id"], geometry["authority"]["object_id"],
                                settings={"operation": "union", "backend": "occt", "voxel_m": .0005}, expected=Head(**geometry["authority"]["head"]),
                                operation_id="late-geometry", command_hash="4"*64)
                        elif boundary == "cancel-at-monitor":
                            current = jobs.get(actor, project["project_id"], job_id)
                            coordinator.cancel(actor, project["project_id"], job_id, expected=current.head, operation_id="cancel-native-monitor", request_hash="5"*64)
                        elif boundary == "membership-downgraded":
                            repo.set_member(owner, project["project_id"], member=actor, capability=Membership.VIEWER,
                                expected=repo.get_project(owner, project["project_id"]).head, operation_id="downgrade-editor")
                    return result
                monkeypatch.setattr(jobs, "append_monitor", monitor)
                original_advance = jobs.advance
                def advance(job_id, state, payload, **extra):
                    if boundary == "late-cancel" and state is JobState.COMPLETED:
                        current = jobs.get(actor, project["project_id"], job_id)
                        coordinator.cancel(actor, project["project_id"], job_id, expected=current.head, operation_id="late-cancel", request_hash="6"*64)
                    return original_advance(job_id, state, payload, **extra)
                monkeypatch.setattr(jobs, "advance", advance)
                body = {"expected": saved["authority"]["head"], "operation_id": str(uuid4())}
                admitted = request(client, base, route+"/jobs", body)
                job_route = route+"/jobs/"+admitted["job_id"]
                done = terminal(owner_client, base, job_route)
                cancelled = boundary in {"cancel-at-monitor", "late-cancel"}
                assert done["state"] == ("CANCELLED" if cancelled else "COMPLETED"), done
                assert done["selected_attempt"] is (boundary in {"current", "nonconverged"})
                assert done["input_current"] is (boundary not in {"edited-study", "edited-geometry"})
                assert not done["engineering_export_eligible"] and not done["physical_validation"]
                monitors = retained_monitors(owner_client, base, job_route)
                assert monitors
                originals = [request(owner_client, base, job_route+"/monitors/"+str(item["sequence"]))["source_canonical_json"] for item in monitors]
                record = json.loads(done["source_canonical_json"])
                if cancelled:
                    record = json.loads(record["candidate_receipt"])
                status = json.loads(record["worker_status_json"])
                assert [json.loads(value) for value in originals] == status["events"]
                raw = None
                if not cancelled:
                    with owner_client.open(base+job_route+"/dataset") as response:
                        raw = response.read()
                        assert sha256(raw).hexdigest() == response.headers["X-COSMOS-SHA256"]
                    dataset = json.loads(raw)
                    assert dataset["study_id"] == saved["study_id"] and dataset["mesh"] == json.loads(saved["mesh_json"])
                    assert not dataset["production_handoff"] and dataset["experimental_validation"] == "not-performed"
                    assert dataset["numerical_convergence"] == ("nonconverged" if boundary == "nonconverged" else "converged")
                    if boundary != "nonconverged":
                        assert dataset["solution_verification"] == "analytic-benchmark-passed"
                    else:
                        assert dataset["solution_verification"] == "not-accepted"
                else:
                    assert not done["blobs"]
                    request(owner_client, base, job_route+"/dataset", expected=404)
                if boundary == "edited-geometry":
                    assert not request(owner_client, base, route)["upstream_current"]
                    request(owner_client, base, route+"/jobs", {"expected": saved["authority"]["head"], "operation_id": str(uuid4())}, expected=400)
                if boundary != "membership-downgraded":
                    assert request(client, base, route+"/jobs", body)["job_id"] == admitted["job_id"]
            with running(root, enabled=False) as (_app, base, client):
                historical = request(client, base, route+"?commit="+saved["authority"]["commit_id"])
                assert historical["source_canonical_json"] == saved["source_canonical_json"]
                reopened = request(client, base, job_route)
                assert reopened["source_canonical_json"] == done["source_canonical_json"] and reopened["head"] == done["head"]
                assert retained_monitors(client, base, job_route) == monitors
                if raw is not None:
                    with client.open(base+job_route+"/dataset") as response:
                        assert response.read() == raw
                request(client, base, route+"/jobs", body, expected=403)
                evidence = os.environ.get("COSMOS_R05_4_EVIDENCE")
                if evidence:
                    directory = Path(evidence)
                    directory.mkdir(parents=True, exist_ok=True)
                    (directory / (boundary+".json")).write_text(json.dumps({"boundary": boundary, "state": done["state"],
                        "selected": done["selected_attempt"], "input_current": done["input_current"],
                        "study_source_sha256": sha256(saved["source_canonical_json"].encode()).hexdigest(),
                        "mesh": json.loads(saved["mesh_json"]), "study_json": saved["study_json"], "monitors": monitors,
                        "dataset_sha256": sha256(raw).hexdigest() if raw else None,
                        "exact_restart_bytes_verified": True, "physical_validation": False}, indent=2)+"\n")
        finally:
            service.close()
