"""Bounded coordinator-only recovery inventory. Reports never evict/repair data.

Not a project API: root-level hashes can reveal other projects' identities.
The caller must hold the application coordinator lease and quiesce writes.
"""
from __future__ import annotations

import os
import sqlite3
import stat
from dataclasses import dataclass

from infrastructure.persistence.files import private_file
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import IntegrityFailure, InvalidRecord


@dataclass(frozen=True)
class RecoveryInventory:
    usage_bytes: int
    referenced_blobs: int
    unreferenced_blobs: int
    unreferenced_bytes: int
    staging_files: int
    staging_bytes: int
    unavailable_references: int
    unreferenced_sample: tuple[str, ...]
    staging_sample: tuple[str, ...]
    unavailable_sample: tuple[str, ...]
    truncated: bool
    deletion_performed: bool = False


def inventory(repository: SQLiteProjectRepository, *, limit: int = 20) -> RecoveryInventory:
    if type(limit) is not int or not 1 <= limit <= 100:
        raise InvalidRecord("Use a bounded recovery inventory sample.")
    with repository._transaction() as connection:
        return _inventory_locked(repository, connection, limit)


def _inventory_locked(repository: SQLiteProjectRepository, connection: sqlite3.Connection, limit: int) -> RecoveryInventory:
    files = repository.files
    files.validate_paths()
    usage = files.usage_bytes()  # Counts orphans/staging; rejects aliases and excessive inventory.
    tables = ["commits"]
    if repository.schema_version >= 3:
        tables += ["durable_job_events", "durable_job_blobs"]
    if repository.schema_version >= 4:
        tables += ["durable_geometry_stages"]
    if repository.schema_version >= 5:
        tables += ["durable_simulation_monitors"]
    if repository.schema_version >= 6:
        tables += ["transfer_receipts"]
    references: dict[str, int] = {}
    for table in tables:
        for row in connection.execute(f"SELECT content_hash,byte_length FROM {table}"):
            if len(references) >= 200_000 and row[0] not in references:
                raise IntegrityFailure("Recovery reference inventory exceeds its budget.")
            if row[0] in references and references[row[0]] != row[1]:
                raise IntegrityFailure("Conflicting retained blob lengths.")
            references[row[0]] = row[1]
    orphan_count = orphan_bytes = staging_count = staging_bytes = unavailable = 0
    orphans: list[str] = []
    stages: list[str] = []
    missing: list[str] = []
    for parent in (files.blobs, files.staging):
        for path in parent.iterdir():
            if not stat.S_ISREG(path.lstat().st_mode):
                raise IntegrityFailure("Unexpected recovery inventory entry.")
            fd = private_file(path)
            size = os.fstat(fd).st_size
            os.close(fd)
            if parent == files.staging:
                staging_count += 1
                staging_bytes += size
                if len(stages) < limit:
                    stages.append(path.name)
            elif path.name not in references:
                orphan_count += 1
                orphan_bytes += size
                if len(orphans) < limit:
                    orphans.append(path.name)
    for digest, length in references.items():
        try:
            files.read_blob(digest, length)
        except IntegrityFailure:
            unavailable += 1
            if len(missing) < limit:
                missing.append(digest)
    return RecoveryInventory(usage, len(references), orphan_count, orphan_bytes, staging_count, staging_bytes,
        unavailable, tuple(orphans), tuple(stages), tuple(missing),
        any(count > limit for count in (orphan_count, staging_count, unavailable)))
