"""Application-lifetime authority composition and durable deny-only sentinel."""

from __future__ import annotations

import os
from pathlib import Path

from infrastructure.persistence.files import (
    CoordinatorLease,
    private_directory,
    private_file,
    sync_directory,
)
from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.projects.authority import SchemaMismatch, StoreUnavailable


def authority_required(application_root: Path) -> bool:
    base = application_root / "engineering_state"
    return any(
        path.exists() or path.is_symlink()
        for path in (base / "authority.required", base / "v1")
    )


class ApplicationAuthority:
    def __init__(self, application_root: Path, *, enabled: bool) -> None:
        base = application_root / "engineering_state"
        private_directory(base)
        root = base / "v1"
        marker = base / "authority.required"
        existing = authority_required(application_root)
        self.lease = CoordinatorLease(root)
        try:
            from infrastructure.persistence.portability import require_completed_restore
            require_completed_restore(root)
            if existing and not (root / "metadata.sqlite3").is_file():
                raise StoreUnavailable(
                    "Required authority database is missing; do not create a replacement or use legacy writes."
                )
            self.repository = SQLiteProjectRepository(root)
            if enabled and self.repository.schema_version < 2:
                raise SchemaMismatch(
                    "Foundation schema v1 is readable only here. A reviewed explicit upgrade is required before managed commands."
                )
            if marker.exists() or marker.is_symlink():
                fd = private_file(marker)
                with os.fdopen(fd, "rb") as stream:
                    if (
                        stream.read(100)
                        != b"cosmos-engineering-authority-required-v1\n"
                    ):
                        raise StoreUnavailable(
                            "Invalid authority protection marker; refusing legacy fallback."
                        )
            else:
                fd = os.open(
                    marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
                )
                with os.fdopen(fd, "wb") as stream:
                    stream.write(b"cosmos-engineering-authority-required-v1\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_directory(base)
            from infrastructure.persistence.durable_jobs import SQLiteJobRepository

            self.jobs = SQLiteJobRepository(self.repository)
            self.recovered_jobs = self.jobs.recover() if enabled and self.repository.schema_version >= 3 else 0
        except BaseException:
            self.lease.close()
            raise

    def legacy_guard(self, design_id: str | None) -> bool:
        return self.repository.is_managed_propulsion(
            design_id or "__legacy_health_check__"
        )

    def close(self) -> None:
        self.lease.close()
