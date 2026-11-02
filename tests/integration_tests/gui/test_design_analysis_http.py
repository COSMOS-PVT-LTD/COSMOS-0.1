"""Real captured one-command analysis; no fabricated reviewed/hardware result."""
import json

import pytest

from api.project_authority import principal
from tests.integration_tests.gui.test_project_authority_http import (
    command,
    new_project,
    request,
    running,
)
from tests.unit_tests.api.test_design_analysis import ready_case


def test_managed_analysis_missing_inputs_history_cas_and_restart(tmp_path):
    pytest.importorskip("cea")
    root = tmp_path / "state"
    with running(root) as (app, base, client):
        project = new_project(base, client)
        actor = principal(app.auth.list_users()[0])
        design, _ = ready_case()
        saved = app.project_api.service.create(actor, project["project_id"], design=design,
            operation_id="source", command_hash="1"*64)
        path = f"/api/projects/{project['project_id']}/designs/{saved.object_id}"
        before = request(client, base, path)
        body = command(before, phase3_inputs={}, phase4_inputs={})
        result = request(client, base, path+"/run/analysis", body)
        assert result["phase_status"] == "INPUT_REQUIRED"
        assert result["execution_ok"] is True and not result["workflow_complete"]
        assert result["stages"]["performance"]["status"] == "CURRENT"
        assert result["stages"]["design_review"]["outputs"]["review_verdict"] == "INCOMPLETE"
        assert result["authority"]["input_commit_id"]
        original = request(client, base, path+"?commit="+saved.commit_id)
        assert original["source_canonical_json"].encode() == saved.payload
        assert request(client, base, path+"/run/analysis", body)["authority"] == result["authority"]
        request(client, base, path+"/run/analysis", command(before), expected=409)
        assert result["design"]["subsystem_inputs"]["chamber"]["characteristic_length_m"] == .8
        canonical = result["source_canonical_json"]
        capture = app.project_api.repository.resolve_snapshot(actor, project["project_id"], result["authority"]["input_commit_id"])
        assert json.loads(capture.payload)["parameters"]["action"] == "run/analysis"
    with running(root) as (_app, base, client):
        restored = request(client, base, path)
        assert restored["source_canonical_json"] == canonical
        assert restored["design"]["workflow"]["results"]["materials"]["status"] == "NOT_CALCULATED"
