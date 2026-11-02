"""Actual authenticated routes, rollback and read-only science parity."""

import hashlib
import json
import threading
import urllib.error
import urllib.request
from http import cookiejar
from http.server import ThreadingHTTPServer

import pytest

from gui.server import CosmosApplication, CosmosApplicationHandler


@pytest.fixture(params=[False, True])
def app_server(tmp_path, request):
    app = CosmosApplication(tmp_path, new_shell=request.param)

    class Handler(CosmosApplicationHandler):
        application = app

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    client = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
    )
    payload = json.dumps(
        {
            "login_id": "cosmos-admin",
            "password": "COSMOS-Dev-2026!",
            "login_profile": "ADMIN",
        }
    ).encode()
    client.open(
        urllib.request.Request(
            base + "/api/auth/login",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
    ).close()
    yield base, client, request.param, tmp_path
    server.shutdown()
    server.server_close()


def test_registered_routes_and_explicit_rollback(app_server):
    base, client, enabled, _ = app_server
    pages = json.load(client.open(base + "/api/workbenches"))["pages"]
    items = [item for page in pages for item in page["items"]]
    assert len(items) == 12
    for item in items:
        response = client.open(base + item["route"])
        body = response.read()
        assert response.status == 200
        assert len(body) == int(response.headers["Content-Length"])
        assert (b'content="p04-v1"' in body) is enabled
        legacy = client.open(base + item["route"] + "?shell=legacy").read()
        assert b'content="p04-v1"' not in legacy
        assert b'class="app-frame' in legacy
    assert (
        "stage=nozzle&from=physics"
        in client.open(base + "/app/physics/compressible").url
    )


def test_dashboard_config_and_authority(app_server):
    base, client, enabled, _ = app_server
    response = client.open(base + "/app/projects")
    assert response.url.endswith("/app/projects" if enabled else "/app/workbenches")
    config = json.load(client.open(base + "/api/ui/shell"))
    assert config["enabled"] is enabled
    assert config["historicalSnapshots"] is False
    assert config["scientificBackendActivated"] is False
    assert config["jobDomain"] == "knowledge-ingestion"
    assert "UI preference" in config["projectContext"]
    for path in ["/api/ui/shell", "/api/propulsion/designs"]:
        with pytest.raises(urllib.error.HTTPError) as error:
            urllib.request.urlopen(base + path)
        assert error.value.code == 401
    assert urllib.request.urlopen(base + "/app/projects").url == base + "/"


def test_asset_allowlist(app_server):
    base, client, _, _ = app_server
    for name in [
        "app-shell/model.js",
        "app-shell/adapter.js",
        "app-shell/shell.js",
        "app-shell/styles.css",
        "design-system/tokens.css",
        "design-system/components.js",
    ]:
        response = client.open(base + "/assets/" + name)
        assert response.status == 200
        assert (
            ("javascript" in response.headers["Content-Type"])
            if name.endswith(".js")
            else ("text/css" in response.headers["Content-Type"])
        )
    for path in [
        "app-shell/contracts.d.ts",
        "app-shell/../../server.py",
        "app-shell/%2e%2e/server.py",
        "design-system/build_tokens.py",
    ]:
        with pytest.raises(urllib.error.HTTPError) as error:
            client.open(base + "/assets/" + path)
        assert error.value.code == 404


def test_shell_reads_do_not_modify_saved_design(app_server):
    base, client, _, state = app_server
    response = client.open(
        urllib.request.Request(
            base + "/api/propulsion/designs",
            data=b'{"name":"P04 HTTP fixture"}',
            headers={"Content-Type": "application/json"},
        )
    )
    design_id = json.load(response)["design"]["design_id"]
    files = list((state / "propulsion_designs").glob("*.json"))
    assert files
    before = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files
    }
    for route in [
        "/app/projects",
        "/app/workbench/rocket-engine",
        "/app/workbench/rocket-engine?shell=legacy",
        "/api/ui/shell",
        "/api/propulsion/designs",
        "/api/propulsion/designs/" + design_id,
    ]:
        client.open(base + route).close()
    assert before == {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in files
    }


def test_viewer_does_not_gain_administration_from_shell(app_server):
    from api.authentication import AuthService, UserRole

    base, _, _, state = app_server
    AuthService(state / "auth").register_user(
        login_id="p04-fixture-viewer",
        password="P04-Test-Only!",
        display_name="P04 temporary viewer",
        designation="Fixture",
        employee_id="P04-ONLY",
        team="Test fixture",
        role=UserRole.VIEWER,
    )
    viewer = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
    )
    payload = json.dumps(
        {
            "login_id": "p04-fixture-viewer",
            "password": "P04-Test-Only!",
            "login_profile": "VIEWER",
        }
    ).encode()
    viewer.open(
        urllib.request.Request(
            base + "/api/auth/login",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
    ).close()
    assert (
        json.load(viewer.open(base + "/api/ui/shell"))["scientificBackendActivated"]
        is False
    )
    for path in ["/api/admin/users", "/app/audit", "/app/admin"]:
        with pytest.raises(urllib.error.HTTPError) as error:
            viewer.open(base + path)
        assert error.value.code == 403
