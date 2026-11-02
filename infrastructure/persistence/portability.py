"""Bounded exact project packages and offline engineering-store recovery.

No credentials/Knowledge database, executable deserialization, purge, live-root
switch or implicit schema upgrade. Failed fresh staging is retained for audit.
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import stat
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from infrastructure.persistence.files import (
    private_directory,
    private_file,
    sync_directory,
)
from infrastructure.persistence.inventory import inventory
from infrastructure.persistence.schema import (
    CURRENT_VERSION,
    SCHEMA,
    SCHEMA_V1,
    SCHEMA_V2,
    SCHEMA_V3,
    SCHEMA_V4,
    SCHEMA_V5,
    check_schema,
)
from infrastructure.persistence.sqlite_projects import (
    SQLiteProjectRepository,
    _metadata,
    _project,
    _project_head,
    _stamp,
)
from systems.persistence.project_repository import RecordPayload, _unique_pairs
from systems.projects.authority import (
    AccessDenied,
    Head,
    IntegrityFailure,
    InvalidRecord,
    Lifecycle,
    Principal,
    Project,
    QuotaExceeded,
    SchemaMismatch,
    identity,
)

DIRECT = ("projects", "project_members", "objects", "commits", "project_events", "operations", "durable_jobs", "durable_job_selections", "transfer_receipts")
COMMIT = ("commit_contexts", "record_dependencies")
JOB = ("durable_job_events", "durable_geometry_stages", "durable_simulation_monitors", "durable_job_blobs")
TABLES = DIRECT[:6] + COMMIT[:1] + DIRECT[6:7] + JOB + DIRECT[7:] + COMMIT[1:]
REFS = ("commits", *JOB, "transfer_receipts")
USER_FIELDS = {"owner_user_id", "user_id", "creator_user_id", "actor_user_id"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()


@dataclass(frozen=True)
class TransferLimits:
    max_bytes: int = 64 * 1024**2
    max_files: int = 4096
    max_rows: int = 100_000


def _json(raw: bytes) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise InvalidRecord("Invalid unambiguous bounded transfer JSON.") from error


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _refs(rows: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for table in REFS:
        for row in rows.get(table, []):
            digest, length = row["content_hash"], row["byte_length"]
            Head(0, digest)
            if type(length) is not int or length < 0 or digest in result and result[digest] != length:
                raise IntegrityFailure("Conflicting transfer blob identity/length.")
            result[digest] = length
    return result


def _insert_rows(connection: sqlite3.Connection, metadata: dict[str, Any], users: Mapping[str, Principal] | None = None) -> None:
    connection.execute("PRAGMA defer_foreign_keys=ON")
    project_id = metadata["project_id"]
    # Replay progress before terminal publication, exactly as the coordinator
    # did originally. Retain all immutability/order/blob-gate triggers.
    events = metadata["tables"].get("durable_job_events", [])
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "INTERRUPTED"}
    steps: list[tuple[str, list[dict[str, Any]]]] = []
    for table in TABLES:
        if table == "durable_job_blobs":
            steps.append(("durable_job_events", [row for row in events if row["state"] in terminal]))
        rows = metadata["tables"].get(table, [])
        steps.append((table, [row for row in rows if row["state"] not in terminal] if table == "durable_job_events" else rows))
    for table, rows in steps:
        columns = {r[1] for r in connection.execute(f"PRAGMA table_info({table})")}
        if table in JOB:
            rows = sorted(rows, key=lambda r: (r["job_id"], r.get("sequence", -1), r.get("name", "")))
        for source in rows:
            if not isinstance(source, dict) or set(source) != columns or ("project_id" in source and source["project_id"] != project_id):
                raise InvalidRecord("Exact scoped schema columns required; no extra project may be imported.")
            row = dict(source)
            if any(v is not None and type(v) not in {str, int} for v in row.values()):
                raise InvalidRecord("Transfer metadata cells must be exact SQLite text/integer/null scalars.")
            for key in {"domain", "object_id", "commit_id", "schema_id", "job_id", "receipt_id", "relation"} & row.keys():
                if row[key] is not None:
                    identity(row[key], key)
            if row.get("source_namespace"):
                identity(row["source_namespace"], "source namespace")
            if users is not None:
                for key in USER_FIELDS & row.keys():
                    row[key] = users[row[key]].user_id
                if table == "project_events":
                    del row["sequence"]
                if table == "durable_jobs":
                    del row["ordinal"]
                if table == "durable_job_selections":
                    # Imported archives authenticate bytes, not native execution
                    # or engineering authority. Explicit current builds/runs are
                    # needed; original selections remain in the source receipt.
                    row["selected_job_id"] = None
                if table == "projects":
                    row["content_hash"] = _project_head(row["title"], row["mission"], row["owner_user_id"], Lifecycle(row["lifecycle"]), row["version"]).content_hash
            keys = list(row)
            connection.execute(f"INSERT INTO {table}({','.join(keys)}) VALUES({','.join('?' for _ in keys)})", tuple(row[k] for k in keys))
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise IntegrityFailure("Imported references must be self-contained, never resolved from another project/root.")


class ProjectPortability:
    def __init__(self, repository: SQLiteProjectRepository, *, limits: TransferLimits | None = None) -> None:
        self.repository, self.limits = repository, limits or TransferLimits()

    def transfers(self, actor: Principal, project_id: str, *, limit: int = 20, after: str = "") -> tuple[dict[str, Any], ...]:
        if self.repository.schema_version < 6:
            raise SchemaMismatch("Transfer receipts require schema6; existing data was not upgraded.")
        if type(limit) is not int or not 1 <= limit <= 100 or type(after) is not str or len(after) > 128:
            raise InvalidRecord("Use bounded transfer receipt pages.")
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            return tuple(dict(row) for row in connection.execute("SELECT * FROM transfer_receipts WHERE project_id=? AND receipt_id>? ORDER BY receipt_id LIMIT ?", (project_id, after, limit)))

    def original(self, actor: Principal, project_id: str, receipt_id: str) -> tuple[str, bytes]:
        identity(receipt_id, "transfer receipt")
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            row = connection.execute("SELECT * FROM transfer_receipts WHERE project_id=? AND receipt_id=?", (project_id, receipt_id)).fetchone()
            if row is None:
                from systems.projects.authority import RecordNotFound
                raise RecordNotFound("Original transfer is not in this owning project.")
            names = {"clone-origin": "clone-origin.zip", "legacy-import": "legacy-original.json", "package-import": "original-import-metadata.json"}
            return names.get(row["kind"], "transfer-original.bin"), self.repository.files.read_blob(row["content_hash"], row["byte_length"])

    def clone(self, actor: Principal, project_id: str, expected: Head, *, title: str, operation_id: str,
              cloner: Callable[[str, str, str, bytes, str], tuple[RecordPayload, int] | None]) -> Project:
        repo = self.repository
        identity(operation_id, "operation ID")
        if repo.schema_version < 6:
            raise SchemaMismatch("Exact origin archive receipts require reviewed schema6.")
        request = sha256(canonical({"action": "clone", "project": project_id, "expected": asdict(expected), "title": title})).hexdigest()
        with repo._transaction() as connection:
            repo._authorize(connection, actor, project_id, owner=True)
            replay = repo._replay(connection, actor, operation_id, request)
            if replay is not None:
                return _project(replay)
        archive = self.export(actor, project_id, expected)
        _, metadata, files = self.inspect(archive)
        old_project = metadata["tables"]["projects"][0]
        _metadata(title, old_project["mission"])
        new_project, stamp = str(uuid4()), _stamp()
        sources = {row["commit_id"]: row for row in metadata["tables"]["commits"]}
        inputs = []
        for item in metadata["tables"]["objects"]:
            source = sources[item["head_commit_id"]]
            new_id = str(uuid4())
            cloned = cloner(item["domain"], source["schema_id"], source["source_namespace"], files["blobs/" + source["content_hash"]], new_id)
            if cloned is not None:
                data, revision = cloned
                data.validate(repo.policy)
                inputs.append((item["domain"], new_id, data, revision, item["object_id"]))
        archive_hash = sha256(archive).hexdigest()
        with repo._transaction(write=True) as connection:
            repo._authorize(connection, actor, project_id, owner=True)
            replay = repo._replay(connection, actor, operation_id, request)
            if replay is not None:
                return _project(replay)
            repo.files.reserve(len(archive) + sum(len(item[2].data) for item in inputs))
            head = _project_head(title, old_project["mission"], actor.user_id, Lifecycle.ACTIVE, 1)
            connection.execute("PRAGMA defer_foreign_keys=ON")
            connection.execute("INSERT INTO projects VALUES(?,?,?,?,?,?,?,?,?)", (new_project, title, old_project["mission"], actor.user_id, "ACTIVE", 1, head.content_hash, stamp, stamp))
            connection.execute("INSERT INTO project_members VALUES(?,?,'OWNER')", (new_project, actor.user_id))
            repo.files.install_blob(archive, archive_hash)
            connection.execute("INSERT INTO transfer_receipts VALUES(?,?,?,?,?,?,?)", (sha256((new_project + archive_hash).encode()).hexdigest(), new_project,
                "clone-origin", archive_hash, len(archive), actor.user_id, stamp))
            for domain, object_id, data, revision, old_id in inputs:
                commit_id = str(uuid4())
                repo.files.install_blob(data.data, data.content_hash)
                connection.execute("INSERT INTO objects VALUES(?,?,?,?,?,?)", (new_project, domain, object_id, commit_id, 1, data.content_hash))
                connection.execute("INSERT INTO commits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (commit_id, new_project, domain, object_id, None, 1, revision,
                    data.content_hash, len(data.data), data.schema_id, data.source_namespace, actor.user_id, stamp))
                connection.execute("INSERT INTO commit_contexts VALUES(?,'create',NULL,NULL,1,NULL)", (commit_id,))
                repo._event(connection, actor, new_project, "clone.input", {"domain": domain, "object_id": object_id, "commit_id": commit_id,
                    "origin_object_id": old_id, "origin_archive_sha256": archive_hash, "inherited_execution_selected": False})
            repo._event(connection, actor, new_project, "project.cloned", {"origin_project_id": project_id, "origin_archive_sha256": archive_hash,
                "memberships_copied": False, "scope": "Editable propulsion/geometry inputs only; all study/run/comparison/report originals retained in origin package. Rebuild/rebind/rerun downstream explicitly."})
            result = repo._authorize(connection, actor, new_project, owner=True)
            repo._check_project_budget(connection, new_project)
            repo._remember(connection, actor, new_project, operation_id, request, repo._project_result(result))
            return result

    def export(self, actor: Principal, project_id: str, expected: Head) -> bytes:
        repo = self.repository
        with repo._transaction() as connection:
            project = repo._authorize(connection, actor, project_id, owner=True)
            repo._expected(project.head, expected)
            known = _tables(connection)
            rows = {}
            for table in TABLES:
                if table not in known:
                    continue
                if table in DIRECT:
                    query = f"SELECT * FROM {table} WHERE project_id=?"
                elif table in COMMIT:
                    query = f"SELECT x.* FROM {table} x JOIN commits c ON c.commit_id=x.commit_id WHERE c.project_id=?"
                else:
                    query = f"SELECT x.* FROM {table} x JOIN durable_jobs j ON j.job_id=x.job_id WHERE j.project_id=?"
                rows[table] = [dict(r) for r in connection.execute(query, (project_id,)).fetchmany(self.limits.max_rows + 1)]
            if sum(map(len, rows.values())) > self.limits.max_rows:
                raise QuotaExceeded("Project export exceeds its explicit metadata-row limit.")
            metadata = canonical({"schema": repo.schema_version, "project_id": project_id, "tables": rows})
            refs = _refs(rows)
            if len(metadata) > repo.policy.record_bytes or len(refs) + 2 > self.limits.max_files or len(metadata) + sum(refs.values()) > self.limits.max_bytes:
                raise QuotaExceeded("Project export exceeds its explicit byte/file budget; no history was truncated.")
        # All committed blobs are retained indefinitely; no cleanup can remove
        # this captured reference set after the short metadata barrier.
        files = {"metadata.json": metadata, **{"blobs/" + key: repo.files.read_blob(key, size) for key, size in refs.items()}}
        manifest = {"format": "cosmos-project-package-v1", "project_id": project_id, "schema": repo.schema_version,
            "files": {name: {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)} for name, raw in files.items()},
            "scope": "Exact engineering authority only; no credentials, Knowledge database or independent signoff"}
        files["manifest.json"] = canonical(manifest)
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as archive:
            for name, raw in sorted(files.items()):
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.external_attr = 0o100600 << 16
                archive.writestr(info, raw)
        raw = stream.getvalue()
        if len(raw) > self.limits.max_bytes:
            raise QuotaExceeded("Package overhead exceeds the explicit byte budget.")
        return raw

    def inspect(self, raw: bytes) -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
        if type(raw) is not bytes or not 0 < len(raw) <= self.limits.max_bytes:
            raise QuotaExceeded("Bounded immutable package bytes required.")
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                entries = archive.infolist()
                if len(entries) > self.limits.max_files or len({e.filename for e in entries}) != len(entries):
                    raise InvalidRecord("Duplicate or excessive archive entries.")
                files = {}
                total = 0
                for entry in entries:
                    name = entry.filename
                    if name not in {"manifest.json", "metadata.json"} and not (name.startswith("blobs/") and len(name) == 70):
                        raise InvalidRecord("Only exact manifest/metadata/digest paths are permitted; no extraction occurs.")
                    if name.startswith("blobs/"):
                        Head(0, name[6:])
                    mode = entry.external_attr >> 16
                    if entry.compress_type != zipfile.ZIP_STORED or mode and not stat.S_ISREG(mode):
                        raise InvalidRecord("Compressed, directory, link or special archive entries refused.")
                    total += entry.file_size
                    if entry.file_size < 0 or total > self.limits.max_bytes:
                        raise QuotaExceeded("Expanded transfer budget exceeded.")
                    files[name] = archive.read(entry)
        except (zipfile.BadZipFile, RuntimeError, OSError) as error:
            raise InvalidRecord("Invalid bounded project archive.") from error
        if not {"manifest.json", "metadata.json"} <= files.keys():
            raise InvalidRecord("Exact transfer manifest and metadata are required.")
        manifest, metadata = _json(files["manifest.json"]), _json(files["metadata.json"])
        if type(manifest) is not dict or set(manifest) != {"format", "project_id", "schema", "files", "scope"} or manifest["format"] != "cosmos-project-package-v1" or type(manifest["files"]) is not dict:
            raise InvalidRecord("Unsupported project package contract.")
        try:
            if str(UUID(manifest["project_id"])) != manifest["project_id"]:
                raise ValueError("Noncanonical project UUID")
        except (ValueError, TypeError, AttributeError) as error:
            raise InvalidRecord("Canonical owning project UUID required.") from error
        if set(files) != set(manifest["files"]) | {"manifest.json"}:
            raise InvalidRecord("Manifest and archive entries disagree.")
        for name, expected in manifest["files"].items():
            data = files[name]
            if expected != {"sha256": sha256(data).hexdigest(), "bytes": len(data)}:
                raise IntegrityFailure("Transfer file checksum/length mismatch.")
        if type(metadata) is not dict or set(metadata) != {"schema", "project_id", "tables"} or metadata["schema"] != manifest["schema"] or metadata["project_id"] != manifest["project_id"] or type(metadata["tables"]) is not dict or any(type(rows) is not list for rows in metadata["tables"].values()):
            raise InvalidRecord("Metadata identity/schema disagrees with manifest.")
        if metadata["schema"] not in range(1, CURRENT_VERSION + 1) or set(metadata["tables"]) - set(TABLES):
            raise SchemaMismatch("Unknown table/schema; do not coerce or reset imported history.")
        if sum(map(len, metadata["tables"].values())) > self.limits.max_rows:
            raise QuotaExceeded("Transfer row budget exceeded.")
        if set(files) != {"manifest.json", "metadata.json"} | {"blobs/" + key for key in _refs(metadata["tables"])}:
            raise InvalidRecord("Package must contain exactly its retained blob reference set.")
        for key, size in _refs(metadata["tables"]).items():
            if len(files["blobs/" + key]) != size or sha256(files["blobs/" + key]).hexdigest() != key:
                raise IntegrityFailure("Retained blob reference differs from package bytes.")
        project_rows = metadata["tables"].get("projects", [])
        if len(project_rows) != 1 or project_rows[0]["project_id"] != manifest["project_id"]:
            raise InvalidRecord("Exactly one owning project must be exported.")
        project = project_rows[0]
        _metadata(project["title"], project["mission"])
        if project["content_hash"] != _project_head(project["title"], project["mission"], project["owner_user_id"], Lifecycle(project["lifecycle"]), project["version"]).content_hash:
            raise IntegrityFailure("Project metadata head does not match its exact source identity.")
        for row in metadata["tables"].get("commits", []):
            RecordPayload(files["blobs/" + row["content_hash"]], row["schema_id"], row["source_namespace"]).validate(self.repository.policy)
        staged = sqlite3.connect(":memory:")
        try:
            staged.execute("PRAGMA foreign_keys=ON")
            staged.executescript(SCHEMA)
            staged.execute("BEGIN")
            _insert_rows(staged, metadata)
            staged.commit()
        except sqlite3.DatabaseError as error:
            raise InvalidRecord("Package metadata fails exact schema/order/constraint validation.") from error
        finally:
            staged.close()
        return manifest, metadata, files

    def preview(self, raw: bytes) -> dict[str, Any]:
        manifest, metadata, files = self.inspect(raw)
        users = sorted({row[key] for rows in metadata["tables"].values() for row in rows for key in USER_FIELDS & row.keys()})
        return {"manifest_sha256": sha256(files["manifest.json"]).hexdigest(), "package_sha256": sha256(raw).hexdigest(),
            "project_id": manifest["project_id"], "schema": metadata["schema"], "required_explicit_user_mapping": users,
            "memberships_to_confirm": metadata["tables"].get("project_members", []), "rows": sum(map(len, metadata["tables"].values())),
            "blobs": len(files) - 2, "limits": asdict(self.limits), "writes_performed": False,
            "warning": "Import retains original source actor IDs in scientific bytes; local metadata mapping is explicit, not credential import"}

    def import_project(self, actor: Principal, raw: bytes, *, confirmed_manifest: str, users: Mapping[str, Principal],
                       confirmed_memberships: bool) -> dict[str, Any]:
        repo = self.repository
        if repo.schema_version < 6:
            raise SchemaMismatch("Transfer receipts require an explicit reviewed schema6 copy; no live upgrade occurred.")
        actor.require(write=True)
        preview = self.preview(raw)
        if confirmed_memberships is not True or confirmed_manifest != preview["manifest_sha256"] or set(users) != set(preview["required_explicit_user_mapping"]):
            raise InvalidRecord("Confirm the exact preview digest, every active-user mapping and membership grants.")
        for user in users.values():
            user.require()
        if len({p.user_id for p in users.values()}) != len(users):
            raise InvalidRecord("Ambiguous many-to-one ownership mapping refused.")
        manifest, metadata, files = self.inspect(raw)
        project_id = manifest["project_id"]
        original_owner = metadata["tables"]["projects"][0]["owner_user_id"]
        if users[original_owner].user_id != actor.user_id:
            raise AccessDenied("The explicitly mapped owner must be the authenticated importer.")
        binding = canonical({"manifest_sha256": confirmed_manifest, "users": {k: v.user_id for k, v in users.items()}})
        receipt_id = sha256(binding).hexdigest()
        with repo._transaction(write=True) as connection:
            existing = connection.execute("SELECT * FROM transfer_receipts WHERE receipt_id=?", (receipt_id,)).fetchone()
            if existing is not None:
                repo._authorize(connection, actor, project_id, owner=True)
                return {"project_id": project_id, "receipt_id": receipt_id, "idempotent": True}
            if connection.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone():
                raise InvalidRecord("Target project already exists; preserve it, do not merge timelines.")
            repo.files.reserve(sum(len(v) for v in files.values()))
            for name, data in files.items():
                if name.startswith("blobs/"):
                    repo.files.install_blob(data, name[6:])
            original = canonical({"manifest_json": files["manifest.json"].decode(), "metadata_json": files["metadata.json"].decode(),
                                  "mapping_json": binding.decode(), "package_sha256": sha256(raw).hexdigest()})
            source_hash = sha256(original).hexdigest()
            repo.files.install_blob(original, source_hash)
            _insert_rows(connection, metadata, users)
            interrupted = canonical({"code": "IMPORTED_ATTEMPT_HAS_NO_EXECUTOR", "automatic_rerun": False})
            interrupted_hash = sha256(interrupted).hexdigest()
            for item in metadata["tables"].get("durable_jobs", []):
                last = connection.execute("SELECT sequence,state FROM durable_job_events WHERE job_id=? ORDER BY sequence DESC LIMIT 1", (item["job_id"],)).fetchone()
                if last is not None and last[1] in {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}:
                    repo.files.install_blob(interrupted, interrupted_hash)
                    connection.execute("INSERT INTO durable_job_events VALUES(?,?,?,?,?,?)", (item["job_id"], last[0] + 1, "INTERRUPTED", interrupted_hash, len(interrupted), _stamp()))
            connection.execute("INSERT INTO transfer_receipts VALUES(?,?,?,?,?,?,?)", (receipt_id, project_id, "package-import", source_hash, len(original), actor.user_id, _stamp()))
            repo._authorize(connection, actor, project_id, owner=True)
            repo._check_project_budget(connection, project_id)
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise IntegrityFailure("Imported references are incomplete; transaction rolled back.")
        return {"project_id": project_id, "receipt_id": receipt_id, "idempotent": False}


def _fresh(path: Path) -> None:
    if not path.is_absolute() or path.exists() or path.is_symlink() or not path.parent.is_dir() or any(p.is_symlink() for p in path.parents):
        raise InvalidRecord("Choose an explicit absent destination with an existing parent; never overwrite a root.")
    path.mkdir(mode=0o700)


def _write(path: Path, raw: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def backup_store(repository: SQLiteProjectRepository, destination: Path) -> dict[str, Any]:
    """Engineering store only. Immutable reference list is a non-evicting pin."""
    _fresh(destination)
    (destination / "blobs").mkdir(mode=0o700)
    target = destination / "metadata.sqlite3"
    fd = private_file(target, create=True)
    os.close(fd)
    with repository._transaction():
        copied = sqlite3.connect(target)
        try:
            # Backup uses its own source connection: no active read transaction
            # is held on it. The outer cooperative barrier excludes commits.
            source_db = repository._connect()
            try:
                source_db.backup(copied)
            finally:
                source_db.close()
            version = check_schema(copied)
            refs: dict[str, int] = {}
            for table in REFS:
                if table in _tables(copied):
                    for key, size in copied.execute(f"SELECT content_hash,byte_length FROM {table}"):
                        if key in refs and refs[key] != size:
                            raise IntegrityFailure("Conflicting backup blob lengths.")
                        refs[key] = size
        finally:
            copied.close()
    for key, size in refs.items():
        _write(destination / "blobs" / key, repository.files.read_blob(key, size))
    if target.stat().st_size > 256 * 1024**2:
        raise QuotaExceeded("Backup metadata exceeds the explicit256MiB restore envelope; original store preserved.")
    db = target.read_bytes()
    manifest = {"format": "cosmos-engineering-backup-v1", "schema": version,
        "metadata_sha256": sha256(db).hexdigest(), "metadata_bytes": len(db), "blobs": refs,
        "scope": "Consistent engineering authority snapshot only; auth, credentials and Knowledge stores excluded",
        "retention": "Captured immutable blob set pinned by manifest; no cleanup/eviction exists"}
    _write(destination / "manifest.json", canonical(manifest))
    sync_directory(destination / "blobs")
    sync_directory(destination)
    return manifest


def restore_store(backup: Path, destination: Path, *, confirmed_manifest: str, upgrade: bool = False) -> dict[str, Any]:
    """Verified fresh-root restore/copy; never switches or overwrites live data."""
    private_directory(backup, create=False)
    manifest_path = backup / "manifest.json"
    fd = private_file(manifest_path)
    with os.fdopen(fd, "rb") as stream:
        raw = stream.read(16 * 1024**2 + 1)
    if len(raw) > 16 * 1024**2 or sha256(raw).hexdigest() != confirmed_manifest:
        raise IntegrityFailure("Confirm the exact bounded backup manifest digest.")
    manifest = _json(raw)
    if set(manifest) != {"format", "schema", "metadata_sha256", "metadata_bytes", "blobs", "scope", "retention"} or manifest["format"] != "cosmos-engineering-backup-v1":
        raise InvalidRecord("Unknown engineering backup contract.")
    _fresh(destination)
    _write(destination / "restore.pending", canonical({"format": "cosmos-restore-pending-v1", "source_manifest_sha256": confirmed_manifest}))
    (destination / "blobs").mkdir(mode=0o700)
    (destination / "staging").mkdir(mode=0o700)
    for name, size in {"metadata.sqlite3": manifest["metadata_bytes"], **{"blobs/" + key: length for key, length in manifest["blobs"].items()}}.items():
        if name != "metadata.sqlite3":
            Head(0, name[6:])
        if type(size) is not int or not 0 <= size <= 256 * 1024**2:
            raise QuotaExceeded("Backup file exceeds the explicit restore safety budget.")
        if name.startswith("blobs/"):
            private_directory(backup / "blobs", create=False)
        expected = manifest["metadata_sha256"] if name == "metadata.sqlite3" else name[6:]
        fd = private_file(backup / name)
        out = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        checksum, total = sha256(), 0
        with os.fdopen(fd, "rb") as stream, os.fdopen(out, "wb") as target:
            while chunk := stream.read(min(1024**2, size - total + 1)):
                total += len(chunk)
                if total > size:
                    raise IntegrityFailure("Backup file exceeds declared length; original root preserved.")
                checksum.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if total != size or checksum.hexdigest() != expected:
            raise IntegrityFailure("Backup file checksum/length mismatch; original root preserved.")
    connection = sqlite3.connect(destination / "metadata.sqlite3")
    try:
        before = check_schema(connection)
        if before != manifest["schema"]:
            raise SchemaMismatch("Backup version differs from its manifest.")
        if upgrade and before < CURRENT_VERSION:
            old = {1: SCHEMA_V1, 2: SCHEMA_V2, 3: SCHEMA_V3, 4: SCHEMA_V4, 5: SCHEMA_V5}[before]
            if not SCHEMA.startswith(old):
                raise SchemaMismatch("Only explicitly supported additive schema copies are implemented.")
            connection.executescript("BEGIN EXCLUSIVE;\n" + SCHEMA[len(old):] + f"\nPRAGMA user_version={CURRENT_VERSION}; COMMIT;")
        after = check_schema(connection)
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok" or connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise IntegrityFailure("Restored metadata integrity/references failed.")
    finally:
        connection.close()
    result = inventory(SQLiteProjectRepository(destination))
    if result.unavailable_references:
        raise IntegrityFailure("Restored store has unavailable references; do not activate it.")
    receipt = {"completed": True, "source_manifest_sha256": confirmed_manifest, "source_schema": before, "target_schema": after,
        "upgrade_explicit": upgrade, "original_root_overwritten": False, "live_switch_performed": False, "verified_inventory": asdict(result)}
    _write(destination / "restore-receipt.json", canonical(receipt))
    sync_directory(destination)
    return receipt


def require_completed_restore(root: Path) -> None:
    """An interrupted staged copy must never become an apparently empty app."""
    pending = root / "restore.pending"
    if not pending.exists() and not pending.is_symlink():
        return
    values = []
    try:
        for path in (pending, root / "restore-receipt.json"):
            fd = private_file(path)
            with os.fdopen(fd, "rb") as stream:
                raw = stream.read(1024**2 + 1)
            if len(raw) > 1024**2:
                raise IntegrityFailure("Restore marker exceeds its bounded contract.")
            values.append(_json(raw))
    except (OSError, ValueError) as error:
        raise IntegrityFailure("Restore staging is incomplete; preserve it and the original root. No legacy fallback or live activation.") from error
    marker, receipt = values
    if type(marker) is not dict or marker.get("format") != "cosmos-restore-pending-v1" or type(receipt) is not dict or receipt.get("completed") is not True or marker.get("source_manifest_sha256") != receipt.get("source_manifest_sha256") or receipt.get("verified_inventory", {}).get("unavailable_references") != 0:
        raise IntegrityFailure("Restore receipt is missing/inconsistent; do not activate or reset this root.")
