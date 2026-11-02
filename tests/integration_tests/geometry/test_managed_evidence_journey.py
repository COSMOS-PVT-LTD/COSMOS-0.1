"""Real native sphere→existing solver→comparison/report→restart; no hardware."""
from __future__ import annotations

import base64
import json
from dataclasses import asdict, replace
from hashlib import sha256
from uuid import uuid4

import pytest

from infrastructure.geometry import WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter
from systems.geometry.service import GeometryBuildService
from systems.projects.authority import Head
from tests.fixtures.knowledge_reports import CLAIM_ID, SOURCE_ID, add_knowledge
from tests.fixtures.vv_cases import criteria
from tests.integration_tests.gui.test_geometry_project_http import create, url
from tests.integration_tests.gui.test_project_authority_http import (
    new_project,
    request,
    running,
)

from .conftest import command
from .test_managed_study_retention import SETTINGS, terminal


@pytest.mark.parametrize("with_claim", [False, True])
def test_actual_durable_comparison_report_journey_restart(native_config, tmp_path, with_claim):
    root, native = tmp_path / "application", tmp_path / "native"
    native.mkdir()
    with WorkerSupervisor(timeout_s=45) as supervisor:
        service = GeometryBuildService(OCCTAdapter(command(native_config, "occt"), supervisor, enabled=True), native,
            step_reader=command(native_config, "step_reader"))
        try:
            with running(root) as (app, base, client):
                project = new_project(base, client, "Actual R05 evidence journey — software only")
                prefix = "/api/projects/" + project["project_id"]
                geometry = create(base, client, project)
                app.project_api.geometry.coordinator.services = lambda: {"occt": service}
                route = url(project, geometry)
                build = request(client, base, route + "/jobs", {"expected": geometry["authority"]["head"], "operation_id": str(uuid4())})
                assert terminal(client, base, route + "/jobs/" + build["job_id"])["state"] == "COMPLETED"
                values = {**SETTINGS, "cells": 64, "max_iterations": 50_000} if not with_claim else SETTINGS
                study = request(client, base, prefix + "/studies", {"geometry_job_id": build["job_id"], "settings": values,
                    "expected": asdict(Head.absent()), "operation_id": str(uuid4())})
                study_route = prefix + "/studies/" + study["authority"]["object_id"]
                run = request(client, base, study_route + "/jobs", {"expected": study["authority"]["head"], "operation_id": str(uuid4())})
                assert terminal(client, base, study_route + "/jobs/" + run["job_id"])["state"] == "COMPLETED"
                attempts = request(client, base, prefix + "/jobs")["attempts"]
                assert {item["domain"] for item in attempts} == {"geometry-fixture", "simulation-benchmark"}
                assert request(client, base, prefix + "/jobs/" + run["job_id"])["domain"] == "simulation-benchmark"
                head = asdict(Head.absent())
                def ledger(action, values):
                    nonlocal head
                    result = request(client, base, prefix + "/evidence/" + action, {**values, "expected": head, "operation_id": str(uuid4())})
                    head = result["authority"]["head"]
                    return result
                policy = ledger("declare", {"criteria": criteria()})["record"]["last_result"]["criteria_id"]
                candidate = ledger("use-run", {"run_job_id": run["job_id"]})["record"]["last_result"]["dataset_id"]
                reference = ledger("reference", {"candidate_id": candidate})["record"]["last_result"]["dataset_id"]
                assessment = ledger("assess", {"candidate_id": candidate, "reference_id": reference, "criteria_id": policy})
                # Assessment has its own identity; it must not replace the ledger CAS head.
                head = request(client, base, prefix + "/evidence")["ledger"]["authority"]["head"]
                assessment_id = assessment["authority"]["object_id"]
                claim_raw = add_knowledge(app.knowledge_workspace()) if with_claim else None
                if with_claim:
                    vault = app.knowledge_workspace().vault
                    original_source = vault.get(SOURCE_ID)
                    vault.update_record(replace(original_source, project_id="unrelated-private-project"))
                    request(client, base, prefix + "/reports", {"title":"Foreign source must be refused", "assessment_id":assessment_id,
                        "claim_ids":[CLAIM_ID], "expected":asdict(Head.absent()), "operation_id":str(uuid4())}, expected=403)
                    vault.update_record(original_source)
                report = request(client, base, prefix + "/reports", {"title": "Actual retained software evidence <script>not executed</script>",
                    "assessment_id": assessment_id, "claim_ids": [CLAIM_ID] if with_claim else [], "expected": asdict(Head.absent()), "operation_id": str(uuid4())})
                report_route = prefix + "/reports/" + report["authority"]["object_id"]
                assert report["upstream_current"] and not report["production_handoff"]
                p11 = json.loads(report["record"]["canonical_json"])
                assert p11["run_id"] == json.loads(assessment["record"]["canonical_json"])["source_run_id"]
                assert p11["status"]["experimental_validation"] == "not-performed" and not p11["status"]["independent_acceptance"]
                if with_claim:
                    assert base64.b64decode(report["record"]["claim_originals"][CLAIM_ID]["base64"]) == claim_raw
                files = {}
                for name in ("report.json", "report.md", "report.html", "package.zip"):
                    with client.open(base + report_route + "/files/" + name) as response:
                        files[name] = response.read()
                        assert sha256(files[name]).hexdigest() == response.headers["X-COSMOS-SHA256"]
                assert b"<script>not executed" not in files["report.html"]
                reviewed = request(client, base, report_route + "/review-intent", {"note": "Synthetic software inspection; not human acceptance",
                    "expected": report["authority"]["head"], "operation_id": str(uuid4())})
                assert reviewed["record"]["canonical_json"] == report["record"]["canonical_json"]
                # Unrelated new policy does not invalidate this assessment/report.
                ledger("declare", {"criteria": {**criteria(), "max_abs_error_k": .4}})
                assert request(client, base, report_route)["upstream_current"]
                if not with_claim:
                    with client.open(base+prefix+"/package?version=1&hash="+project["head"]["content_hash"]) as response:
                        package=response.read()
                    with running(tmp_path/"imported-application") as (target,target_base,target_client):
                        encoded={"package_base64":base64.b64encode(package).decode()}
                        preview=request(target_client,target_base,"/api/projects/import-preview",encoded)["preview"]
                        target_owner=next(user for user in target.auth.list_users() if user.login_id=="cosmos-admin")
                        imported=request(target_client,target_base,"/api/projects/import",{**encoded,
                            "confirmed_manifest_sha256":preview["manifest_sha256"], "user_mapping":{key:target_owner.user_id for key in preview["required_explicit_user_mapping"]},
                            "confirmed_memberships":True})
                        assert imported["import"]["project_id"]==project["project_id"]
                        retained=request(target_client,target_base,report_route)
                        assert retained["source_canonical_json"]==reviewed["source_canonical_json"] and not retained["upstream_current"]
                        imported_run=request(target_client,target_base,study_route+"/jobs/"+run["job_id"])
                        assert imported_run["state"]=="COMPLETED" and not imported_run["selected_attempt"]
            with running(root) as (app, base, client):
                reopened = request(client, base, report_route)
                assert reopened["source_canonical_json"] == reviewed["source_canonical_json"]
                # The pre-existing foundation service does not yet reconstruct
                # equation entities after restart (R11). Do not invent live
                # approval/currentness: exact captured claim/original survives.
                assert reopened["upstream_current"] is not with_claim
                if with_claim:
                    assert base64.b64decode(reopened["record"]["claim_originals"][CLAIM_ID]["base64"]) == claim_raw
                for name, raw in files.items():
                    with client.open(base + report_route + "/files/" + name) as response:
                        assert response.read() == raw
                original = request(client, base, report_route + "?commit=" + report["authority"]["commit_id"])
                assert original["source_canonical_json"] == report["source_canonical_json"]
                if with_claim:
                    workspace = app.knowledge_workspace()
                    src = workspace.vault.get(SOURCE_ID)
                    workspace.vault.update_record(replace(src, version=src.version + 1))
                    assert not request(client, base, report_route)["upstream_current"]
                else:
                    request(client, base, study_route, {"settings": {**SETTINGS, "surface_k": 325.}, "expected": study["authority"]["head"], "operation_id": str(uuid4())})
                    assert not request(client, base, report_route)["upstream_current"]
                    assert not request(client, base, prefix + "/evidence/assessments/" + assessment_id)["upstream_current"]
                assert request(client, base, report_route)["record"]["canonical_json"] == report["record"]["canonical_json"]
        finally:
            service.close()
