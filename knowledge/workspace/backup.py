"""Bounded local backups and staged restore; callers quiesce workspace writers.

SQLite's backup API captures committed WAL state. This is not a distributed
transaction across arbitrary external filesystem writers. Restore retains the
previous root privately for recovery; it never deletes an existing workspace.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import sqlite3
import stat
import struct
import tempfile
import time
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, TypedDict

from knowledge.workspace.models import PIPELINE_VERSION, IngestionJob, SourceRecord

__all__ = ("BackupArchive", "WorkspaceBackupError", "backup_workspace_root", "restore_workspace_root")

MAX_ARCHIVE_BYTES = 128 * 1024**2
MAX_MEMBER_BYTES = 128 * 1024**2
MAX_EXPANDED_BYTES = 512 * 1024**2
MAX_MEMBERS = 10_000
MAX_JSON_BYTES = 8 * 1024**2
MAX_MANIFEST_BYTES = 2 * 1024**2
MAX_CENTRAL_DIRECTORY_BYTES = 8 * 1024**2
MAX_DATABASE_ROWS = 100_000
SNAPSHOT_TIMEOUT_SECONDS = 15.
_DIRECTORIES = ("knowledge_vault", "jobs", "conversations")
_MANIFEST = "backup_manifest.json"
_FORMAT = "cosmos-workspace-backup-v2"
_LEGACY_FORMAT = "cosmos-workspace-backup-v1"
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")


class _InventoryEntry(TypedDict):
    size_bytes: int
    sha256: str


class WorkspaceBackupError(ValueError):
    """Compatible ValueError with a stable diagnostic and recovery instruction."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.recovery = "Keep the existing workspace; use a trusted compatible backup or inspect the retained recovery directory."


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise WorkspaceBackupError(code, message)


def _owned_path(path: Path) -> Path:
    """Reject symlinks/foreign ownership without resolving through them first."""
    path = Path(os.path.abspath(path))
    # macOS's OS-owned aliases are not user-created workspace symlinks.
    for alias, canonical in ((Path("/tmp"), Path("/private/tmp")), (Path("/var"), Path("/private/var"))):
        if alias.is_symlink() and alias.lstat().st_uid == 0 and alias.resolve() == canonical and path.is_relative_to(alias):
            path = canonical / path.relative_to(alias)
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.exists() or current.is_symlink():
            observed = current.lstat()
            _require(not stat.S_ISLNK(observed.st_mode), "UNSAFE_PATH", "Symlink path components are not allowed")
            # Shared system ancestors (/tmp, /Users) need not belong to this user.
            if current == path and hasattr(os, "getuid"):
                _require(observed.st_uid == os.getuid(), "UNSAFE_PATH", "Target is not owned by the current local user")
    return path


def _safe_name(value: str, *, directory: bool = False) -> str:
    name = value[:-1] if directory and value.endswith("/") else value
    parts = PurePosixPath(name).parts
    _require(bool(parts) and len(name.encode("utf-8")) <= 512 and len(parts) <= 12
             and not name.startswith("/") and "\\" not in name and ":" not in name
             and all(part not in {"", ".", ".."} for part in parts)
             and name == PurePosixPath(name).as_posix()
             and name == unicodedata.normalize("NFC", name)
             and not any(ord(char) < 32 or ord(char) == 127 for char in name),
             "UNSAFE_ARCHIVE_PATH", "Archive path is not a bounded canonical relative path")
    _require(parts[0] in _DIRECTORIES or name in {_MANIFEST, "workspace.sqlite"},
             "UNSUPPORTED_MEMBER", "Archive contains data outside the supported workspace areas")
    _require(not directory or parts[0] in _DIRECTORIES, "UNSUPPORTED_MEMBER", "Metadata and database cannot be directories")
    _require(directory or parts[0] not in _DIRECTORIES or len(parts) > 1,
             "UNSAFE_MEMBER", "Workspace areas must be directories, not file members")
    return name


def _strict_json(data: bytes, *, limit: int = MAX_JSON_BYTES) -> dict[str, Any]:
    _require(len(data) <= limit, "JSON_LIMIT", "Workspace metadata exceeds its bounded limit")
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        _require(len({key for key, _ in items}) == len(items), "INVALID_JSON", "Duplicate JSON keys")
        return dict(items)
    def constant(_: str) -> None:
        raise WorkspaceBackupError("INVALID_JSON", "Nonfinite JSON constants are not accepted")
    def finite(value: str) -> float:
        number = float(value)
        _require(math.isfinite(number), "INVALID_JSON", "Nonfinite JSON numbers are not accepted")
        return number
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant, parse_float=finite)
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, WorkspaceBackupError):
            raise
        raise WorkspaceBackupError("INVALID_JSON", "Malformed workspace JSON") from error
    _require(type(value) is dict, "INVALID_JSON", "Workspace metadata must be an object")
    return value


def _digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(64 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def _write_json(path: Path, value: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())
    path.chmod(0o600)


def _stat_key(path: Path) -> tuple[int, int, int, int, int]:
    observed = path.lstat()
    _require(stat.S_ISREG(observed.st_mode), "UNSAFE_PATH", "Only regular workspace files are supported")
    _owned_path(path)
    return observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns, observed.st_ctime_ns


def _source_files(root: Path) -> dict[str, tuple[int, int, int, int, int]]:
    files: dict[str, tuple[int, int, int, int, int]] = {}
    def unreadable(_error: OSError) -> None:
        raise WorkspaceBackupError("SOURCE_UNAVAILABLE", "Workspace directory cannot be inventoried completely")
    for folder in _DIRECTORIES:
        source = root / folder
        _owned_path(source)
        if not source.exists():
            continue
        _require(source.is_dir(), "UNSAFE_PATH", "Workspace area is not a directory")
        for parent, directories, names in os.walk(source, followlinks=False, onerror=unreadable):
            for name in directories:
                _owned_path(Path(parent) / name)
            for name in names:
                path = Path(parent) / name
                relative = _safe_name(path.relative_to(root).as_posix())
                files[relative] = _stat_key(path)
                _require(len(files) <= MAX_MEMBERS - 2, "MEMBER_LIMIT", "Too many workspace files")
    _require(sum(item[2] for item in files.values()) <= MAX_EXPANDED_BYTES, "EXPANDED_LIMIT", "Workspace exceeds backup size limit")
    return files


def _copy_regular(source: Path, destination: Path) -> None:
    before = _stat_key(source)
    _require(before[2] <= MAX_MEMBER_BYTES, "MEMBER_LIMIT", "Workspace file exceeds backup size limit")
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as incoming, destination.open("xb") as outgoing:
        opened = os.fstat(incoming.fileno())
        _require((opened.st_dev, opened.st_ino) == before[:2], "SOURCE_CHANGED", "Source changed while opening snapshot")
        copied = 0
        for block in iter(lambda: incoming.read(64 * 1024), b""):
            copied += len(block)
            _require(copied <= before[2], "SOURCE_CHANGED", "Source grew while copying backup")
            outgoing.write(block)
        outgoing.flush(); os.fsync(outgoing.fileno())
    destination.chmod(0o600)
    _require(_stat_key(source) == before and destination.stat().st_size == before[2],
             "SOURCE_CHANGED", "Source changed during backup; retry with workspace writers quiesced")


def _sqlite_snapshot(source: Path, destination: Path) -> None:
    original = _stat_key(source)
    _require(original[2] <= MAX_MEMBER_BYTES, "MEMBER_LIMIT", "Database exceeds backup size limit")
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = _owned_path(source.with_name(source.name + suffix))
        if sidecar.exists():
            _require(_stat_key(sidecar)[2] <= MAX_EXPANDED_BYTES, "MEMBER_LIMIT", "SQLite sidecar exceeds bounded size")
    started = time.monotonic()
    page_size = 0
    def progress(_status: int, _remaining: int, total: int) -> None:
        _require(time.monotonic() - started <= SNAPSHOT_TIMEOUT_SECONDS, "BACKUP_TIMEOUT", "SQLite snapshot exceeded its local time budget")
        _require(total * page_size <= MAX_MEMBER_BYTES, "MEMBER_LIMIT", "SQLite snapshot exceeds bounded page count")
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=.2) as incoming:
            page_size = incoming.execute("PRAGMA page_size").fetchone()[0]
            with sqlite3.connect(destination) as outgoing:
                incoming.backup(outgoing, pages=128, progress=progress, sleep=.02)
    except sqlite3.Error as error:
        raise WorkspaceBackupError("INVALID_DATABASE", "SQLite snapshot failed") from error
    _require(_stat_key(source)[:2] == original[:2], "SOURCE_CHANGED", "Database file was replaced during backup")
    _require(destination.stat().st_size <= MAX_MEMBER_BYTES, "MEMBER_LIMIT", "Database snapshot exceeds backup size limit")
    destination.chmod(0o600)


def _database(path: Path) -> list[tuple[str, str, dict[str, Any]]]:
    if not path.exists():
        return []
    with path.open("rb") as stream:
        header = stream.read(16)
    _require(path.stat().st_size <= MAX_MEMBER_BYTES and header == b"SQLite format 3\0", "INVALID_DATABASE", "Unsupported SQLite file")
    rows: list[tuple[str, str, dict[str, Any]]] = []
    try:
        with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=.2) as connection:
            started = time.monotonic()
            connection.set_progress_handler(lambda: int(time.monotonic() - started > SNAPSHOT_TIMEOUT_SECONDS), 1000)
            connection.execute("PRAGMA trusted_schema=OFF")
            _require(connection.execute("PRAGMA user_version").fetchone()[0] in {0, 1}, "UNSUPPORTED_VERSION", "Unsupported workspace database version")
            _require(connection.execute("PRAGMA quick_check").fetchall() == [("ok",)], "INVALID_DATABASE", "SQLite integrity check failed")
            schema = connection.execute("SELECT name, type FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'").fetchall()
            _require(schema == [("workspace_kv", "table")], "INVALID_DATABASE", "Unsupported workspace database schema")
            columns = connection.execute("PRAGMA table_info(workspace_kv)").fetchall()
            _require([(row[1], row[2].upper(), row[3], row[5]) for row in columns]
                     == [("collection", "TEXT", 1, 1), ("record_id", "TEXT", 1, 2), ("payload", "TEXT", 1, 0), ("updated_at", "TEXT", 1, 0)],
                     "INVALID_DATABASE", "Workspace database columns are incompatible")
            for collection, record, payload in connection.execute("SELECT collection,record_id,payload FROM workspace_kv LIMIT ?", (MAX_DATABASE_ROWS + 1,)):
                _require(len(rows) < MAX_DATABASE_ROWS and type(collection) is str and type(record) is str and type(payload) is str,
                         "DATABASE_LIMIT", "Invalid or excessive database records")
                rows.append((collection, record, _strict_json(payload.encode("utf-8"))))
    except sqlite3.Error as error:
        raise WorkspaceBackupError("INVALID_DATABASE", "Workspace SQLite validation failed") from error
    return rows


def _validate_payload(root: Path, *, destination: Path | None = None) -> None:
    """Validate metadata without following an archived absolute storage_uri."""
    for directory in [*(root / name for name in _DIRECTORIES),
                      *(root / "knowledge_vault" / name for name in ("originals", "derivatives", "page_images", "ocr", "equations", "extracted", "datasets", "manifests"))]:
        _require(not directory.exists() or directory.is_dir(), "UNSAFE_MEMBER", "Workspace storage area is not a directory")
    source_records: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "knowledge_vault" / "manifests").glob("*")):
        _require(path.is_file() and path.suffix == ".json", "INVALID_SOURCE", "Source manifest store contains unsupported records")
        value = _strict_json(path.read_bytes())
        try:
            record = SourceRecord.from_mapping(value)
        except (KeyError, TypeError, ValueError) as error:
            raise WorkspaceBackupError("INVALID_SOURCE", "Source manifest is incompatible") from error
        _require(type(value["source_id"]) is str and bool(_IDENTIFIER.fullmatch(record.source_id)) and path.stem == record.source_id
                 and bool(_SHA256.fullmatch(record.sha256)) and type(value["size_bytes"]) is int
                 and 0 <= record.size_bytes <= MAX_MEMBER_BYTES and type(value["version"]) is int and record.version >= 1,
                 "INVALID_SOURCE", "Source identity/hash/size/version is invalid")
        original = root / "knowledge_vault" / "originals" / record.source_id / record.sha256
        _require(original.is_file() and original.stat().st_size == record.size_bytes and _digest(original) == record.sha256,
                 "SOURCE_INTEGRITY", "Source original is missing or does not match its manifest")
        source_records[record.source_id] = value
        if destination is not None:
            value["storage_uri"] = str(destination / "knowledge_vault" / "originals" / record.source_id / record.sha256)
            _write_json(path, value)
    for path in sorted((root / "jobs").glob("*")):
        _require(path.is_file() and path.suffix == ".json", "INVALID_JOB", "Job store contains unsupported records")
        value = _strict_json(path.read_bytes())
        try:
            job = IngestionJob.from_mapping(value)
        except (KeyError, TypeError, ValueError) as error:
            raise WorkspaceBackupError("INVALID_JOB", "Job record is incompatible") from error
        _require(bool(_IDENTIFIER.fullmatch(job.job_id)) and path.stem == job.job_id and bool(_SHA256.fullmatch(job.source_hash)),
                 "INVALID_JOB", "Job identity/hash is invalid")
        if job.status.value in {"AVAILABLE", "APPROVED", "REVIEW_REQUIRED"}:
            _require(job.source_id in source_records and job.source_hash == source_records[job.source_id]["sha256"],
                     "INCONSISTENT_SNAPSHOT", "Available/reviewable job must bind its retained source original")
    for path in sorted((root / "conversations").glob("*")):
        _require(path.is_file() and path.suffix == ".json", "INVALID_CONVERSATION", "Conversation store contains unsupported records")
        value = _strict_json(path.read_bytes())
        _require(type(value.get("conversation_id")) is str and bool(_IDENTIFIER.fullmatch(value["conversation_id"]))
                 and path.stem == value["conversation_id"] and type(value.get("messages", [])) is list
                 and all(type(message) is dict and type(message.get("role")) is str and type(message.get("content")) is str
                         for message in value.get("messages", [])),
                 "INVALID_CONVERSATION", "Conversation identity/messages are incompatible")
    database = root / "workspace.sqlite"
    records = _database(database)
    for collection, record_id, value in records:
        if collection == "sources":
            source = source_records.get(record_id)
            _require(source is not None and value.get("source_id") == record_id
                     and value.get("sha256") == source["sha256"] and value.get("size_bytes") == source["size_bytes"],
                     "INCONSISTENT_SNAPSHOT", "Database source does not match backed-up vault metadata")
    if destination is not None and database.exists():
        with sqlite3.connect(database) as connection:
            connection.execute("PRAGMA trusted_schema=OFF")
            for record_id, value in source_records.items():
                connection.execute("UPDATE workspace_kv SET payload=? WHERE collection='sources' AND record_id=?",
                                   (json.dumps(value, sort_keys=True), record_id))
            connection.commit()


def _archive_members(archive: zipfile.ZipFile) -> tuple[dict[str, Any], list[zipfile.ZipInfo]]:
    members = archive.infolist()
    _require(0 < len(members) <= MAX_MEMBERS, "MEMBER_LIMIT", "Archive member count is invalid")
    seen: set[str] = set(); files: dict[str, zipfile.ZipInfo] = {}
    total = 0
    for member in members:
        _require(member.orig_filename == member.filename, "UNSAFE_ARCHIVE_PATH", "Archive filename was truncated or contains a NUL")
        name = _safe_name(member.filename, directory=member.is_dir())
        folded = name.casefold()
        _require(folded not in seen, "DUPLICATE_MEMBER", "Archive has duplicate/case-colliding paths")
        seen.add(folded)
        mode = member.external_attr >> 16
        _require(stat.S_IFMT(mode) in {0, stat.S_IFREG, stat.S_IFDIR}
                 and (not member.is_dir() or stat.S_IFMT(mode) != stat.S_IFREG)
                 and (member.is_dir() or stat.S_IFMT(mode) != stat.S_IFDIR),
                 "UNSAFE_MEMBER", "Archive symlinks/special files are not supported")
        _require(not member.flag_bits & 1 and member.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED},
                 "UNSUPPORTED_COMPRESSION", "Encrypted/unsupported compressed members are refused")
        _require(0 <= member.file_size <= MAX_MEMBER_BYTES, "MEMBER_LIMIT", "Archive member exceeds size limit")
        _require(not member.is_dir() or member.file_size == 0, "UNSAFE_MEMBER", "Directory archive members must have no payload")
        if name.startswith(("knowledge_vault/manifests/", "jobs/", "conversations/")) and not member.is_dir():
            _require(member.file_size <= MAX_JSON_BYTES, "JSON_LIMIT", "Metadata member exceeds size limit")
        total += member.file_size
        if not member.is_dir():
            files[name] = member
    _require(total <= MAX_EXPANDED_BYTES, "EXPANDED_LIMIT", "Archive expands beyond its declared limit")
    _require(_MANIFEST in files and files[_MANIFEST].file_size <= MAX_MANIFEST_BYTES, "INVALID_MANIFEST", "Missing/oversized backup manifest")
    folded_files = {name.casefold() for name in files}
    for name in files:
        _require(not any(str(parent).casefold() in folded_files for parent in PurePosixPath(name).parents if str(parent) != "."),
                 "UNSAFE_ARCHIVE_PATH", "A file is also used as a parent directory")
    manifest = _strict_json(archive.read(files[_MANIFEST]), limit=MAX_MANIFEST_BYTES)
    _require(type(manifest.get("root_name")) is str and bool(manifest["root_name"]) and "/" not in manifest["root_name"]
             and "\\" not in manifest["root_name"] and manifest["root_name"] not in {".", ".."}, "INVALID_MANIFEST", "Backup root name is invalid")
    if manifest.get("format") == _LEGACY_FORMAT:
        _require(set(manifest) == {"format", "root_name"}, "INVALID_MANIFEST", "Legacy backup manifest is incompatible")
    else:
        _require(manifest.get("format") == _FORMAT and type(manifest.get("manifest_schema_version")) is int and manifest.get("manifest_schema_version") == 2
                 and type(manifest.get("workspace_schema_version")) is int and manifest.get("workspace_schema_version") == 1 and manifest.get("pipeline_version") == PIPELINE_VERSION,
                 "UNSUPPORTED_VERSION", "Backup format/schema/pipeline version is unsupported")
        _require(set(manifest) == {"format", "manifest_schema_version", "workspace_schema_version", "pipeline_version", "root_name", "files", "snapshot_policy"}
                 and type(manifest["files"]) is dict and set(manifest["files"]) == set(files) - {_MANIFEST},
                 "INVALID_MANIFEST", "Backup inventory must match every payload member")
        _require(type(manifest["snapshot_policy"]) is str and 0 < len(manifest["snapshot_policy"]) <= 512,
                 "INVALID_MANIFEST", "Backup snapshot policy must be explicit bounded text")
        for name, declaration in manifest["files"].items():
            _require(type(declaration) is dict and set(declaration) == {"size_bytes", "sha256"}
                     and type(declaration["size_bytes"]) is int and declaration["size_bytes"] == files[name].file_size
                     and type(declaration["sha256"]) is str and bool(_SHA256.fullmatch(declaration["sha256"])),
                     "INVALID_MANIFEST", "Invalid payload size/checksum declaration")
    _require(bool(set(files) - {_MANIFEST}), "EMPTY_BACKUP", "Backup contains no workspace payload")
    return manifest, members


def _zip_preflight(stream: BinaryIO) -> None:
    """Bound ZIP32 directory allocation before ZipFile constructs member objects.

    ZIP64/multidisk/SFX archives are outside the bounded legacy/v2 profile.
    Counts are checked against actual directory records, not trusted blindly.
    """
    stream.seek(0, os.SEEK_END); length = stream.tell()
    _require(22 <= length <= MAX_ARCHIVE_BYTES, "ARCHIVE_LIMIT", "ZIP archive size is invalid")
    stream.seek(max(0, length - 65_557))
    tail = stream.read(65_557)
    index = tail.rfind(b"PK\x05\x06")
    _require(index >= 0 and len(tail) - index >= 22, "CORRUPT_ARCHIVE", "ZIP end directory is missing")
    _, disk, directory_disk, disk_count, count, size, offset, comment = struct.unpack_from("<4s4H2LH", tail, index)
    end = length - len(tail) + index
    _require(disk == directory_disk == 0 and disk_count == count and count != 0xffff
             and size != 0xffffffff and offset != 0xffffffff, "UNSUPPORTED_ARCHIVE", "ZIP64 or multidisk archives are unsupported")
    _require(end + 22 + comment == length and offset + size == end,
             "CORRUPT_ARCHIVE", "ZIP directory offsets/lengths are inconsistent")
    _require(0 < count <= MAX_MEMBERS and 0 < size <= MAX_CENTRAL_DIRECTORY_BYTES,
             "MEMBER_LIMIT", "ZIP central directory exceeds bounded count/size")
    stream.seek(offset)
    observed = 0
    while stream.tell() < end:
        header = stream.read(46)
        _require(len(header) == 46 and header[:4] == b"PK\x01\x02", "CORRUPT_ARCHIVE", "Invalid ZIP central directory record")
        name_size, extra_size, comment_size, starting_disk = struct.unpack_from("<4H", header, 28)
        observed += 1
        _require(observed <= MAX_MEMBERS and 0 < name_size <= 512 and extra_size <= 4096
                 and comment_size <= 4096 and starting_disk == 0, "MEMBER_LIMIT", "ZIP record metadata exceeds bounds")
        next_record = stream.tell() + name_size + extra_size + comment_size
        _require(next_record <= end, "CORRUPT_ARCHIVE", "ZIP record crosses directory boundary")
        stream.seek(next_record)
    _require(stream.tell() == end and observed == count, "CORRUPT_ARCHIVE", "ZIP declared and actual member counts disagree")
    stream.seek(0)


def _extract(archive: zipfile.ZipFile, members: list[zipfile.ZipInfo], manifest: dict[str, Any], staging: Path) -> None:
    total = 0
    for member in members:
        name = _safe_name(member.filename, directory=member.is_dir())
        path = staging / name
        if member.is_dir():
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            continue
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        digest = hashlib.sha256(); length = 0
        with archive.open(member) as incoming, path.open("xb") as outgoing:
            for block in iter(lambda: incoming.read(64 * 1024), b""):
                length += len(block); total += len(block)
                _require(length <= member.file_size and length <= MAX_MEMBER_BYTES and total <= MAX_EXPANDED_BYTES,
                         "EXPANDED_LIMIT", "Actual archive output exceeded bounded size")
                outgoing.write(block); digest.update(block)
            outgoing.flush(); os.fsync(outgoing.fileno())
        path.chmod(0o600)
        _require(length == member.file_size, "CORRUPT_ARCHIVE", "Archive payload length mismatch")
        if manifest["format"] == _FORMAT and name != _MANIFEST:
            _require(digest.hexdigest() == manifest["files"][name]["sha256"], "CHECKSUM_MISMATCH", "Backup payload checksum mismatch")


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@dataclass(frozen=True, slots=True, kw_only=True)
class BackupArchive:
    archive_path: Path
    included: tuple[str, ...]


def backup_workspace_root(root: Path, destination: Path) -> BackupArchive:
    root, destination = _owned_path(Path(root)), _owned_path(Path(destination))
    _require(root.is_dir(), "SOURCE_UNAVAILABLE", "Workspace directory does not exist")
    _require(not destination.exists(), "NO_OVERWRITE", "Backup destination already exists")
    _require(not destination.is_relative_to(root) or destination.is_relative_to(root / "backups"),
             "UNSAFE_DESTINATION", "Backup cannot overwrite or enter workspace source areas")
    before = _source_files(root)
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    _owned_path(destination.parent)
    with tempfile.TemporaryDirectory(prefix=".cosmos-backup-", dir=destination.parent) as temporary:
        staging = Path(temporary) / "payload"; staging.mkdir(mode=0o700)
        for name in sorted(before):
            _copy_regular(root / name, staging / name)
        database = root / "workspace.sqlite"
        if database.exists() or database.is_symlink():
            _sqlite_snapshot(database, staging / "workspace.sqlite")
        _require(before == _source_files(root), "SOURCE_CHANGED", "Workspace files changed; retry while writers are quiesced")
        for name in before:
            _require(_digest(root / name) == _digest(staging / name), "SOURCE_CHANGED", "Workspace bytes changed during backup")
        _validate_payload(staging)
        files: dict[str, _InventoryEntry] = {
            path.relative_to(staging).as_posix(): {"size_bytes": path.stat().st_size, "sha256": _digest(path)}
            for path in sorted(staging.rglob("*")) if path.is_file()}
        _require(bool(files) and sum(value["size_bytes"] for value in files.values()) <= MAX_EXPANDED_BYTES,
                 "EMPTY_BACKUP", "Workspace has no bounded backup payload")
        manifest = {"format": _FORMAT, "manifest_schema_version": 2, "workspace_schema_version": 1,
                    "pipeline_version": PIPELINE_VERSION, "root_name": root.name, "files": files,
                    "snapshot_policy": "Caller quiesces workspace writes; stable copied files and committed SQLite backup snapshot"}
        archive_path = Path(temporary) / "backup.zip"
        with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(_MANIFEST, json.dumps(manifest, sort_keys=True))
            for name in files:
                archive.write(staging / name, arcname=name)
        _require(archive_path.stat().st_size <= MAX_ARCHIVE_BYTES, "ARCHIVE_LIMIT", "Compressed backup exceeds limit")
        with zipfile.ZipFile(archive_path) as archive:
            _archive_members(archive)
        _require(before == _source_files(root), "SOURCE_CHANGED", "Workspace changed before backup publication")
        _owned_path(destination)
        archive_path.chmod(0o600)
        with archive_path.open("rb") as stream:
            os.fsync(stream.fileno())
        try:
            os.link(archive_path, destination)  # Atomic publish without overwriting.
        except FileExistsError as error:
            raise WorkspaceBackupError("NO_OVERWRITE", "Backup destination changed before publication") from error
        _fsync_directory(destination.parent)
    return BackupArchive(archive_path=destination, included=(_MANIFEST, *files))


def restore_workspace_root(archive_path: Path, destination: Path) -> Path:
    archive_path, destination = _owned_path(Path(archive_path)), _owned_path(Path(destination))
    protected = (Path.home(), Path(__file__).resolve().parents[2], Path.cwd())
    _require(destination.parent != destination and not any(path == destination or path.is_relative_to(destination) for path in protected),
             "UNSAFE_DESTINATION", "Restore cannot replace a home/repository/ancestor directory")
    _require(archive_path.is_file(), "ARCHIVE_UNAVAILABLE", "Backup archive does not exist")
    archive_stat = _stat_key(archive_path)
    _require(archive_stat[2] <= MAX_ARCHIVE_BYTES, "ARCHIVE_LIMIT", "Backup archive exceeds compressed limit")
    if destination.exists():
        _require(destination.is_dir() and (not any(destination.iterdir()) or (destination / "workspace.sqlite").is_file()),
                 "UNSAFE_DESTINATION", "Existing destination is not an empty directory or recognizable workspace")
    transaction: Path | None = None
    retained = False
    try:
        descriptor = os.open(archive_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as incoming:
            _require((os.fstat(incoming.fileno()).st_dev, os.fstat(incoming.fileno()).st_ino) == archive_stat[:2],
                     "SOURCE_CHANGED", "Archive changed during opening")
            _zip_preflight(incoming)
            with zipfile.ZipFile(incoming) as archive:
                manifest, members = _archive_members(archive)
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                _owned_path(destination.parent)
                transaction = Path(tempfile.mkdtemp(prefix=".cosmos-restore-recovery-", dir=destination.parent))
                staging = transaction / "staged"; staging.mkdir(mode=0o700)
                _extract(archive, members, manifest, staging)
                _validate_payload(staging)
                _require(_stat_key(archive_path) == archive_stat, "SOURCE_CHANGED", "Archive changed during validation")
                _validate_payload(staging, destination=destination)
        _owned_path(destination)
        receipt = {"format": "cosmos-restore-receipt-v1", "archive_format": manifest["format"],
                   "archive_sha256": _digest(archive_path), "destination": str(destination),
                   "previous_workspace": str(transaction / "previous") if destination.exists() else None,
                   "integrity_scope": "Per-member SHA256/size plus SQLite/source/schema checks" if manifest["format"] == _FORMAT else "Legacy CRC plus SQLite/source/schema checks; no full payload SHA inventory",
                   "signature": "not-authenticated; trusted administrator action required"}
        _require(_stat_key(archive_path) == archive_stat, "SOURCE_CHANGED", "Archive changed before restoration")
        _write_json(transaction / "restore_receipt.json", receipt)
        for folder in sorted((p for p in staging.rglob("*") if p.is_dir()), reverse=True):
            _fsync_directory(folder)
        _fsync_directory(staging)
        _fsync_directory(transaction)
        previous = transaction / "previous"
        existed = destination.exists()
        if existed:
            destination.rename(previous)
            retained = True
        try:
            staging.rename(destination)
            _fsync_directory(destination.parent)
        except OSError as error:
            if not existed and destination.exists():
                destination.rename(transaction / "failed-promotion")
            if existed:
                if destination.exists():
                    destination.rename(transaction / "failed-promotion")
                try:
                    previous.rename(destination)
                    retained = False
                except OSError as rollback_error:
                    raise WorkspaceBackupError("RESTORE_ROLLBACK_FAILED", f"Previous workspace remains recoverable at {previous}") from rollback_error
            raise WorkspaceBackupError("RESTORE_PROMOTION_FAILED", "Previous workspace restored after promotion failure") from error
        # A successful replacement retains old bytes; no user-owned tree deletion.
        retained = True
    except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, RuntimeError) as error:
        raise WorkspaceBackupError("CORRUPT_ARCHIVE", "Backup ZIP is invalid or corrupt") from error
    finally:
        if transaction is not None and not retained:
            shutil.rmtree(transaction)  # Only this private, newly created staging.
    return destination
