"""Isolated archive/backup/restore copies, never real owner migration."""
from __future__ import annotations

import io
import sqlite3
import zipfile
from dataclasses import replace
from hashlib import sha256

import pytest

from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.portability import (
    ProjectPortability,
    TransferLimits,
    backup_store,
    require_completed_restore,
    restore_store,
)
from infrastructure.persistence.schema import (
    APPLICATION_ID,
    CURRENT_VERSION,
    SCHEMA_V1,
    SCHEMA_V2,
    SCHEMA_V3,
    SCHEMA_V4,
    SCHEMA_V5,
)
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    IntegrityFailure,
    InvalidRecord,
    Principal,
    QuotaExceeded,
)

OWNER = Principal("USR-portable-original", "ENGINEER")
TARGET = Principal("USR-portable-mapped", "ENGINEER")


def example(root):
    repo = SQLiteProjectRepository(root)
    project = repo.create_project(OWNER, title="Synthetic project archive", operation_id="new")
    saved = repo.save_snapshot(OWNER, project.project_id, domain="synthetic-storage", object_id="source", input_revision=17,
        payload=RecordPayload(b'{ "original": "synthetic, not hardware", "value": 17 }', "test.original.v1"), expected=Head.absent(), operation_id="first")
    return repo, project, saved


def test_project_package_explicit_mapping_exact_bytes_restart_idempotency(tmp_path):
    source, project, saved = example(tmp_path / "source")
    package = ProjectPortability(source).export(OWNER, project.project_id, project.head)
    target = SQLiteProjectRepository(tmp_path / "target")
    service = ProjectPortability(target)
    preview = service.preview(package)
    assert not preview["writes_performed"] and preview["required_explicit_user_mapping"] == [OWNER.user_id]
    options = {"confirmed_manifest": preview["manifest_sha256"], "users": {OWNER.user_id: TARGET}, "confirmed_memberships": True}
    first = service.import_project(TARGET, package, **options)
    assert not first["idempotent"] and service.import_project(TARGET, package, **options)["idempotent"]
    reopened = SQLiteProjectRepository(target.files.root)
    result = reopened.get_snapshot(TARGET, project.project_id, domain=saved.domain, object_id=saved.object_id)
    assert result.payload == saved.payload and result.commit_id == saved.commit_id and result.input_revision == 17
    assert result.creator_user_id == TARGET.user_id
    assert inventory(reopened).unavailable_references == 0
    receipts = ProjectPortability(reopened).transfers(TARGET, project.project_id)
    assert len(receipts) == 1
    name, original = ProjectPortability(reopened).original(TARGET, project.project_id, receipts[0]["receipt_id"])
    assert name == "original-import-metadata.json" and preview["package_sha256"].encode() in original
    with pytest.raises(AccessDenied):
        reopened.get_project(OWNER, project.project_id)
    assert source.get_snapshot(OWNER, project.project_id, domain=saved.domain, object_id=saved.object_id).payload == saved.payload


@pytest.mark.parametrize("kind", ["confirmation", "missing-map", "inactive-map", "wrong-owner", "memberships"])
def test_unconfirmed_mapping_never_changes_target(kind, tmp_path):
    source, project, _ = example(tmp_path / "source")
    raw = ProjectPortability(source).export(OWNER, project.project_id, project.head)
    target = SQLiteProjectRepository(tmp_path / "target")
    service = ProjectPortability(target)
    args = {"confirmed_manifest": service.preview(raw)["manifest_sha256"], "users": {OWNER.user_id: TARGET}, "confirmed_memberships": True}
    if kind == "confirmation": args["confirmed_manifest"] = "0"*64
    if kind == "missing-map": args["users"] = {}
    if kind == "inactive-map": args["users"] = {OWNER.user_id: replace(TARGET, active=False)}
    if kind == "wrong-owner": args["users"] = {OWNER.user_id: OWNER}
    if kind == "memberships": args["confirmed_memberships"] = False
    with pytest.raises((InvalidRecord, AccessDenied)):
        service.import_project(TARGET, raw, **args)
    assert not target.list_projects(TARGET)


@pytest.mark.parametrize("name", ["../escape", "/absolute", "blobs/../escape", "auth/passwords.json", "blobs/" + "z"*64])
def test_archive_paths_are_not_extracted(name, tmp_path):
    target = SQLiteProjectRepository(tmp_path / "target")
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        info = zipfile.ZipInfo(name)
        info.external_attr = 0o100600 << 16
        archive.writestr(info, b"synthetic")
    with pytest.raises(InvalidRecord):
        ProjectPortability(target).preview(stream.getvalue())


@pytest.mark.parametrize("kind", ["duplicate", "symlink", "compression", "hash", "missing"])
def test_archive_duplicate_link_bomb_hash_and_missing_refused(kind, tmp_path):
    source, project, _ = example(tmp_path / "source")
    raw = ProjectPortability(source).export(OWNER, project.project_id, project.head)
    with zipfile.ZipFile(io.BytesIO(raw)) as original:
        contents = {name: original.read(name) for name in original.namelist()}
    if kind == "hash": contents["metadata.json"] += b" "
    if kind == "missing": contents.pop(next(name for name in contents if name.startswith("blobs/")))
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, value in contents.items():
            info = zipfile.ZipInfo(name)
            info.external_attr = (0o120777 if kind == "symlink" else 0o100600) << 16
            info.compress_type = zipfile.ZIP_DEFLATED if kind == "compression" else zipfile.ZIP_STORED
            archive.writestr(info, value)
        if kind == "duplicate":
            with pytest.warns(UserWarning): archive.writestr("manifest.json", contents["manifest.json"])
    with pytest.raises((InvalidRecord, IntegrityFailure)):
        ProjectPortability(source).preview(stream.getvalue())


def test_explicit_export_budget_refuses_without_truncating_source(tmp_path):
    source, project, saved = example(tmp_path / "source")
    with pytest.raises(QuotaExceeded):
        ProjectPortability(source, limits=TransferLimits(max_bytes=10)).export(OWNER, project.project_id, project.head)
    assert source.get_snapshot(OWNER, project.project_id, domain=saved.domain, object_id=saved.object_id).payload == saved.payload


def test_consistent_backup_verified_fresh_restore_preserves_original(tmp_path):
    source, project, saved = example(tmp_path / "source")
    before = source.path.read_bytes()
    destination = tmp_path / "backup"
    backup_store(source, destination)
    digest = sha256((destination / "manifest.json").read_bytes()).hexdigest()
    result = restore_store(destination, tmp_path / "restored", confirmed_manifest=digest)
    assert result["target_schema"] == CURRENT_VERSION and not result["live_switch_performed"]
    assert source.path.read_bytes() == before
    restored = SQLiteProjectRepository(tmp_path / "restored")
    require_completed_restore(restored.files.root)
    assert restored.get_snapshot(OWNER, project.project_id, domain=saved.domain, object_id=saved.object_id).payload == saved.payload
    with pytest.raises(InvalidRecord):
        restore_store(destination, tmp_path / "restored", confirmed_manifest=digest)


@pytest.mark.parametrize("version,schema", [(1, SCHEMA_V1), (2, SCHEMA_V2), (3, SCHEMA_V3), (4, SCHEMA_V4), (5, SCHEMA_V5)])
def test_all_supported_schema_upgrades_copy_only_never_rewrite_original(version, schema, tmp_path):
    root = tmp_path / "old"
    root.mkdir(mode=0o700)
    path = root / "metadata.sqlite3"
    connection = sqlite3.connect(path)
    connection.executescript(schema + f"\nPRAGMA user_version={version}; PRAGMA application_id={APPLICATION_ID};")
    connection.close()
    path.chmod(0o600)
    repo = SQLiteProjectRepository(root)
    project = repo.create_project(OWNER, title="Old schema synthetic", operation_id="create")
    original = path.read_bytes()
    backup = tmp_path / "backup"
    backup_store(repo, backup)
    digest = sha256((backup / "manifest.json").read_bytes()).hexdigest()
    receipt = restore_store(backup, tmp_path / "new", confirmed_manifest=digest, upgrade=True)
    assert receipt["source_schema"] == version and receipt["target_schema"] == CURRENT_VERSION
    assert path.read_bytes() == original and SQLiteProjectRepository(root).schema_version == version
    assert SQLiteProjectRepository(tmp_path / "new").get_project(OWNER, project.project_id).title == project.title


@pytest.mark.parametrize("fault", ["checksum", "symlink", "wrong-confirmation"])
def test_restore_refuses_tampered_or_aliased_files_without_touching_original(fault, tmp_path):
    source, project, saved = example(tmp_path / "source")
    backup = tmp_path / "backup"
    backup_store(source, backup)
    digest = sha256((backup / "manifest.json").read_bytes()).hexdigest()
    blob = backup / "blobs" / sha256(saved.payload).hexdigest()
    if fault == "checksum": blob.write_bytes(b"tampered")
    if fault == "symlink":
        external = tmp_path / "outside"
        external.write_bytes(saved.payload)
        blob.unlink()
        blob.symlink_to(external)
    if fault == "wrong-confirmation": digest = "0"*64
    with pytest.raises(IntegrityFailure):
        restore_store(backup, tmp_path / "restored", confirmed_manifest=digest)
    if (tmp_path / "restored").exists():
        with pytest.raises(IntegrityFailure):
            require_completed_restore(tmp_path / "restored")
    assert source.get_snapshot(OWNER, project.project_id, domain=saved.domain, object_id=saved.object_id).payload == saved.payload


def test_incomplete_restore_fails_closed_even_with_flag_off_and_valid_database(tmp_path):
    from infrastructure.persistence.application_authority import ApplicationAuthority
    from infrastructure.persistence.portability import _write, canonical
    application = tmp_path / "application"
    root = application / "engineering_state" / "v1"
    root.parent.mkdir(mode=0o700, parents=True)
    repo = SQLiteProjectRepository(root)
    _write(root / "restore.pending", canonical({"format": "cosmos-restore-pending-v1", "source_manifest_sha256": "a"*64}))
    with pytest.raises(IntegrityFailure, match="incomplete"):
        ApplicationAuthority(application, enabled=False)
    assert repo.path.is_file() and (root / "restore.pending").is_file()
