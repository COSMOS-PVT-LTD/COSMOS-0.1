"""Release preview evidence and security boundaries, never physical acceptance."""
import json
import os
import platform
import stat
from email.message import Message
from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.release.inventory import (
    contract_registry,
    sha,
    source_files,
    verify_registry,
)
from infrastructure.release.security import (
    ReleaseProfileError,
    guard,
    preview_enabled,
    private_bootstrap,
    strict_json,
)
from scripts.build_release_preview import build

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("value,expected", [(None, False), ("", False), ("local-preview", True)])
def test_profile_is_explicit(value, expected):
    assert preview_enabled(value) is expected


@pytest.mark.parametrize("value", ["production", "true", "1", "LOCAL-PREVIEW"])
def test_profile_cannot_silently_authorize_production(value):
    with pytest.raises(ReleaseProfileError, match="production is not authorized"):
        preview_enabled(value)


def test_bootstrap_is_private_unique_and_restart_stable(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    first = private_bootstrap(a)
    assert len(first) >= 32 and first != "COSMOS-Dev-2026!"
    assert private_bootstrap(a) == first != private_bootstrap(b)
    assert stat.S_IMODE(a.stat().st_mode) == 0o700
    assert stat.S_IMODE((a / "first-login.json").stat().st_mode) == 0o600


def test_legacy_root_not_changed(tmp_path):
    auth = tmp_path / "auth"
    auth.mkdir(); (auth / "users.sqlite").write_bytes(b"existing legacy fixture")
    with pytest.raises(ReleaseProfileError) as error:
        private_bootstrap(tmp_path)
    assert error.value.code == "LEGACY_DATA_ROOT"
    assert (auth / "users.sqlite").read_bytes() == b"existing legacy fixture"
    assert not (tmp_path / "first-login.json").exists()


@pytest.mark.parametrize("target", ["root", "auth", "database", "secret", "credential"])
def test_symlinked_preview_credentials_are_refused_before_migration(tmp_path, target):
    outside = tmp_path / "outside"; outside.mkdir()
    root = tmp_path / "preview"; root.mkdir()
    path = {"root": root, "auth": root / "auth", "database": root / "auth/users.sqlite",
            "secret": root / "auth/session.secret", "credential": root / "first-login.json"}[target]
    if target == "root":
        root.rmdir()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ReleaseProfileError):
        private_bootstrap(root)
    assert list(outside.iterdir()) == []


def test_world_readable_first_login_refused(tmp_path):
    private_bootstrap(tmp_path)
    (tmp_path / "first-login.json").chmod(0o644)
    with pytest.raises(ReleaseProfileError):
        private_bootstrap(tmp_path)


def handler(extra=()):
    headers = Message()
    for name, value in [("Host", "127.0.0.1:8840"), *extra]:
        headers[name] = value
    return SimpleNamespace(headers=headers, server=SimpleNamespace(server_address=("127.0.0.1", 8840)), client_address=("127.0.0.1", 1))


@pytest.mark.parametrize("extra,code", [
    ([("Host", "evil.example")], "INVALID_HOST"),
    ([("Transfer-Encoding", "chunked")], "INVALID_FRAMING"),
    ([("Content-Length", "1"), ("Content-Length", "1")], "INVALID_FRAMING"),
    ([("Content-Length", "9" * 5000)], "INVALID_FRAMING"),
    ([("Content-Length", "-1")], "INVALID_FRAMING"),
    ([("Content-Length", "16777217")], "BODY_LIMIT"),
    ([("Content-Length", "1")], "INVALID_FRAMING"),
    ([("Sec-Fetch-Site", "cross-site")], "INVALID_ORIGIN"),
])
def test_ambiguous_or_hostile_get_is_refused(extra, code):
    with pytest.raises(ReleaseProfileError) as error:
        guard(handler(extra), "GET")
    assert error.value.code == code


@pytest.mark.parametrize("extra,code", [
    ([], "INVALID_ORIGIN"),
    ([("Origin", "https://evil.example")], "INVALID_ORIGIN"),
    ([("Origin", "http://127.0.0.1:8840")], "INVALID_FRAMING"),
    ([("Origin", "http://127.0.0.1:8840"), ("Content-Length", "2"), ("Content-Type", "text/plain")], "INVALID_CONTENT_TYPE"),
])
def test_mutation_guards_include_login(extra, code):
    with pytest.raises(ReleaseProfileError) as error:
        guard(handler(extra), "POST")
    assert error.value.code == code


def test_valid_loopback_request():
    guard(handler(), "GET")
    guard(handler([("Origin", "http://127.0.0.1:8840"), ("Content-Type", "application/json"), ("Content-Length", "2")]), "POST")


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'[]', b'\xff', b'{'])
def test_strict_preview_json_has_no_duplicate_nonfinite_or_encoding_fallback(raw):
    with pytest.raises(ReleaseProfileError):
        strict_json(raw)
    assert strict_json(b'{"x":1}') == {"x": 1}


def test_contract_freeze_is_hashed_and_escape_refused():
    value = contract_registry(ROOT)
    verify_registry(ROOT, value)
    value["wire_version"] = "changed"
    with pytest.raises(ValueError, match="checksum"):
        verify_registry(ROOT, value)


def test_source_inventory_excludes_private_state():
    files = source_files(ROOT)
    assert files and all(not name.startswith(("docs/", "tests/", ".venv", "cache/", "dist/")) for name in files)
    assert files["validation/reporting.py"] == sha(ROOT / "validation/reporting.py")


@pytest.mark.skipif(platform.system() != "Darwin" or platform.machine() != "arm64", reason="Only local macOS arm64 preview packaging is claimed")
def test_preview_package_is_repeatable_and_never_overwrites(tmp_path):
    import sys
    a = build(ROOT, tmp_path / "a", Path(sys.executable))
    b = build(ROOT, tmp_path / "b", Path(sys.executable))
    one = {str(p.relative_to(a)): sha(p) for p in a.rglob("*") if p.is_file()}
    two = {str(p.relative_to(b)): sha(p) for p in b.rglob("*") if p.is_file()}
    assert one == two
    manifest = json.loads((a / "Contents/Resources/preview-manifest.json").read_text())
    assert not manifest["standalone"] and not manifest["native_libraries_distributed"]
    assert os.access(a / "Contents/MacOS/cosmos-launcher", os.X_OK)
    with pytest.raises(ValueError, match="new output"):
        build(ROOT, tmp_path / "a", Path(sys.executable))
