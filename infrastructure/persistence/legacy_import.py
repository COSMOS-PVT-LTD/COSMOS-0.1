"""Explicit legacy JSON preview/import; no guessing owners or lost revisions."""
from __future__ import annotations

import json
import os
import stat
from hashlib import sha256
from pathlib import Path
from typing import Any

from infrastructure.persistence.portability import canonical
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository, _stamp
from systems.persistence.project_repository import RecordPayload, _unique_pairs
from systems.projects.authority import (
    Head,
    IntegrityFailure,
    InvalidRecord,
    Principal,
    QuotaExceeded,
    SchemaMismatch,
)
from systems.projects.models import PropulsionDesign


def original_file(path: Path, limit: int = 16 * 1024**2) -> bytes:
    # Existing legacy files need not have new-store private modes. They are
    # read-only inputs: never chmod, rename, truncate or claim arbitrary aliases.
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise IntegrityFailure("Legacy paths must not traverse aliases.")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or info.st_size > limit:
            raise InvalidRecord("Legacy source must be a bounded owned regular original.")
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise InvalidRecord("Legacy file grew beyond its byte budget.")
    return raw


def parse_original(raw: bytes) -> PropulsionDesign:
    value = json.loads(raw, object_pairs_hook=_unique_pairs)
    if not isinstance(value, dict):
        raise InvalidRecord("Legacy design must be an exact JSON object.")
    design = PropulsionDesign.from_canonical_dict(value)
    # The compatibility adapter must not fill absent fields, drop unknown data
    # or infer an earlier revision. Unsupported schemas remain untouched.
    if design.to_canonical_dict() != value:
        raise SchemaMismatch("Legacy schema cannot round-trip exactly; preserve and review rather than default fields.")
    return design


def preview_legacy(directory: Path) -> dict[str, Any]:
    if not directory.is_absolute() or not directory.is_dir() or any(p.is_symlink() for p in (directory, *directory.parents)):
        raise InvalidRecord("Choose an explicit non-aliased existing legacy directory.")
    paths = sorted(directory.glob("*.json"))
    if len(paths) > 1000:
        raise InvalidRecord("Legacy preview is limited to1000 files; choose an explicitly reviewed subset.")
    rows = []
    total = 0
    for path in paths:
        row: dict[str, Any] = {"filename": path.name}
        try:
            raw = original_file(path)
            row.update({"sha256": sha256(raw).hexdigest(), "bytes": len(raw)})
            total += len(raw)
            if total > 64 * 1024**2:
                raise QuotaExceeded("Preview exceeds64MiB; choose an explicit subset.")
            design = parse_original(raw)
            rows.append({"filename": path.name, "sha256": sha256(raw).hexdigest(), "bytes": len(raw), "status": "supported",
                "design_id": design.design_id, "available_input_revision": design.revision,
                "unrecorded_revisions_reconstructed": False, "source_engineer_metadata": design.engineer})
        except QuotaExceeded:
            raise
        except Exception as error:
            if isinstance(error, (KeyboardInterrupt, SystemExit)):
                raise
            rows.append({**row, "status": "quarantined-in-place-not-moved", "reason": type(error).__name__})
    value = {"format": "cosmos-legacy-preview-v1", "directory": str(directory), "files": rows,
             "owner_mapping": "Explicit active owner per selected design required; engineer text is not an account identity",
             "writes_performed": False}
    return {**value, "preview_sha256": sha256(canonical(value)).hexdigest()}


def import_legacy(repository: SQLiteProjectRepository, actor: Principal, project_id: str, directory: Path, *,
                  confirmed_preview: str, selected_owners: dict[str, Principal]) -> dict[str, Any]:
    if repository.schema_version < 6:
        raise SchemaMismatch("Legacy receipts require reviewed schema6; no existing store upgraded.")
    preview = preview_legacy(directory)
    if confirmed_preview != preview["preview_sha256"] or not selected_owners:
        raise InvalidRecord("Confirm the exact preview and explicit supported design owner mapping.")
    rows = {row["design_id"]: row for row in preview["files"] if row["status"] == "supported"}
    if len(rows) != sum(row["status"] == "supported" for row in preview["files"]):
        raise InvalidRecord("Ambiguous duplicate legacy design identities refused.")
    if set(selected_owners) - rows.keys():
        raise InvalidRecord("Unknown/corrupt/unsupported originals cannot be silently imported.")
    actor.require(write=True)
    for owner in selected_owners.values():
        owner.require(write=True)
        if owner.user_id != actor.user_id:
            raise InvalidRecord("Each import must be performed by its explicitly mapped active owner; no ownership guessing.")
    completed = []
    for design_id in sorted(selected_owners):
        row = rows[design_id]
        raw = original_file(directory / row["filename"])
        if sha256(raw).hexdigest() != row["sha256"]:
            raise IntegrityFailure("Legacy source changed after preview.")
        design = parse_original(raw)
        receipt_id = sha256(canonical({"project": project_id, "file": row["filename"], "hash": row["sha256"], "owner": actor.user_id})).hexdigest()
        # Original byte receipt is durable before managed routing can begin.
        # A crash here is resumable; it never fabricates a completed calculation.
        with repository._transaction(write=True) as connection:
            repository._authorize(connection, actor, project_id, owner=True, write=True)
            if connection.execute("SELECT 1 FROM transfer_receipts WHERE receipt_id=?", (receipt_id,)).fetchone() is None:
                repository.files.reserve(len(raw))
                repository.files.install_blob(raw, row["sha256"])
                connection.execute("INSERT INTO transfer_receipts VALUES(?,?,?,?,?,?,?)", (receipt_id, project_id, "legacy-import", row["sha256"], len(raw), actor.user_id, _stamp()))
                repository._event(connection, actor, project_id, "legacy.original-retained", {**row, "receipt_id": receipt_id, "explicit_owner": actor.user_id})
                repository._check_project_budget(connection, project_id)
        saved = repository.save_snapshot(actor, project_id, domain="propulsion", object_id=design_id,
            input_revision=design.revision, payload=RecordPayload.from_design(design), expected=Head.absent(), operation_id="legacy-" + receipt_id,
            command_hash=receipt_id, purpose="create", response_payload=canonical({"original_sha256": row["sha256"], "filename": row["filename"],
                "receipt_id": receipt_id, "available_input_revision": design.revision, "unrecorded_revisions_reconstructed": False}))
        completed.append({"design_id": design_id, "commit_id": saved.commit_id, "original_sha256": row["sha256"], "receipt_id": receipt_id})
    return {"imports": completed, "quarantined_in_place": [row for row in preview["files"] if row["status"] != "supported"], "source_files_modified": False}
