"""Real local backup/restore boundaries; all destructive fixtures use tmp_path."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
import struct
import threading
import zipfile
from pathlib import Path
from typing import Any

import pytest

from knowledge.persistence.backend import SQLitePersistenceBackend
from knowledge.workspace import backup
from knowledge.workspace.corpus import cooling_markdown_bytes
from knowledge.workspace.session import KnowledgeWorkspace
from knowledge.workspace.vault import DurableArtifactVault


def workspace(path: Path) -> KnowledgeWorkspace:
    value = KnowledgeWorkspace(path)
    value.ingest(cooling_markdown_bytes(), filename="cooling.md")
    value.conversations.create()
    return value


def hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def archive_data(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def rewritten(source: Path, target: Path, *, change: dict[str, bytes] | None = None,
              manifest_change: dict[str, Any] | None = None, reseal: bool = False) -> Path:
    values = archive_data(source)
    values.update(change or {})
    manifest = json.loads(values["backup_manifest.json"])
    manifest.update(manifest_change or {})
    if reseal:
        manifest["files"] = {name: {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                             for name, data in values.items() if name != "backup_manifest.json"}
    values["backup_manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(target, "x") as archive:
        for name, data in values.items():
            archive.writestr(name, data)
    return target


def test_v2_snapshot_relocates_without_original_root_and_retains_metadata(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    expected = original.vault.list_sources()[0]
    original.persistence.close()  # type: ignore[attr-defined]
    archive = backup.backup_workspace_root(original.root, tmp_path / "backup.zip")  # type: ignore[arg-type]
    with zipfile.ZipFile(archive.archive_path) as packed:
        manifest = json.loads(packed.read("backup_manifest.json"))
        assert manifest["format"] == "cosmos-workspace-backup-v2"
        assert set(archive.included) == set(packed.namelist())
        assert not any(name.endswith(("-wal", "-shm")) for name in packed.namelist())
        for name, entry in manifest["files"].items():
            assert hashlib.sha256(packed.read(name)).hexdigest() == entry["sha256"]
    original.root.rename(tmp_path / "old-source")  # type: ignore[union-attr]
    restored = backup.restore_workspace_root(archive.archive_path, tmp_path / "restored")
    vault = DurableArtifactVault(restored / "knowledge_vault")
    assert vault.retrieve_original(expected.source_id) == cooling_markdown_bytes()
    assert Path(vault.get(expected.source_id).storage_uri).is_relative_to(restored)
    database = SQLitePersistenceBackend(restored / "workspace.sqlite")
    assert database.get("sources", expected.source_id)["storage_uri"] == vault.get(expected.source_id).storage_uri  # type: ignore[index]
    database.close()
    recovered = KnowledgeWorkspace(restored)
    assert recovered.search_documents("regenerative cooling")
    assert recovered.list_jobs()
    assert recovered.conversations.store.list()
    recovered.persistence.close()  # type: ignore[attr-defined]


def test_valid_legacy_v1_is_explicitly_integrity_limited_and_relocated(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "new.zip")  # type: ignore[arg-type]
    values = archive_data(packed.archive_path)
    values["backup_manifest.json"] = json.dumps({"format": "cosmos-workspace-backup-v1", "root_name": "source"}).encode()
    legacy = tmp_path / "legacy.zip"
    with zipfile.ZipFile(legacy, "x") as archive:
        for name, data in values.items():
            archive.writestr(name, data)
    restored = backup.restore_workspace_root(legacy, tmp_path / "restored")
    assert DurableArtifactVault(restored / "knowledge_vault").verify(original.vault.list_sources()[0].source_id)
    receipt = json.loads(next(tmp_path.glob(".cosmos-restore-recovery-*/restore_receipt.json")).read_text())
    assert "no full payload SHA inventory" in receipt["integrity_scope"]


def test_existing_workspace_is_retained_recoverably_not_deleted(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "archive.zip")  # type: ignore[arg-type]
    live = workspace(tmp_path / "live")
    live.persistence.close()  # type: ignore[attr-defined]
    (live.root / "keep-me.txt").write_text("old private bytes")  # type: ignore[operator]
    before = hashes(live.root)  # type: ignore[arg-type]
    backup.restore_workspace_root(packed.archive_path, live.root)  # type: ignore[arg-type]
    recovery = next(tmp_path.glob(".cosmos-restore-recovery-*/previous"))
    assert hashes(recovery) == before
    assert not (live.root / "keep-me.txt").exists()  # type: ignore[operator]
    assert stat.S_IMODE(recovery.parent.stat().st_mode) == 0o700


@pytest.mark.parametrize("kind", ["missing", "not-zip", "missing-manifest", "bad-json", "future-format", "future-schema", "boolean-schema", "checksum", "crc"])
def test_invalid_archive_never_changes_existing_workspace(tmp_path: Path, kind: str) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    invalid = tmp_path / "invalid.zip"
    if kind == "not-zip":
        invalid.write_bytes(b"not a ZIP")
    elif kind == "missing-manifest":
        with zipfile.ZipFile(invalid, "x") as archive:
            archive.writestr("jobs/empty.json", b"{}")
    elif kind == "bad-json":
        rewritten(packed.archive_path, invalid, change={"backup_manifest.json": b"{}"}, manifest_change={"root_name": ""})
    elif kind == "future-format":
        rewritten(packed.archive_path, invalid, manifest_change={"format": "cosmos-workspace-backup-v99"})
    elif kind == "future-schema":
        rewritten(packed.archive_path, invalid, manifest_change={"workspace_schema_version": 99})
    elif kind == "boolean-schema":
        rewritten(packed.archive_path, invalid, manifest_change={"workspace_schema_version": True})
    elif kind == "checksum":
        name = next(name for name in archive_data(packed.archive_path) if name.startswith("jobs/"))
        rewritten(packed.archive_path, invalid, change={name: b"{}"})
    elif kind == "crc":
        invalid.write_bytes(packed.archive_path.read_bytes()[:-20])
    live = workspace(tmp_path / "live")
    live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    with pytest.raises(backup.WorkspaceBackupError):
        backup.restore_workspace_root(invalid, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]
    assert not list(tmp_path.glob(".cosmos-restore-recovery-*"))


@pytest.mark.parametrize("name", ["../escape", "/absolute", "jobs/../../escape", "jobs\\escape", "jobs//escape", "jobs/./escape", "jobs/file:stream", "auth/private.json"])
def test_zip_paths_refused_before_any_destination_creation(tmp_path: Path, name: str) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "x") as packed:
        packed.writestr("backup_manifest.json", json.dumps({"format": "cosmos-workspace-backup-v1", "root_name": "source"}))
        packed.writestr(name, b"{}")
    with pytest.raises(backup.WorkspaceBackupError):
        backup.restore_workspace_root(archive, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()
    assert not (tmp_path / "escape").exists()


@pytest.mark.parametrize("variant", ["duplicate", "case-collision", "symlink", "ancestor-file", "compression"])
def test_unsafe_member_types_and_collisions_refused(tmp_path: Path, variant: str) -> None:
    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "x") as packed:
        packed.writestr("backup_manifest.json", json.dumps({"format": "cosmos-workspace-backup-v1", "root_name": "source"}))
        if variant == "symlink":
            info = zipfile.ZipInfo("jobs/link"); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            packed.writestr(info, "../../elsewhere")
        elif variant == "ancestor-file":
            packed.writestr("jobs/x", b"{}"); packed.writestr("jobs/x/y.json", b"{}")
        elif variant == "compression":
            packed.writestr("jobs/a.json", b"{}", compress_type=zipfile.ZIP_BZIP2)
        else:
            packed.writestr("jobs/A.json", b"{}")
            if variant == "duplicate":
                with pytest.warns(UserWarning, match="Duplicate"):
                    packed.writestr("jobs/A.json", b"{}")
            else:
                packed.writestr("jobs/a.json", b"{}")
    with pytest.raises(backup.WorkspaceBackupError):
        backup.restore_workspace_root(archive, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


@pytest.mark.parametrize("limit", ["MAX_ARCHIVE_BYTES", "MAX_EXPANDED_BYTES", "MAX_MEMBERS", "MAX_MANIFEST_BYTES", "MAX_MEMBER_BYTES"])
def test_declared_limits_fail_closed_without_touching_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    live = workspace(tmp_path / "live")
    live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    monkeypatch.setattr(backup, limit, 1)
    with pytest.raises(backup.WorkspaceBackupError):
        backup.restore_workspace_root(packed.archive_path, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]


def test_valid_checksum_does_not_waive_sqlite_schema_validation(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    wrong = tmp_path / "wrong.sqlite"
    with sqlite3.connect(wrong) as connection:
        connection.execute("CREATE TABLE unexpected(secret TEXT)")
    incompatible = rewritten(packed.archive_path, tmp_path / "invalid.zip", change={"workspace.sqlite": wrong.read_bytes()}, reseal=True)
    live = workspace(tmp_path / "live"); live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    with pytest.raises(backup.WorkspaceBackupError, match="INVALID_DATABASE"):
        backup.restore_workspace_root(incompatible, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]


def test_resealed_sqlite_trigger_with_noninternal_prefix_is_rejected(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    malicious = tmp_path / "untrusted.sqlite"
    malicious.write_bytes(archive_data(packed.archive_path)["workspace.sqlite"])
    with sqlite3.connect(malicious) as connection:
        connection.execute("CREATE TRIGGER sqliteXattack AFTER UPDATE ON workspace_kv BEGIN DELETE FROM workspace_kv WHERE collection='sources'; END")
    incompatible = rewritten(packed.archive_path, tmp_path / "invalid.zip", change={"workspace.sqlite": malicious.read_bytes()}, reseal=True)
    live = workspace(tmp_path / "live"); live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    with pytest.raises(backup.WorkspaceBackupError, match="INVALID_DATABASE"):
        backup.restore_workspace_root(incompatible, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]


@pytest.mark.parametrize("area", ["jobs", "conversations", "knowledge_vault/originals", "knowledge_vault/manifests"])
def test_workspace_storage_directory_cannot_be_replaced_by_file(tmp_path: Path, area: str) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    incompatible = rewritten(packed.archive_path, tmp_path / "invalid.zip", change={area: b"not a directory"}, reseal=True)
    live = workspace(tmp_path / "live"); live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    with pytest.raises(backup.WorkspaceBackupError):
        backup.restore_workspace_root(incompatible, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]


def test_source_hash_and_untrusted_absolute_uri_are_checked(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    values = archive_data(packed.archive_path)
    name = next(name for name in values if name.startswith("knowledge_vault/manifests/"))
    record = json.loads(values[name]); record["storage_uri"] = str(tmp_path / "private-unrelated.txt")
    (tmp_path / "private-unrelated.txt").write_text("never read me")
    uri_archive = rewritten(packed.archive_path, tmp_path / "uri.zip", change={name: json.dumps(record).encode()}, reseal=True)
    restored = backup.restore_workspace_root(uri_archive, tmp_path / "restored")
    assert DurableArtifactVault(restored / "knowledge_vault").retrieve_original(record["source_id"]) == cooling_markdown_bytes()
    original_name = next(name for name in values if name.startswith("knowledge_vault/originals/"))
    corrupted = rewritten(packed.archive_path, tmp_path / "corrupt-source.zip", change={original_name: b"modified"}, reseal=True)
    with pytest.raises(backup.WorkspaceBackupError, match="SOURCE_INTEGRITY"):
        backup.restore_workspace_root(corrupted, tmp_path / "another")
    assert not (tmp_path / "another").exists()


def test_symlink_source_destination_and_archive_refused(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    link = tmp_path / "linked.zip"; link.symlink_to(packed.archive_path)
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_PATH"):
        backup.restore_workspace_root(link, tmp_path / "restored")
    (tmp_path / "destination-link").symlink_to(tmp_path / "source", target_is_directory=True)
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_PATH"):
        backup.restore_workspace_root(packed.archive_path, tmp_path / "destination-link")
    (original.root / "jobs" / "linked.json").symlink_to(tmp_path / "valid.zip")  # type: ignore[operator]
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_PATH"):
        backup.backup_workspace_root(original.root, tmp_path / "not-created.zip")  # type: ignore[arg-type]
    assert not (tmp_path / "not-created.zip").exists()


def test_backup_never_overwrites_archive_or_source(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    existing = tmp_path / "existing.zip"; existing.write_bytes(b"prior artifact")
    with pytest.raises(backup.WorkspaceBackupError, match="NO_OVERWRITE"):
        backup.backup_workspace_root(original.root, existing)  # type: ignore[arg-type]
    with pytest.raises(backup.WorkspaceBackupError, match="NO_OVERWRITE"):
        backup.backup_workspace_root(original.root, original.root / "workspace.sqlite")  # type: ignore[arg-type,operator]
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_DESTINATION"):
        backup.backup_workspace_root(original.root, original.root / "jobs" / "not-a-job.zip")  # type: ignore[arg-type,operator]
    assert existing.read_bytes() == b"prior artifact"
    packed = backup.backup_workspace_root(original.root, original.root / "backups" / "valid.zip")  # type: ignore[arg-type,operator]
    assert packed.archive_path.is_file()


def test_source_changes_abort_unpublished_backup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = workspace(tmp_path / "source")
    copy = backup._copy_regular
    changed = False
    def changing(source: Path, destination: Path) -> None:
        nonlocal changed
        copy(source, destination)
        if not changed:
            source.write_bytes(source.read_bytes() + b" ")
            changed = True
    monkeypatch.setattr(backup, "_copy_regular", changing)
    with pytest.raises(backup.WorkspaceBackupError, match="SOURCE_CHANGED"):
        backup.backup_workspace_root(original.root, tmp_path / "unpublished.zip")  # type: ignore[arg-type]
    assert not (tmp_path / "unpublished.zip").exists()


def test_sqlite_wal_snapshot_has_committed_coherent_rows_during_writer(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    database = original.root / "workspace.sqlite"  # type: ignore[operator]
    stop = threading.Event(); started = threading.Event(); failures: list[Exception] = []
    def writer() -> None:
        try:
            with sqlite3.connect(database, timeout=5) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                for index in range(500):
                    if stop.is_set():
                        break
                    with connection:
                        for key in ("left", "right"):
                            connection.execute("INSERT OR REPLACE INTO workspace_kv VALUES ('wal-test',?,?,?)", (key, json.dumps({"value": index}), "test"))
                    started.set()
        except sqlite3.Error as error:
            failures.append(error); started.set()
    thread = threading.Thread(target=writer); thread.start()
    assert started.wait(5)
    try:
        packed = backup.backup_workspace_root(original.root, tmp_path / "wal.zip")  # type: ignore[arg-type]
    finally:
        stop.set(); thread.join(5)
    assert not thread.is_alive() and not failures
    restored = backup.restore_workspace_root(packed.archive_path, tmp_path / "restored")
    with sqlite3.connect(restored / "workspace.sqlite") as connection:
        rows = connection.execute("SELECT payload FROM workspace_kv WHERE collection='wal-test'").fetchall()
        assert len(rows) == 2 and json.loads(rows[0][0]) == json.loads(rows[1][0])
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)


def test_promotion_failure_restores_existing_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    live = workspace(tmp_path / "live"); live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    rename = Path.rename
    def interrupted(path: Path, target: Path) -> Path:
        if path.name == "staged":
            raise OSError("Injected promotion failure")
        return rename(path, target)
    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(backup.WorkspaceBackupError, match="RESTORE_PROMOTION_FAILED"):
        backup.restore_workspace_root(packed.archive_path, live.root)  # type: ignore[arg-type]
    assert hashes(live.root) == before  # type: ignore[arg-type]
    assert not list(tmp_path.glob(".cosmos-restore-recovery-*"))


def test_rollback_failure_retains_private_recoverable_previous_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    live = workspace(tmp_path / "live"); live.persistence.close()  # type: ignore[attr-defined]
    before = hashes(live.root)  # type: ignore[arg-type]
    rename = Path.rename
    def interrupted(path: Path, target: Path) -> Path:
        if path.name in {"staged", "previous"}:
            raise OSError("Injected promotion and rollback failure")
        return rename(path, target)
    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(backup.WorkspaceBackupError, match="RESTORE_ROLLBACK_FAILED"):
        backup.restore_workspace_root(packed.archive_path, live.root)  # type: ignore[arg-type]
    previous = next(tmp_path.glob(".cosmos-restore-recovery-*/previous"))
    assert hashes(previous) == before and stat.S_IMODE(previous.parent.stat().st_mode) == 0o700


def test_existing_nonworkspace_directory_is_not_replaceable(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    packed = backup.backup_workspace_root(original.root, tmp_path / "valid.zip")  # type: ignore[arg-type]
    unrelated = tmp_path / "unrelated"; unrelated.mkdir(); (unrelated / "valuable.txt").write_text("retain")
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_DESTINATION"):
        backup.restore_workspace_root(packed.archive_path, unrelated)
    assert (unrelated / "valuable.txt").read_text() == "retain"


def test_forged_member_count_is_bounded_before_zipfile_allocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "forged.zip"
    with zipfile.ZipFile(archive, "x") as packed:
        packed.writestr("backup_manifest.json", b"{}")
        packed.writestr("jobs/a.json", b"{}")
    data = bytearray(archive.read_bytes())
    end = data.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", data, end + 8, 1, 1)
    archive.write_bytes(data)
    monkeypatch.setattr(backup, "MAX_MEMBERS", 1)
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("ZipFile must not allocate untrusted member objects")
    monkeypatch.setattr(backup.zipfile, "ZipFile", forbidden)
    with pytest.raises(backup.WorkspaceBackupError, match="MEMBER_LIMIT"):
        backup.restore_workspace_root(archive, tmp_path / "restored")
    assert not (tmp_path / "restored").exists()


def test_sqlite_sidecar_symlink_is_refused_before_snapshot(tmp_path: Path) -> None:
    original = workspace(tmp_path / "source")
    (tmp_path / "unrelated.txt").write_text("retain")
    (original.root / "workspace.sqlite-wal").symlink_to(tmp_path / "unrelated.txt")  # type: ignore[operator]
    with pytest.raises(backup.WorkspaceBackupError, match="UNSAFE_PATH"):
        backup.backup_workspace_root(original.root, tmp_path / "archive.zip")  # type: ignore[arg-type]
    assert (tmp_path / "unrelated.txt").read_text() == "retain"
    assert not (tmp_path / "archive.zip").exists()
