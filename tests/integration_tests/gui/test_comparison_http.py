"""Actual authenticated HTTP, strict imports and default-off isolation."""
import json
import threading
import urllib.error
import urllib.request
from http import cookiejar

import pytest

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler, ThreadingHTTPServer
from tests.fixtures.vv_cases import criteria, dataset


@pytest.fixture
def server(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, comparison_enabled=True)
    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args): pass
    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    base = f"http://127.0.0.1:{http.server_port}"
    client.open(urllib.request.Request(base + "/api/auth/login", json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode(), {"Content-Type": "application/json"})).close()
    yield app, base, client
    http.shutdown(); http.server_close(); thread.join()
    if app._comparison_workspace is not None: app._comparison_workspace.close()


def post(client, base, action, value, headers=None):
    req = urllib.request.Request(base + "/api/comparison/" + action, json.dumps(value).encode(), {"Content-Type": "application/json", "Origin": base, **(headers or {})})
    try:
        with client.open(req) as response: return response.status, json.load(response)
    except urllib.error.HTTPError as response:
        return response.code, json.load(response)


def test_empty_context_does_not_activate_simulation_or_native(server):
    app, base, client = server
    assert b"Comparison and V&amp;V" in client.open(base + "/app/workbench/comparison").read().replace(b"Comparison and V&V", b"Comparison and V&amp;V")
    context = json.load(client.open(base + "/api/comparison/context"))
    assert context["candidate"] is None and context["production_handoff"] is False
    assert app._simulation_workspace is None and app._ngg_workspace is None
    pages = json.load(client.open(base + "/api/workbenches"))["pages"]
    assert sum(i["workbench_id"] == "comparison" for p in pages for i in p["items"]) == 1


def test_default_off_rollback_and_invalid_flag(tmp_path, server):
    app, base, client = server; app.comparison_enabled = False
    with pytest.raises(urllib.error.HTTPError) as caught: client.open(base + "/api/comparison/context")
    assert caught.value.code == 404 and app._comparison_workspace is None
    assert b'initWorkbenchDetail("code-comparison")' in client.open(base + "/app/workbench/code-comparison").read()
    assert not CosmosApplication(tmp_path / "default").comparison_enabled
    assert not CosmosApplication(tmp_path / "no-shell", new_shell=False, comparison_enabled=True).comparison_enabled


@pytest.mark.parametrize("headers,code", [({"Origin": "https://evil.example"}, "INVALID_ORIGIN"), ({"Host": "evil.example"}, "INVALID_HOST"), ({"Content-Type": "text/plain"}, "INVALID_CONTENT_TYPE")])
def test_transport_rejected_before_service(server, headers, code):
    app, base, client = server
    status, value = post(client, base, "criteria", {"criteria": criteria()}, headers)
    assert status == 400 and value["error"]["code"] == code and app._comparison_workspace is None


def test_actual_import_assessment_receipt_and_review_cannot_publish(server):
    _, base, client = server
    assert post(client, base, "criteria", {"criteria": criteria()})[0] == 200
    p = json.load(client.open(base + "/api/comparison/context"))["criteria"][0]["criteria_id"]
    a = post(client, base, "import", {"dataset": dataset()})[1]["dataset_id"]
    b = post(client, base, "import", {"dataset": dataset("experimental", "2", [.1]*4)})[1]["dataset_id"]
    status, value = post(client, base, "assess", {"candidate_id": a, "reference_id": b, "criteria_id": p})
    assert status == 200 and value["report"]["experimental_validation"] == "evidence-pending-independent-review"
    assert value["report"]["combined_standard_uncertainty_k"] is None
    receipt = json.load(client.open(base + "/api/comparison/reports/" + value["report_id"]))
    assert receipt["report"] == value["report"] and receipt["freshness"] == "not-assessed"
    intent = post(client, base, "review-intent", {"report_id": value["report_id"], "note": "Synthetic contract test, not actual human signoff"})[1]
    assert intent["independent_acceptance"] is False
    assert post(client, base, "production-handoff", {})[0] == 403


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER])
def test_readonly_roles_cannot_import_or_accept(server, role):
    app, base, _ = server
    login = "p10-" + role.value.lower()
    app.auth.register_user(login_id=login, password="P10-synthetic-test-password", display_name="P10 test", designation="Test", employee_id="TEST", team="Local", role=role)
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    client.open(urllib.request.Request(base + "/api/auth/login", json.dumps({"login_id": login, "password": "P10-synthetic-test-password", "login_profile": "USER"}).encode(), {"Content-Type": "application/json"})).close()
    assert post(client, base, "import", {"dataset": dataset()})[0] == 403
    assert post(client, base, "production-handoff", {})[0] == 403
    assert app._ngg_workspace is None


@pytest.mark.parametrize("body", [b'{"dataset":{},"dataset":{}}', b'{"dataset":NaN}', b'[]', b'{"path":"/etc/passwd"}', b'{"base64":"abc","provenance":{},"argv":["sh"]}'])
def test_untrusted_and_duplicate_payloads(server, body):
    app, base, client = server
    req = urllib.request.Request(base + "/api/comparison/import", body, {"Content-Type": "application/json", "Origin": base})
    with pytest.raises(urllib.error.HTTPError) as caught: client.open(req)
    assert caught.value.code == 400 and app._comparison_workspace is None


def test_unauthenticated_and_oversized_requests(server):
    app, base, client = server
    with pytest.raises(urllib.error.HTTPError) as caught: urllib.request.urlopen(base + "/api/comparison/context")
    assert caught.value.code == 401
    req = urllib.request.Request(base + "/api/comparison/import", b'{}', {"Content-Type": "application/json", "Origin": base, "Content-Length": str(3*1024**2)})
    with pytest.raises(urllib.error.HTTPError) as caught: client.open(req)
    assert caught.value.code == 400 and app._comparison_workspace is None
