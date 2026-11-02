"""Private POSIX store files, bounded root accounting and cooperative IO locks.

OS administrators are outside this local trust boundary. The application must
hold CoordinatorLease for its lifetime; repositories use a separate short IO
lock so client connections/processes can exercise SQLite CAS independently.
"""

from __future__ import annotations

import errno
import fcntl
import os
import stat
import time
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Self
from uuid import uuid4

from systems.projects.authority import (
    IntegrityFailure,
    QuotaExceeded,
    StoragePolicy,
    StoreUnavailable,
)


def private_directory(path: Path, *, create: bool = True) -> None:
    for candidate in reversed((path, *path.parents)):
        if candidate.is_symlink():
            raise IntegrityFailure("Store paths must not traverse symlinks.")
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        raise IntegrityFailure(
            "Engineering storage requires a private owned directory."
        )


def private_file(path: Path, *, create: bool = False) -> int:
    flags = os.O_RDWR | os.O_NOFOLLOW | (os.O_CREAT if create else 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            raise IntegrityFailure("Store paths must not traverse aliases.") from exc
        raise
    info = os.fstat(fd)
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_uid != os.getuid()
        or info.st_mode & 0o077
    ):
        os.close(fd)
        raise IntegrityFailure("Store file is not a private owned regular file.")
    return fd


def sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class CoordinatorLease:
    """One live mutating application coordinator per root; no data deletion."""

    def __init__(self, root: Path) -> None:
        private_directory(root)
        self._fd = private_file(root / "coordinator.lock", create=True)
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            self._fd = -1
            raise StoreUnavailable(
                "Another coordinator owns this engineering root."
            ) from exc

    def close(self) -> None:
        if self._fd >= 0:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = -1

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class StoreFiles:
    def __init__(self, root: Path, policy: StoragePolicy) -> None:
        self.root = root.absolute()
        self.policy = policy
        private_directory(self.root)
        self.blobs = self.root / "blobs"
        self.staging = self.root / "staging"
        private_directory(self.blobs)
        private_directory(self.staging)

    @contextmanager
    def write_lock(self) -> Iterator[None]:
        for path in (self.root, self.blobs, self.staging):
            private_directory(path, create=False)
        fd = private_file(self.root / "write.lock", create=True)
        deadline = time.monotonic() + self.policy.busy_timeout_ms / 1000
        try:
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError as exc:
                    if time.monotonic() >= deadline:
                        raise StoreUnavailable(
                            "Engineering store is busy; retry the same operation ID."
                        ) from exc
                    time.sleep(0.01)
            # Sidecars are transient during a cooperative writer's commit.
            # Inspect them only after excluding that journal lifecycle.
            self.validate_paths()
            yield
        finally:
            os.close(fd)

    def validate_paths(self) -> None:
        for path in (self.root, self.blobs, self.staging):
            private_directory(path, create=False)
        # SQLite can recover a journal while opening, before the first SQL
        # transaction. Refuse hostile sidecars before allowing that recovery.
        for suffix in ("-journal", "-wal", "-shm"):
            sidecar = self.root / ("metadata.sqlite3" + suffix)
            if sidecar.exists() or sidecar.is_symlink():
                fd = private_file(sidecar)
                os.close(fd)

    def usage_bytes(self) -> int:
        total = 0
        count = 0
        for parent, dirs, files in os.walk(self.root, followlinks=False):
            for name in (*dirs, *files):
                info = (Path(parent) / name).lstat()
                count += 1
                if count > 200_000 or stat.S_ISLNK(info.st_mode):
                    raise IntegrityFailure("Unsafe or excessive store inventory.")
                if (
                    not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode))
                    or info.st_nlink > 1
                    and stat.S_ISREG(info.st_mode)
                ):
                    raise IntegrityFailure("Unexpected store file type/alias.")
                total += info.st_size if stat.S_ISREG(info.st_mode) else 0
        return total

    def reserve(self, incoming: int = 0) -> None:
        # Conservative room for staging+installed bytes, SQLite metadata growth
        # and a full rollback journal. No retained/orphan data is evicted.
        db = self.root / "metadata.sqlite3"
        db_bytes = db.stat().st_size if db.exists() else 0
        if (
            self.usage_bytes() + 2 * incoming + db_bytes + 65_536
            > self.policy.store_bytes
        ):
            raise QuotaExceeded(
                "Store budget exhausted; preserve data and choose a larger approved budget/root."
            )

    def read_blob(self, digest: str, length: int) -> bytes:
        private_directory(self.blobs, create=False)
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise IntegrityFailure("Malformed stored digest.")
        if type(length) is not int or not 0 <= length <= self.policy.blob_bytes:
            raise IntegrityFailure("Invalid stored blob length.")
        try:
            fd = private_file(self.blobs / digest)
            with os.fdopen(fd, "rb") as stream:
                data = stream.read(length + 1)
        except OSError as exc:
            raise IntegrityFailure(
                "Retained source bytes are missing or inaccessible."
            ) from exc
        if len(data) != length or sha256(data).hexdigest() != digest:
            raise IntegrityFailure(
                "Retained source hash/length mismatch; record unavailable."
            )
        return data

    def install_blob(self, data: bytes, digest: str) -> None:
        self.validate_paths()
        if type(data) is not bytes or len(data) > self.policy.blob_bytes:
            raise QuotaExceeded("Immutable blob exceeds the configured byte budget.")
        if not isinstance(digest, str) or sha256(data).hexdigest() != digest:
            raise IntegrityFailure(
                "Immutable blob requires its exact SHA-256 identity."
            )
        destination = self.blobs / digest
        if destination.exists() or destination.is_symlink():
            if self.read_blob(digest, len(data)) != data:
                raise IntegrityFailure("Immutable source collision.")
            return
        stage = self.staging / uuid4().hex
        fd = os.open(stage, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            # Atomic put-if-absent. Link then unlink leaves a recoverable pair if
            # killed in between; reads refuse that alias until explicit recovery.
            os.link(stage, destination, follow_symlinks=False)
            stage.unlink()
            sync_directory(self.blobs)
            sync_directory(self.staging)
        except OSError as exc:
            # Leave incomplete/unreferenced bytes for explicit recovery. Never
            # publish a DB reference after any failed installation boundary.
            if exc.errno in {errno.ENOSPC, errno.EDQUOT}:
                raise QuotaExceeded(
                    "Disk full while staging immutable source; no record committed."
                ) from exc
            raise StoreUnavailable(
                "Immutable source installation failed; inspect retained staging."
            ) from exc
