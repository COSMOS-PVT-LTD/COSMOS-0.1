"""Explicit exact-byte recovery of ONE missing, already-referenced job artifact.

No record deletion, schema migration, new object/job, integrity bypass or source
substitution. Default is a read-only preview; apply binds its exact preview hash.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from hashlib import sha256
from pathlib import Path

from infrastructure.persistence.durable_jobs import SQLiteJobRepository
from infrastructure.persistence.files import CoordinatorLease
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository

TABLES = (
    "commits",
    "durable_job_events",
    "durable_job_blobs",
    "durable_geometry_stages",
    "durable_simulation_monitors",
    "transfer_receipts",
)


def read_references(store, digest):
    database = store / "metadata.sqlite3"
    if (
        not store.is_absolute()
        or store != store.resolve()
        or not database.is_file()
        or database.is_symlink()
    ):
        raise ValueError(
            "Explicit existing real authority store required; no initialization"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Exact expected SHA256 required")
    references = []
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        tables = {
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        for table in TABLES:
            if table in tables:
                references.extend(
                    {"table": table, "byte_length": r[0]}
                    for r in connection.execute(
                        f"SELECT byte_length FROM {table} WHERE content_hash=?",
                        (digest,),
                    )
                )
    if any(r["table"] == "commits" for r in references):
        raise ValueError(
            "Commit-byte recovery is unsupported by this job-artifact helper; nothing was restored"
        )
    lengths = {r["byte_length"] for r in references}
    if len(lengths) != 1 or not 0 < next(iter(lengths)) <= 256 * 1024**2:
        raise ValueError("One bounded existing referenced byte length required")
    return references, next(iter(lengths))


def command(store, source, digest, *, apply_preview_sha256=None, output=None):
    references, length = read_references(store, digest)
    destination = store / "blobs" / digest
    if destination.exists() or destination.is_symlink():
        raise ValueError(
            "Recovery restores missing bytes only; never overwrites a retained blob"
        )
    if (
        not source.is_absolute()
        or not source.is_file()
        or source.is_symlink()
        or source.stat().st_size != length
    ):
        raise ValueError(
            "Explicit regular source with exact referenced byte length required"
        )
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError(
            "Recovery source differs from original SHA256; equivalent geometry is not original bytes"
        )
    if output is not None and (
        not output.is_absolute()
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
    ):
        raise ValueError("A new absolute recovery receipt is required")
    database = store / "metadata.sqlite3"
    before = sha256(database.read_bytes()).hexdigest()
    preview = {
        "schema": "cosmos.exact-blob-recovery-preview.v1",
        "store": str(store),
        "source": str(source),
        "digest": digest,
        "bytes": length,
        "references": references,
        "metadata_sha256": before,
        "effect": "RESTORE_MISSING_ORIGINAL_BYTES_ONLY_NO_METADATA_EDITS",
    }
    preview_hash = sha256(
        json.dumps(preview, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    result = {"applied": False, "preview_sha256": preview_hash, "preview": preview}
    if apply_preview_sha256 is not None:
        if apply_preview_sha256 != preview_hash:
            raise ValueError("Recovery preview changed; nothing was restored")
        with CoordinatorLease(store):
            if (
                sha256(database.read_bytes()).hexdigest() != before
                or destination.exists()
                or destination.is_symlink()
            ):
                raise ValueError(
                    "Recovery state changed while acquiring coordinator; re-preview"
                )
            repository = SQLiteProjectRepository(store)
            # Uses the existing atomic, private, fsynced put-if-absent path. It
            # installs no new database reference and does not call jobs.recover.
            with repository.files.write_lock():
                repository.files.install_blob(raw, digest)
            SQLiteJobRepository(repository).verify_integrity()
            after = sha256(database.read_bytes()).hexdigest()
            if after != before:
                raise ValueError(
                    "Metadata bytes changed unexpectedly; inspect before continuing"
                )
            result.update(
                applied=True,
                restored_blob_sha256=digest,
                metadata_sha256_after=after,
                metadata_unchanged=True,
                durable_job_integrity="PASS",
                records_deleted=0,
                schema_migrated=False,
            )
    if output is not None:
        with output.open("x") as stream:
            json.dump(result, stream, indent=2, allow_nan=False)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--apply-preview-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = command(
        args.store,
        args.source,
        args.sha256,
        apply_preview_sha256=args.apply_preview_sha256,
        output=args.output,
    )
    print(json.dumps({key: value for key, value in result.items() if key != "preview"}))


if __name__ == "__main__":
    main()
