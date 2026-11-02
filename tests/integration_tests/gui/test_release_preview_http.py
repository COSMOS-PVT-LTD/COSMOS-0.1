"""Actual opt-in profile; no existing user root or network service is touched."""
import http.client
import json
import threading

import pytest

from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer, ReleaseProfileError


@pytest.fixture
def preview(tmp_path, monkeypatch):
    monkeypatch.setenv("COSMOS_RELEASE_PROFILE", "local-preview")
    app = CosmosApplication(tmp_path)
    class Handler(CosmosApplicationHandler):
        application = app
        def log_message(self, *_args):
            pass
    server = PreviewHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield app, server
    server.shutdown(); server.server_close(); thread.join(timeout=2)


def request(server, path, body=None, headers=None):
    port = server.server_address[1]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    value = {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"}
    value.update(headers or {})
    connection.request("POST" if body is not None else "GET", path, json.dumps(body) if body is not None else None, value)
    response = connection.getresponse(); data = response.read(); result = response.status, dict(response.getheaders()), data
    connection.close(); return result


def test_unique_bootstrap_and_response_headers(preview):
    app, server = preview
    auth = json.loads((app.root / "first-login.json").read_text())
    status, _, _ = request(server, "/api/auth/login", {"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!", "login_profile": "ADMIN"})
    assert status in {400, 401}
    status, headers, _ = request(server, "/api/auth/login", {"login_id": auth["login_id"], "password": auth["password"], "login_profile": "ADMIN"})
    assert status == 200 and "HttpOnly" in headers["Set-Cookie"]
    assert headers["X-Content-Type-Options"] == "nosniff" and headers["Cache-Control"] == "no-store"
    status, _, body = request(server, "/")
    assert status == 200 and b"COSMOS-Dev-2026!" not in body and b"first-login.json" in body


@pytest.mark.parametrize("headers,code", [
    ({"Host": "evil.example"}, "INVALID_HOST"),
    ({"Origin": "https://evil.example"}, "INVALID_ORIGIN"),
    ({"Content-Length": "16777217"}, "BODY_LIMIT"),
    ({"Transfer-Encoding": "chunked"}, "INVALID_FRAMING"),
])
def test_legacy_login_is_guarded_before_body_read(preview, headers, code):
    _, server = preview
    status, _, data = request(server, "/api/auth/login", {"unused": True}, headers)
    assert status == 400 and json.loads(data)["error"]["code"] == code


def test_public_bind_is_refused(preview):
    _, server = preview
    with pytest.raises(ReleaseProfileError):
        PreviewHTTPServer(("0.0.0.0", 0), server.RequestHandlerClass)


def test_restart_preserves_auth_and_legacy_mode_stays_available(preview):
    app, _ = preview
    original = (app.root / "first-login.json").read_bytes()
    again = CosmosApplication(app.root, new_shell=False)
    assert again.release_preview and not again.shell_flag.enabled
    assert (app.root / "first-login.json").read_bytes() == original


def test_saturation_remains_bounded_and_recovers(preview):
    _, server = preview
    for _ in range(8):
        assert server._slots.acquire(blocking=False)
    try:
        assert request(server, "/")[0] == 503
    finally:
        for _ in range(8):
            server._slots.release()
    assert request(server, "/")[0] == 200
