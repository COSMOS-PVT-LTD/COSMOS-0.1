"""Real authenticated preview boundaries, using only pytest-owned roots/ports."""
from __future__ import annotations

import hashlib
import http.client
import json
import zipfile
from pathlib import Path

import pytest

from api.authentication import UserRole
from api.profile import MAX_PHOTO_BYTES
from tests.integration_tests.gui.test_r01_authorization_http import cookie

pytest_plugins = ["tests.integration_tests.gui.test_release_preview_http"]

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc``\x00\x00"
    b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
)


def request(server, path, body=None, *, token=None, headers=None, method=None):
    port = server.server_address[1]
    values = {"Origin": f"http://127.0.0.1:{port}", "Content-Type": "application/json"}
    if token is not None:
        values["Cookie"] = token
    values.update(headers or {})
    raw = body if isinstance(body, bytes) else json.dumps(body) if body is not None else None
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    connection.request(method or ("POST" if body is not None else "GET"), path, raw, values)
    response = connection.getresponse()
    result = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return result


def admin(preview):
    app, server = preview
    auth = json.loads((app.root / "first-login.json").read_text())
    status, headers, body = request(server, "/api/auth/login", auth | {"login_profile": "ADMIN"})
    assert status == 200, body
    return headers["Set-Cookie"].split(";", 1)[0]


def multipart(content, filename="source.md", content_type="text/markdown"):
    boundary = "cosmos-r01-owned-acceptance"
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def ingest(preview, token, content=b"# Synthetic source\r\nregenerative cooling evidence\r\n", filename="source.md"):
    _, server = preview
    body, headers = multipart(content, filename)
    status, _, raw = request(server, "/api/ingest", body, token=token, headers=headers)
    assert status == 200, raw
    return json.loads(raw)


def backup(preview, token, **options):
    _, server = preview
    status, _, raw = request(server, "/api/backup", options, token=token)
    assert status == 200, raw
    return Path(json.loads(raw)["archive"])


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_admin_http_snapshot_restore_preserves_evidence_and_recovery(preview):
    app, server = preview
    token = admin(preview)
    source = ingest(preview, token)["source"]
    status, _, raw = request(server, "/api/conversations", {"user": "snapshot-user"}, token=token)
    assert status == 201, raw
    conversation_id = json.loads(raw)["conversation_id"]
    archive = backup(preview, token, destination="explicit-owned.zip")
    workspace = app.knowledge_workspace()
    assert archive.parent == workspace.root / "backups"
    with zipfile.ZipFile(archive) as packed:
        manifest = json.loads(packed.read("backup_manifest.json"))
        assert manifest["format"] == "cosmos-workspace-backup-v2"
        assert "workspace.sqlite" in manifest["files"]
    extra = ingest(preview, token, b"# Later source\nnot in snapshot", "later.md")["source"]
    workspace.persistence.put("acceptance", "after-snapshot", {"retained": "previous root"})
    before = hashes(workspace.root)
    status, _, raw = request(server, "/api/restore", {"archive": str(archive)}, token=token)
    assert status == 200 and json.loads(raw)["restored"] is True, raw
    assert workspace.root == app.root / "workspace_data"
    assert workspace.vault.retrieve_original(source["source_id"]) == b"# Synthetic source\r\nregenerative cooling evidence\r\n"
    restored_source = workspace.vault.get(source["source_id"])
    assert restored_source.sha256 == source["sha256"]
    assert Path(restored_source.storage_uri).is_relative_to(workspace.root)
    assert workspace.persistence.get("sources", source["source_id"])["storage_uri"] == restored_source.storage_uri
    assert workspace.persistence.get("acceptance", "after-snapshot") is None
    assert extra["source_id"] not in {item.source_id for item in workspace.list_sources()}
    assert workspace.search_documents("regenerative cooling")
    assert workspace.list_jobs()
    assert conversation_id in {item.conversation_id for item in workspace.conversations.store.list()}
    recovery = next(app.root.glob(".cosmos-restore-recovery-*/previous"))
    assert hashes(recovery) == before
    receipt = json.loads((recovery.parent / "restore_receipt.json").read_text())
    assert receipt["destination"] == str(workspace.root)
    assert hashlib.sha256((recovery / "backups" / archive.name).read_bytes()).hexdigest() == receipt["archive_sha256"]
    workspace.persistence.put("acceptance", "reopened", {"usable": True})
    assert workspace.persistence.get("acceptance", "reopened") == {"usable": True}
    assert request(server, "/api/sources", token=token)[0] == 200


@pytest.mark.parametrize("role", [UserRole.VIEWER, UserRole.ENGINEER, UserRole.REVIEWER, UserRole.APPROVER])
def test_read_roles_cannot_backup_or_restore_even_with_spoofed_admin_header(preview, role):
    app, server = preview
    authorized = admin(preview)
    ingest(preview, authorized)
    archive = backup(preview, authorized)
    token = cookie(app, server, role)
    workspace = app.knowledge_workspace()
    before = hashes(workspace.root)
    spoof = {"X-COSMOS-ROLE": "ADMIN"}
    assert request(server, "/api/sources", token=token, headers=spoof)[0] == 200
    assert request(server, "/api/backup", {}, token=token, headers=spoof)[0] == 403
    assert request(server, "/api/restore", {"archive": str(archive)}, token=token, headers=spoof)[0] == 403
    assert hashes(workspace.root) == before
    assert not list(app.root.glob(".cosmos-restore-recovery-*"))


@pytest.mark.parametrize("path,body", [("/api/backup", {}), ("/api/restore", {"archive": "unused.zip"})])
def test_backup_and_restore_require_authenticated_session(preview, path, body):
    _, server = preview
    assert request(server, path, body, headers={"X-COSMOS-ROLE": "ADMIN"})[0] == 401


@pytest.mark.parametrize("kind", ["missing", "not-zip", "truncated", "checksum", "bad-manifest"])
def test_invalid_http_archive_preserves_original_and_reopens_sqlite(preview, kind):
    app, server = preview
    token = admin(preview)
    source = ingest(preview, token)["source"]
    valid = backup(preview, token)
    invalid = valid.parent / f"invalid-{kind}.zip"
    if kind == "not-zip":
        invalid.write_bytes(b"not a ZIP")
    elif kind == "truncated":
        invalid.write_bytes(valid.read_bytes()[:-20])
    elif kind in {"checksum", "bad-manifest"}:
        with zipfile.ZipFile(valid) as original, zipfile.ZipFile(invalid, "x") as altered:
            for name in original.namelist():
                data = original.read(name)
                if kind == "bad-manifest" and name == "backup_manifest.json":
                    data = b'{"format":"unknown"}'
                if kind == "checksum" and name.startswith("jobs/"):
                    data += b" "
                altered.writestr(name, data)
    workspace = app.knowledge_workspace()
    workspace.persistence.put("acceptance", "sentinel", {"before": kind})
    before = hashes(workspace.root)
    status, _, raw = request(server, "/api/restore", {"archive": str(invalid)}, token=token)
    assert status == 400, raw
    assert hashes(workspace.root) == before
    assert workspace.persistence.get("acceptance", "sentinel") == {"before": kind}
    assert workspace.vault.verify(source["source_id"])
    workspace.persistence.put("acceptance", "after-refusal", {"usable": True})
    assert workspace.persistence.get("acceptance", "after-refusal") == {"usable": True}
    assert request(server, "/api/sources", token=token)[0] == 200
    assert not list(app.root.glob(".cosmos-restore-recovery-*"))


@pytest.mark.parametrize("action", ["backup", "restore"])
@pytest.mark.parametrize("variant", ["outside", "traversal", "symlink-outside", "symlink-inside"])
def test_http_archive_paths_cannot_escape_or_use_symlink_aliases(preview, action, variant):
    app, server = preview
    token = admin(preview)
    ingest(preview, token)
    valid = backup(preview, token)
    external = app.root / "outside.zip"
    external.write_bytes(valid.read_bytes())
    if variant == "outside":
        supplied = external
    elif variant == "traversal":
        supplied = Path("../../outside.zip")
    else:
        supplied = valid.parent / f"alias-{action}.zip"
        supplied.symlink_to(external if variant == "symlink-outside" else (valid if action == "restore" else valid.parent / "new-target.zip"))
    workspace = app.knowledge_workspace()
    before = hashes(workspace.root)
    outside_before = external.read_bytes()
    key = "archive" if action == "restore" else "destination"
    status, _, raw = request(server, f"/api/{action}", {key: str(supplied)}, token=token)
    assert status == 400, raw
    assert hashes(workspace.root) == before
    assert external.read_bytes() == outside_before
    assert not list(app.root.glob(".cosmos-restore-recovery-*"))


@pytest.mark.parametrize("role", list(UserRole))
def test_authenticated_roles_can_save_only_their_own_exact_valid_png(preview, role):
    app, server = preview
    token = cookie(app, server, role)
    body, headers = multipart(PNG, "avatar.png", "image/png")
    headers["X-COSMOS-ROLE"] = "ADMIN"
    status, _, raw = request(server, "/api/profile/photo", body, token=token, headers=headers)
    assert status == 200, raw
    url = json.loads(raw)["profile_photo_url"]
    user = app.auth.validate_token(token.split("=", 1)[1]).user
    stored = app.profiles.photo_dir / f"{user.user_id}.png"
    assert stored.read_bytes() == PNG and stored.stat().st_size > 0
    assert url == f"/assets/profiles/{user.user_id}.png"
    assert len(list(app.profiles.photo_dir.iterdir())) == 1
    status, _, downloaded = request(server, url, token=token)
    assert status == 200 and downloaded == PNG


@pytest.mark.parametrize("boundary", ["unauthenticated", "cross-origin", "empty", "over-photo-limit", "malformed"])
def test_photo_refusals_do_not_replace_preexisting_bytes(preview, boundary):
    app, server = preview
    token = cookie(app, server, UserRole.VIEWER)
    body, headers = multipart(PNG, "avatar.png", "image/png")
    assert request(server, "/api/profile/photo", body, token=token, headers=headers)[0] == 200
    before = hashes(app.profiles.photo_dir)
    content = b"" if boundary == "empty" else PNG + b"x" * MAX_PHOTO_BYTES if boundary == "over-photo-limit" else PNG
    body, headers = multipart(content, "replacement.png", "image/png")
    if boundary == "malformed":
        body = body[:-9]
    if boundary == "cross-origin":
        headers["Origin"] = "https://untrusted.invalid"
    supplied = None if boundary == "unauthenticated" else token
    status, _, raw = request(server, "/api/profile/photo", body, token=supplied, headers=headers)
    assert status == (401 if boundary == "unauthenticated" else 400), raw
    assert hashes(app.profiles.photo_dir) == before


@pytest.mark.parametrize("ending", [b"\r\n", b"--", b"\r\n\r\n", b"\r\n--"])
def test_http_document_upload_retains_exact_bytes_and_original_sha(preview, ending):
    app, _ = preview
    token = admin(preview)
    content = b"# Original synthetic evidence\r\nregenerative cooling not measured" + ending
    payload = ingest(preview, token, content)
    source = payload["source"]
    workspace = app.knowledge_workspace()
    assert workspace.vault.retrieve_original(source["source_id"]) == content
    assert source["size_bytes"] == len(content)
    assert source["sha256"] == hashlib.sha256(content).hexdigest()
    assert payload["job"]["source_hash"] == source["sha256"]
    assert workspace.persistence.get("sources", source["source_id"])["sha256"] == source["sha256"]


@pytest.mark.parametrize("path", ["/api/profile", "/api/conversations", "/api/ngg/settings"])
@pytest.mark.parametrize("raw", [b'{"bio":"a","bio":"b"}', b'{"bio":NaN}', b'{"bio":1e999}'])
def test_real_json_surfaces_refuse_duplicate_nonfinite_and_overflow(preview, path, raw):
    app, server = preview
    app.ngg_enabled = True
    token = admin(preview)
    status, _, data = request(server, path, raw, token=token)
    assert status == 400, data
    assert b"inf" not in data.lower()
