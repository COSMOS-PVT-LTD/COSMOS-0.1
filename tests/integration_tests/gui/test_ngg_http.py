"""Real authenticated transport guards. No fake native success responses."""
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
def ngg_server(tmp_path):
    app = CosmosApplication(tmp_path, new_shell=True, ngg_enabled=True)
    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    body = json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"}).encode()
    client.open(urllib.request.Request(base + "/api/auth/login", body, {"Content-Type": "application/json"})).close()
    yield app, base, client
    server.shutdown(); server.server_close()


def error(client, request):
    with pytest.raises(urllib.error.HTTPError) as caught:
        client.open(request)
    return caught.value.code, json.loads(caught.value.read())


def test_capability_requires_flag_and_never_activates_native_on_page_read(ngg_server):
    app, base, client = ngg_server
    items = json.load(client.open(base + "/api/workbenches"))["pages"][0]["items"]
    assert any(item["workbench_id"] == "native-geometry" for item in items)
    assert b"software fixtures" in client.open(base + "/app/workbench/native-geometry").read()
    assert app._ngg_workspace is None
    status, value = error(client, base + "/api/ngg/context")
    assert status == 400 and value["error"]["code"] == "NATIVE_CONFIG_REQUIRED"
    assert app._ngg_workspace is None


def test_unauthenticated_native_api_is_denied(ngg_server):
    _, base, _ = ngg_server
    status, _ = error(urllib.request.build_opener(), base + "/api/ngg/context")
    assert status == 401


@pytest.mark.parametrize("headers,code", [({"Origin": "http://evil.example"}, "INVALID_ORIGIN"),
    ({"Origin": None}, "INVALID_ORIGIN"), ({"Host": "malicious.example"}, "INVALID_HOST"),
    ({"Content-Type": "text/plain"}, "INVALID_CONTENT_TYPE")])
def test_unsafe_transport_refused_before_any_native_configuration(ngg_server, headers, code):
    app, base, client = ngg_server
    actual = {"Origin": base, "Content-Type": "application/json", **headers}
    actual = {key: value for key, value in actual.items() if value is not None}
    status, value = error(client, urllib.request.Request(base + "/api/ngg/build", b'{}', actual))
    assert status == 400 and value["error"]["code"] == code and app._ngg_workspace is None


def test_flag_off_catalog_bytes_and_existing_rocket_route_compatible(ngg_server):
    app, base, client = ngg_server
    app.ngg_enabled = False
    assert len([item for p in json.load(client.open(base + "/api/workbenches"))["pages"] for item in p["items"]]) == 12
    assert error(client, base + "/api/ngg/context")[0] == 404
    assert error(client, base + "/app/workbench/native-geometry")[0] == 404
    assert b"Rocket Engine Propulsion" in client.open(base + "/app/workbench/rocket-engine?shell=legacy").read()
    assert app._ngg_workspace is None


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.REVIEWER, UserRole.APPROVER])
def test_readonly_roles_cannot_launch_native_mutations(ngg_server, role):
    app, base, _ = ngg_server
    login_id = "read-only-" + role.value.lower()
    app.auth.register_user(login_id=login_id, password="P08-test-only-password", display_name="P08 isolated read-only fixture",
        designation="Test", employee_id="TEST", team="Local qualification", role=role)
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar.CookieJar()))
    body = json.dumps({"login_id": login_id, "password": "P08-test-only-password", "login_profile": "USER"}).encode()
    client.open(urllib.request.Request(base + "/api/auth/login", body, {"Content-Type": "application/json"})).close()
    for action in ("settings", "activate", "build", "cancel", "reimport"):
        status, value = error(client, urllib.request.Request(base + "/api/ngg/" + action, b'{}', {"Origin": base, "Content-Type": "application/json"}))
        assert status == 403 and value["error"]["code"] == "FORBIDDEN_ROLE"
    assert app._ngg_workspace is None
