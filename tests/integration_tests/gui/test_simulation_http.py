"""Real authentication/transport/default-off checks, no fake solver evidence."""
import json
import threading
import urllib.error
import urllib.request
from http import cookiejar
from http.server import ThreadingHTTPServer

import pytest

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler


@pytest.fixture
def server(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, simulation_enabled=True)
    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    base = f"http://127.0.0.1:{server.server_port}"
    client.open(urllib.request.Request(base + "/api/auth/login", json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode(), {"Content-Type": "application/json"})).close()
    yield app, base, client
    server.shutdown(); server.server_close(); thread.join()
    if app._simulation_workspace is not None:
        app._simulation_workspace.close()


def error(client, request):
    with pytest.raises(urllib.error.HTTPError) as caught:
        client.open(request)
    return caught.value.code, json.loads(caught.value.read())


def post(client, base, action, data, headers=None):
    return client.open(urllib.request.Request(base + "/api/simulation/" + action, json.dumps(data).encode(), {"Content-Type": "application/json", "Origin": base, **(headers or {})}))


def test_preview_context_empty_and_does_not_activate_native(server):
    app, base, client = server
    assert b"steady spherical conduction" in client.open(base + "/app/workbench/simulation").read()
    context = json.load(client.open(base + "/api/simulation/context"))
    assert context["study"] is None and context["production_handoff"] is False
    assert app._ngg_workspace is None
    items = [item for page in json.load(client.open(base + "/api/workbenches"))["pages"] for item in page["items"]]
    assert next(item for item in items if item["workbench_id"] == "simulation")["status"] == "active"


def test_rollback_restores_legacy_bytes_catalog_and_no_backend(server):
    app, base, client = server
    app.simulation_enabled = False
    assert error(client, base + "/api/simulation/context")[0] == 404
    assert b'initWorkbenchDetail("simulation")' in client.open(base + "/app/workbench/simulation").read()
    items = [item for page in json.load(client.open(base + "/api/workbenches"))["pages"] for item in page["items"]]
    assert next(item for item in items if item["workbench_id"] == "simulation")["status"] == "planned"
    assert app._simulation_workspace is None and app._ngg_workspace is None


def test_unauthenticated_access_refused(server):
    _, base, _ = server
    assert error(urllib.request.build_opener(), base + "/api/simulation/context")[0] == 401


@pytest.mark.parametrize("headers,code", [({"Origin": "http://evil.example"}, "INVALID_ORIGIN"), ({"Host": "evil.example"}, "INVALID_HOST"), ({"Content-Type": "text/plain"}, "INVALID_CONTENT_TYPE")])
def test_transport_refused_before_backend(server, headers, code):
    app, base, client = server
    status, data = error(client, urllib.request.Request(base + "/api/simulation/run", b'{}', {"Origin": base, "Content-Type": "application/json", **headers}))
    assert status == 400 and data["error"]["code"] == code and app._simulation_workspace is None


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER])
def test_readonly_role_cannot_mutate_or_grant_engineering_acceptance(server, role):
    app, base, _ = server
    login = "p09-test-" + role.value.lower()
    app.auth.register_user(login_id=login, password="P09-local-test-only-password", display_name="P09 fixture", designation="Test", employee_id="TEST", team="Local", role=role)
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    client.open(urllib.request.Request(base + "/api/auth/login", json.dumps({"login_id": login, "password": "P09-local-test-only-password", "login_profile": "USER"}).encode(), {"Content-Type": "application/json"})).close()
    for action in ("handoff", "settings", "activate", "run", "cancel", "production-handoff"):
        status, data = error(client, urllib.request.Request(base + "/api/simulation/" + action, b'{}', {"Origin": base, "Content-Type": "application/json"}))
        assert status == 403 and data["error"]["code"] == "FORBIDDEN_ROLE"
    assert app._ngg_workspace is None and app._simulation_workspace is None


def test_admin_still_cannot_create_production_acceptance(server):
    _, base, client = server
    status, value = error(client, urllib.request.Request(base + "/api/simulation/production-handoff", b'{}', {"Origin": base, "Content-Type": "application/json"}))
    assert status == 403 and value["error"]["code"] == "ENGINEERING_ACCEPTANCE_REQUIRED"


@pytest.mark.parametrize("body,code", [(b'{"study_id":"a","study_id":"b"}', "DUPLICATE_FIELD"), (b'{"study_id":NaN}', "INVALID_REQUEST"), (b'{"study_id":"a","path":"/tmp/a"}', "INVALID_REQUEST"), (b'[]', "INVALID_REQUEST")])
def test_untrusted_payload_refused(server, body, code):
    _, base, client = server
    status, data = error(client, urllib.request.Request(base + "/api/simulation/run", body, {"Origin": base, "Content-Type": "application/json"}))
    assert status == 400 and data["error"]["code"] == code
