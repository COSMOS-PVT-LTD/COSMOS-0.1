"""Non-authoritative private execution scratch from authorized exact blobs."""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from systems.geometry.retained_source import CapturedGeometrySource, RetainedFixture
from systems.projects.authority import IntegrityFailure


@contextmanager
def materialize_fixture(source: RetainedFixture) -> Iterator[CapturedGeometrySource]:
    # These files are task-generated execution copies, never the retained store.
    with TemporaryDirectory(prefix="cosmos-managed-study-") as temporary:
        directory = Path(temporary).resolve()
        for blob in source.files:
            if blob.name not in {"source.brep", "export.step"} or sha256(blob.data).hexdigest() != blob.content_hash:
                raise IntegrityFailure("Refuse unsupported or corrupt execution materialization.")
            fd = os.open(directory / blob.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(blob.data)
        yield CapturedGeometrySource(source, directory)
