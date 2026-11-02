"""Isolated diagnostic only: no user data, repository source or remote writes.

Creates its own temporary private root and an ephemeral IPv4-loopback server.
Never records passwords, cookies, tokens, private paths or fixture content.
This is a reproduction of existing authorization defects, not a fix.
"""
from __future__ import annotations

import http.client
import json
import os
import secrets
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
os.environ["COSMOS_RELEASE_PROFILE"] = "local-preview"
for flag in ("COSMOS_NEW_SHELL", "COSMOS_NGG", "COSMOS_NEW_SIM_UI", "COSMOS_NEW_VV_UI", "COSMOS_NEW_KNOWLEDGE_REPORTS_UI"):
    os.environ[flag] = "0"

from api.authentication import UserRole
from gui.server import CosmosApplication, CosmosApplicationHandler
from infrastructure.release.security import PreviewHTTPServer
from knowledge.references.rights import RightsStatus
from knowledge.workspace.access import WorkspaceRole


def main() -> None:
    fixture_root = Path(tempfile.mkdtemp(prefix="cosmos-review-security-"))
    app = CosmosApplication(fixture_root / "private-app")
    password = secrets.token_urlsafe(32)
    app.auth.register_user(login_id="review-fixture-viewer", password=password,
                          display_name="Review Fixture Viewer", designation="Fixture",
                          employee_id="REVIEW-DUMMY", team="Review", role=UserRole.VIEWER)
    workspace = app.knowledge_workspace()
    workspace.role = WorkspaceRole.ADMIN
    intake = workspace.ingest(b"This is synthetic software review fixture text, not engineering evidence.\n",
                              filename="review-fixture.txt", rights_status=RightsStatus.INTERNAL,
                              title="Software review fixture only")
    if intake.source is None:
        raise RuntimeError("Own diagnostic source could not be prepared")
    source_id = intake.source.source_id

    class Handler(CosmosApplicationHandler):
        application = app

    server = PreviewHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    cookie = ""

    def request(path: str, payload: object = None, *, extra: dict[str, str] | None = None,
                raw: bytes | None = None) -> tuple[int, dict[str, str], dict[str, object]]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
        headers = {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"}
        if cookie:
            headers["Cookie"] = cookie
        headers.update(extra or {})
        data = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
        connection.request("POST" if data is not None else "GET", path, body=data, headers=headers)
        response = connection.getresponse()
        body = response.read()
        values = dict(response.getheaders())
        status = response.status
        connection.close()
        return status, values, json.loads(body)

    result: dict[str, object] = {"scope": "Owned synthetic fixture only; isolated temporary root and ephemeral loopback port",
                                "release_profile": "local-preview", "authenticated_role": "VIEWER",
                                "user_data_touched": False, "production_source_changed": False,
                                "credential_values_recorded": False}
    try:
        status, headers, body = request("/api/auth/login", {"login_id": "review-fixture-viewer",
            "password": password, "login_profile": "VIEWER"})
        if status != 200:
            raise RuntimeError("Own viewer login failed")
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        result["login"] = {"http_status": status, "role": body["user"]["role"]}
        status, _, body = request("/api/propulsion/designs", {"name": "Review-owned dummy design"})
        design_id = body.get("design", {}).get("design_id")
        result["viewer_propulsion_create"] = {"http_status": status,
            "saved_design_created": bool(design_id and app.design_store.exists(str(design_id))),
            "expected_read_only_status": 403}
        if design_id:
            status, _, body = request(f"/api/propulsion/designs/{design_id}/save", {"name": "Viewer edited dummy"})
            result["viewer_propulsion_save"] = {"http_status": status,
                "saved_name_changed": app.design_store.load(str(design_id)).name == "Viewer edited dummy",
                "expected_read_only_status": 403}
        approval_path = f"/api/sources/{source_id}/approve"
        status, headers, _ = request(approval_path, {})
        result["viewer_knowledge_approve_without_header"] = {"http_status": status,
            "expected_status": 403, "has_preview_no_store": headers.get("Cache-Control") == "no-store",
            "has_preview_nosniff": headers.get("X-Content-Type-Options") == "nosniff"}
        status, _, body = request(approval_path, {}, extra={"X-COSMOS-ROLE": "ADMIN"})
        result["viewer_knowledge_approve_with_admin_header"] = {"http_status": status,
            "approved": body.get("approved"), "persisted_integrity_status": workspace.vault.get(source_id).integrity_status,
            "expected_status": 403}
        status, _, body = request("/api/backup", {"destination": str(fixture_root / "viewer-backup.zip")})
        result["viewer_knowledge_backup_without_header"] = {"http_status": status,
            "archive_created_inside_owned_fixture": (fixture_root / "viewer-backup.zip").is_file(),
            "expected_admin_only_status": 403}
        multipart = b"--review-boundary\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"dummy.png\"\r\nContent-Type: image/png\r\n\r\ndummy\r\n--review-boundary--\r\n"
        for path in ("/api/profile/photo", "/api/ingest"):
            status, _, body = request(path, raw=multipart,
                extra={"Content-Type": "multipart/form-data; boundary=review-boundary"})
            result["preview_multipart_" + path.rsplit("/", 1)[-1]] = {"http_status": status,
                "error_code": body.get("error", {}).get("code"), "rejected_before_route_parser": status == 400}
        status, headers, _ = request("/api/conversations", raw=b'{"user":"fixture-one","user":"fixture-two"}')
        result["knowledge_proxy_duplicate_json"] = {"http_status": status,
            "duplicate_keys_accepted": status == 201, "expected_preview_strict_json_rejection": True,
            "has_preview_no_store": headers.get("Cache-Control") == "no-store"}
        result["completed"] = True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        result["owned_server_stopped"] = not thread.is_alive()
    destination = Path(__file__).with_name("security-boundary-probe.json")
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
