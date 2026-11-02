"""Owned, isolated local preview regression for the audit's write boundaries."""
import http.client
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from api.authentication import UserRole
from knowledge.workspace.access import KnowledgeGovernanceError, WorkspaceRole
from knowledge.workspace.session import KnowledgeWorkspace

pytest_plugins = ["tests.integration_tests.gui.test_release_preview_http"]


def call(server, path, body=None, *, token=None, headers=None):
    port = server.server_address[1]
    values = {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"}
    if token:
        values["Cookie"] = token
    values.update(headers or {})
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    raw = body if isinstance(body, bytes) else json.dumps(body) if body is not None else None
    connection.request("POST" if body is not None else "GET", path, raw, values)
    response = connection.getresponse()
    data = response.read()
    result = response.status, dict(response.getheaders()), data
    connection.close()
    return result


def cookie(app, server, role):
    login = f"test-{role.value.lower()}"
    app.auth.register_user(login_id=login, password="isolated-test-password", display_name=login,
        designation="test", employee_id=login, team="test", role=role)
    status, headers, _ = call(server, "/api/auth/login",
        {"login_id": login, "password": "isolated-test-password", "login_profile": "USER"})
    assert status == 200
    return headers["Set-Cookie"].split(";", 1)[0]


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER])
def test_read_roles_cannot_write_designs_or_spoof_knowledge_admin(preview, role):
    app, server = preview
    token = cookie(app, server, role)
    spoof = {"X-COSMOS-ROLE": "ADMIN"}
    assert call(server, "/api/propulsion/designs", {"name": "unauthorized"}, token=token, headers=spoof)[0] == 403
    assert call(server, "/api/backup", {}, token=token, headers=spoof)[0] == 403
    assert call(server, "/api/sources/not-a-source/approve", {}, token=token, headers=spoof)[0] == 403
    assert not list((app.root / "knowledge_workspace" / "backups").glob("*.zip"))


def test_engineer_can_write_design_but_cannot_backup(preview):
    app, server = preview
    token = cookie(app, server, UserRole.ENGINEER)
    assert call(server, "/api/propulsion/designs", {"name": "allowed"}, token=token)[0] == 200
    assert call(server, "/api/backup", {}, token=token)[0] == 403


def test_knowledge_json_and_response_protection(preview):
    app, server = preview
    token = cookie(app, server, UserRole.VIEWER)
    status, headers, _ = call(server, "/api/graph", token=token)
    assert status == 200 and headers["Cache-Control"] == "no-store" and headers["X-Content-Type-Options"] == "nosniff"
    assert call(server, "/api/conversations", b'{"user":"a","user":"b"}', token=token)[0] == 400
    assert call(server, "/api/conversations", b'{"user":NaN}', token=token)[0] == 400


def test_context_does_not_leak_between_threads_or_exception():
    workspace = KnowledgeWorkspace(role=WorkspaceRole.VIEWER, actor_id="default")
    def observe(role):
        with workspace.as_principal(role, role.value):
            return workspace.role, workspace.actor_id
    with ThreadPoolExecutor(2) as pool:
        assert list(pool.map(observe, [WorkspaceRole.ADMIN, WorkspaceRole.VIEWER])) == [
            (WorkspaceRole.ADMIN, "ADMIN"), (WorkspaceRole.VIEWER, "VIEWER")]
    with pytest.raises(RuntimeError), workspace.as_principal(WorkspaceRole.ADMIN, "temp"):
        raise RuntimeError("synthetic failure")
    assert workspace.role is WorkspaceRole.VIEWER and workspace.actor_id == "default"
    with pytest.raises(KnowledgeGovernanceError):
        workspace.backup()


def test_valid_preview_multipart_reaches_owned_intake(preview):
    app, server = preview
    auth = json.loads((app.root / "first-login.json").read_text())
    _, headers, _ = call(server, "/api/auth/login", auth | {"login_profile": "ADMIN"})
    token = headers["Set-Cookie"].split(";", 1)[0]
    body = b'--cosmos-test\r\nContent-Disposition: form-data; name="file"; filename="sample.md"\r\nContent-Type: text/markdown\r\n\r\n# Synthetic evidence\r\nNot experimental data.\r\n--cosmos-test--\r\n'
    status, _, data = call(server, "/api/ingest", body, token=token,
        headers={"Content-Type": "multipart/form-data; boundary=cosmos-test"})
    assert status == 200, data
    assert call(server, "/api/propulsion/designs", body, token=token,
        headers={"Content-Type": "multipart/form-data; boundary=cosmos-test"})[0] == 400
