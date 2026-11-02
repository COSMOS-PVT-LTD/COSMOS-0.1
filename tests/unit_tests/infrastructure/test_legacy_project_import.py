"""Explicit raw legacy import in copies; no real project migration."""
from __future__ import annotations

import json
from hashlib import sha256

import pytest

from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.legacy_import import import_legacy, preview_legacy
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import InvalidRecord, Principal, QuotaExceeded
from systems.projects.models import PropulsionDesign

OWNER = Principal("USR-explicit-legacy-owner", "ENGINEER")


def files(tmp_path):
    directory = tmp_path / "legacy"
    directory.mkdir()
    design = PropulsionDesign("Synthetic legacy original", revision=17, engineer="Descriptive text, not ownership")
    original = json.dumps(design.to_canonical_dict(), indent=2).encode() + b"\n"
    path = directory / (design.design_id + ".json")
    path.write_bytes(original)
    return directory, path, design, original


def test_raw_bytes_available_revision_owner_mapping_and_restart_idempotency(tmp_path):
    directory, path, design, raw = files(tmp_path)
    repo = SQLiteProjectRepository(tmp_path / "target")
    project = repo.create_project(OWNER, title="Explicit test migration copy", operation_id="create")
    preview = preview_legacy(directory)
    assert path.read_bytes() == raw and not preview["writes_performed"]
    assert preview["files"][0]["available_input_revision"] == 17
    args = {"confirmed_preview": preview["preview_sha256"], "selected_owners": {design.design_id: OWNER}}
    first = import_legacy(repo, OWNER, project.project_id, directory, **args)
    second = import_legacy(repo, OWNER, project.project_id, directory, **args)
    assert first == second and path.read_bytes() == raw
    reopened = SQLiteProjectRepository(repo.files.root)
    saved = reopened.get_snapshot(OWNER, project.project_id, domain="propulsion", object_id=design.design_id)
    assert json.loads(saved.payload) == design.to_canonical_dict() and saved.input_revision == 17
    assert len(reopened.list_commit_ids(OWNER, project.project_id, domain="propulsion", object_id=design.design_id)) == 1
    assert reopened.files.read_blob(sha256(raw).hexdigest(), len(raw)) == raw
    assert inventory(reopened).unavailable_references == 0 and not second["source_files_modified"]


@pytest.mark.parametrize("fault", ["unknown-fields", "missing-fields", "duplicate-keys", "not-json", "symlink"])
def test_unsupported_sources_are_reported_not_defaulted_deleted_or_rewritten(fault, tmp_path):
    directory, path, _design, raw = files(tmp_path)
    if fault == "unknown-fields": path.write_text(json.dumps({**json.loads(raw), "unknown_future_field": 1}))
    if fault == "missing-fields": path.write_text('{"name":"Incomplete"}')
    if fault == "duplicate-keys": path.write_text('{"name":"A","name":"B"}')
    if fault == "not-json": path.write_bytes(b"not JSON")
    if fault == "symlink":
        target = tmp_path / "outside.json"
        target.write_bytes(raw)
        path.unlink()
        path.symlink_to(target)
    before = path.read_bytes()
    preview = preview_legacy(directory)
    assert preview["files"][0]["status"] == "quarantined-in-place-not-moved"
    assert path.read_bytes() == before
    if fault != "symlink":
        assert preview["files"][0]["sha256"] == sha256(before).hexdigest()


def test_preview_aggregate_budget_is_not_swallowed_as_an_unsupported_file(tmp_path, monkeypatch):
    from infrastructure.persistence import legacy_import
    for index in range(5):
        (tmp_path / f"{index}.json").write_bytes(b"unchanged")
    raw = b" " * (16 * 1024**2)
    monkeypatch.setattr(legacy_import, "original_file", lambda path: raw)
    with pytest.raises(QuotaExceeded):
        preview_legacy(tmp_path)
    assert all(path.read_bytes() == b"unchanged" for path in tmp_path.glob("*.json"))


def test_changed_preview_wrong_owner_and_ambiguous_ids_refused(tmp_path):
    directory, path, design, raw = files(tmp_path)
    repo = SQLiteProjectRepository(tmp_path / "target")
    project = repo.create_project(OWNER, title="Synthetic", operation_id="create")
    preview = preview_legacy(directory)
    with pytest.raises(InvalidRecord):
        import_legacy(repo, OWNER, project.project_id, directory, confirmed_preview=preview["preview_sha256"], selected_owners={design.design_id: Principal("USR-other", "ENGINEER")})
    path.write_bytes(raw + b" ")
    with pytest.raises(InvalidRecord):
        import_legacy(repo, OWNER, project.project_id, directory, confirmed_preview=preview["preview_sha256"], selected_owners={design.design_id: OWNER})
    (directory / "duplicate.json").write_bytes(path.read_bytes())
    with pytest.raises(InvalidRecord):
        import_legacy(repo, OWNER, project.project_id, directory, confirmed_preview=preview_legacy(directory)["preview_sha256"], selected_owners={design.design_id: OWNER})
