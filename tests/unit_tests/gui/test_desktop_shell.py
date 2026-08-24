"""Integration tests for the COSMOS desktop HTTP shell."""

from __future__ import annotations

from http.server import HTTPServer
from http import cookiejar
from pathlib import Path
import json
import threading
import urllib.error
import urllib.request

from gui.server import CosmosApplicationHandler


def _start_server(tmp_path: Path) -> tuple[str, HTTPServer]:
    from gui.server import CosmosApplication

    class Handler(CosmosApplicationHandler):
        application = CosmosApplication(tmp_path)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return f"http://{host}:{port}", server


def _client_with_cookies() -> urllib.request.OpenerDirector:
    jar = cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def test_login_workbench_flow_and_audit(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    opener = _client_with_cookies()
    try:
        login_request = urllib.request.Request(
            f"{base}/api/auth/login",
            data=json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        login_body = json.loads(opener.open(login_request, timeout=5).read())
        assert login_body["user"]["role"] == "ADMIN"

        session_request = urllib.request.Request(f"{base}/api/auth/session")
        session_body = json.loads(opener.open(session_request, timeout=5).read())
        assert session_body["user"]["login_id"] == "cosmos-admin"

        workbenches = json.loads(opener.open(f"{base}/api/workbenches", timeout=5).read())
        assert len(workbenches["pages"]) >= 3

        hub_page = opener.open(f"{base}/app/workbenches", timeout=5).read().decode("utf-8")
        assert "workbench-grid" in hub_page

        audit = json.loads(opener.open(f"{base}/api/audit/events", timeout=5).read())
        assert any(event["action"] == "LOGIN" for event in audit["events"])
    finally:
        server.shutdown()
        server.server_close()


def test_login_page_requires_credentials(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    try:
        login_page = urllib.request.urlopen(f"{base}/", timeout=5).read().decode("utf-8")
        assert "LOGIN ID" in login_page
        assert "LOG IN" in login_page
    finally:
        server.shutdown()
        server.server_close()


def test_unauthenticated_api_is_blocked(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    try:
        try:
            urllib.request.urlopen(f"{base}/api/workbenches", timeout=5)
            raised = False
        except urllib.error.HTTPError as exc:
            raised = exc.code == 401
        assert raised
    finally:
        server.shutdown()
        server.server_close()


def test_admin_can_register_user(tmp_path: Path) -> None:
    base, server = _start_server(tmp_path)
    opener = _client_with_cookies()
    try:
        login_request = urllib.request.Request(
            f"{base}/api/auth/login",
            data=json.dumps({"login_id": "cosmos-admin", "password": "COSMOS-Dev-2026!"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        opener.open(login_request, timeout=5)

        register_request = urllib.request.Request(
            f"{base}/api/admin/users",
            data=json.dumps(
                {
                    "auto_generate": True,
                    "display_name": "Propulsion Lead",
                    "designation": "Lead Engineer",
                    "employee_id": "EMP-200",
                    "team": "Rocket Engine",
                    "role": "ENGINEER",
                },
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        created = json.loads(opener.open(register_request, timeout=5).read())
        assert created["credentials_secured"] is True
        assert "login_id" in created["one_time_credentials"]
        assert "password" in created["one_time_credentials"]
        assert len(created["one_time_credentials"]["password"]) >= 12

        users = json.loads(opener.open(f"{base}/api/admin/users", timeout=5).read())
        assert any(item["employee_id"] == "EMP-200" for item in users["users"])
    finally:
        server.shutdown()
        server.server_close()
