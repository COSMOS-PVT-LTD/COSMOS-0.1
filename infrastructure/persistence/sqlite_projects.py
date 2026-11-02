"""Opt-in SQLite implementation of the engineering project repository.

No application composition or legacy routing is changed by this module.
Each operation opens its own connection; the app coordinator must separately
hold CoordinatorLease. Scientific work never runs inside these transactions.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.serialization import canonical_json_dumps
from infrastructure.persistence.files import StoreFiles, private_file, sync_directory
from infrastructure.persistence.schema import (
    APPLICATION_ID,
    CURRENT_VERSION,
    SCHEMA,
    check_schema,
)
from systems.persistence.project_repository import Dependency, RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    HeadConflict,
    IntegrityFailure,
    InvalidRecord,
    Lifecycle,
    Membership,
    ObjectHead,
    OperationConflict,
    Principal,
    Project,
    QuotaExceeded,
    RecordNotFound,
    SavedSnapshot,
    SchemaMismatch,
    StoragePolicy,
    StoreUnavailable,
    identity,
    require_active_project,
    require_project_access,
)


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _digest(value: Mapping[str, object]) -> str:
    return sha256(canonical_json_dumps(value).encode("utf-8")).hexdigest()


def _response_record(payload: bytes | None) -> str | None:
    if payload is None:
        return None
    return json.dumps(
        {
            "format": "cosmos.command-response.v1",
            "sha256": sha256(payload).hexdigest(),
            "utf8": payload.decode("utf-8"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _response_bytes(text: str | None, limit: int) -> bytes | None:
    if text is None:
        return None
    try:
        if not isinstance(text, str) or len(text.encode("utf-8")) > 6 * limit + 1024:
            raise ValueError("Response exceeds retained metadata budget")
        record = json.loads(text)
        if (
            set(record) != {"format", "sha256", "utf8"}
            or record["format"] != "cosmos.command-response.v1"
        ):
            raise ValueError("Unknown response record")
        data = record["utf8"].encode("utf-8")
        if len(data) > limit or sha256(data).hexdigest() != record["sha256"]:
            raise ValueError("Response checksum differs")
        return data
    except (ValueError, TypeError, AttributeError, UnicodeError) as error:
        raise IntegrityFailure(
            "Retained command response checksum/format failed; no substitute is published."
        ) from error


def _metadata(title: str, mission: str) -> None:
    if not isinstance(title, str) or not title.strip() or len(title) > 240:
        raise InvalidRecord("Project title must contain 1–240 characters.")
    if not isinstance(mission, str) or len(mission) > 8192 or "\x00" in title + mission:
        raise InvalidRecord("Invalid bounded project mission metadata.")
    try:
        (title + mission).encode("utf-8")
    except UnicodeError as exc:
        raise InvalidRecord("Project metadata must be valid UTF-8.") from exc


def _project(row: Mapping[str, Any] | sqlite3.Row) -> Project:
    return Project(
        project_id=row["project_id"],
        title=row["title"],
        mission=row["mission"],
        owner_user_id=row["owner_user_id"],
        lifecycle=Lifecycle(row["lifecycle"]),
        head=Head(row["version"], row["content_hash"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _project_head(
    title: str, mission: str, owner: str, lifecycle: Lifecycle, version: int
) -> Head:
    return Head(
        version,
        _digest(
            {
                "title": title,
                "mission": mission,
                "owner_user_id": owner,
                "lifecycle": lifecycle.value,
                "version": version,
            }
        ),
    )


class SQLiteProjectRepository:
    """Internal authority handle; trusted services supply authenticated actors.

    Separate repository handles may coexist for one coordinator's requests.
    Construction does not acquire the application-lifetime coordinator lease.
    No automatic migration, orphan deletion, or schema repair is performed.
    """

    def __init__(
        self, root: Path | str, *, policy: StoragePolicy | None = None
    ) -> None:
        self.policy = policy or StoragePolicy()
        self.files = StoreFiles(Path(root), self.policy)
        self.path = self.files.root / "metadata.sqlite3"
        try:
            with self.files.write_lock():
                new = not self.path.exists() and not self.path.is_symlink()
                if new:
                    self.files.reserve()
                fd = private_file(self.path, create=new)
                os.close(fd)
                connection = self._connect(check=False)
                try:
                    if new:
                        connection.executescript(
                            "BEGIN EXCLUSIVE;\n"
                            + SCHEMA
                            + f"\nPRAGMA user_version={CURRENT_VERSION}; PRAGMA application_id={APPLICATION_ID}; COMMIT;",
                        )
                        sync_directory(self.files.root)
                    self.schema_version = check_schema(connection)
                    if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                        raise IntegrityFailure(
                            "Engineering database integrity check failed."
                        )
                    if (
                        connection.execute("PRAGMA foreign_key_check").fetchone()
                        is not None
                    ):
                        raise IntegrityFailure(
                            "Engineering database references are incomplete."
                        )
                    for row in connection.execute(
                        "SELECT DISTINCT content_hash,byte_length FROM commits"
                    ):
                        self.files.read_blob(row[0], row[1])
                    if self.schema_version >= 2:
                        for row in connection.execute(
                            "SELECT response_json FROM commit_contexts WHERE response_json IS NOT NULL"
                        ):
                            _response_bytes(row[0], self.policy.record_bytes)
                finally:
                    connection.close()
        except (sqlite3.DatabaseError, OSError) as exc:
            raise StoreUnavailable(
                "Engineering authority cannot be opened; existing data was not reset."
            ) from exc

    def _connect(self, *, check: bool = True) -> sqlite3.Connection:
        self.files.validate_paths()
        fd = private_file(self.path)
        os.close(fd)
        connection = sqlite3.connect(
            self.path, isolation_level=None, timeout=self.policy.busy_timeout_ms / 1000
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA trusted_schema=OFF")
            if connection.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
                raise SchemaMismatch(
                    "Unqualified journal mode; refusing an implicit conversion."
                )
            if check:
                check_schema(connection)
        except BaseException:
            connection.close()
            raise
        return connection

    @contextmanager
    def _transaction(self, *, write: bool = False) -> Iterator[sqlite3.Connection]:
        try:
            # Reads also open SQLite (and can recover a hot journal). Keep the
            # short IO lock through close; no scientific work runs inside it.
            with self.files.write_lock():
                connection = self._connect()
                try:
                    connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
                    yield connection
                    if write:
                        page_bytes = (
                            connection.execute("PRAGMA page_count").fetchone()[0]
                            * connection.execute("PRAGMA page_size").fetchone()[0]
                        )
                        self.files.reserve(
                            max(0, page_bytes - self.path.stat().st_size)
                        )
                    connection.commit()
                except BaseException:
                    connection.rollback()
                    raise
                finally:
                    connection.close()
        except sqlite3.IntegrityError as exc:
            raise IntegrityFailure(
                "Authority constraint rejected the transaction; nothing committed."
            ) from exc
        except (sqlite3.DatabaseError, OSError) as exc:
            raise StoreUnavailable(
                "Authority IO/busy failure; retry the same operation ID after recovery."
            ) from exc

    def _authorize(
        self,
        connection: sqlite3.Connection,
        actor: Principal,
        project_id: str,
        *,
        write: bool = False,
        owner: bool = False,
    ) -> Project:
        actor.require(write=write or owner)
        identity(project_id, "project ID")
        row = connection.execute(
            "SELECT p.*,m.capability FROM projects p LEFT JOIN project_members m "
            "ON p.project_id=m.project_id AND m.user_id=? WHERE p.project_id=?",
            (actor.user_id, project_id),
        ).fetchone()
        if row is None:
            raise RecordNotFound("Project not found.")
        capability = row["capability"]
        project = _project(row)
        require_project_access(
            actor,
            project,
            Membership(capability) if capability is not None else None,
            write=write,
            owner=owner,
        )
        return project

    def _replay(
        self,
        connection: sqlite3.Connection,
        actor: Principal,
        operation_id: str,
        request_hash: str,
    ) -> dict[str, Any] | None:
        identity(operation_id, "operation ID")
        row = connection.execute(
            "SELECT project_id,request_hash,result_json FROM operations WHERE actor_user_id=? AND operation_id=?",
            (actor.user_id, operation_id),
        ).fetchone()
        if row is None:
            return None
        if row["request_hash"] != request_hash:
            raise OperationConflict(
                "Operation ID was already used with another request."
            )
        self._authorize(connection, actor, row["project_id"])
        return json.loads(row["result_json"])

    def _remember(
        self,
        connection: sqlite3.Connection,
        actor: Principal,
        project_id: str,
        operation_id: str,
        request_hash: str,
        result: Mapping[str, object],
    ) -> None:
        connection.execute(
            "INSERT INTO operations VALUES(?,?,?,?,?)",
            (
                actor.user_id,
                operation_id,
                project_id,
                request_hash,
                canonical_json_dumps(result),
            ),
        )
        self._check_project_budget(connection, project_id)

    def _check_project_budget(
        self, connection: sqlite3.Connection, project_id: str
    ) -> None:
        # Logical retained bytes, not a claim about exact per-project SQLite
        # page ownership. Every commit reference is charged even if deduplicated.
        usage = connection.execute(
            """
            SELECT
              COALESCE((SELECT SUM(byte_length + LENGTH(CAST(commit_id || object_id || domain || schema_id || source_namespace || creator_user_id AS BLOB)) + 256)
                        FROM commits WHERE project_id=:project),0)
            + COALESCE((SELECT SUM(LENGTH(CAST(payload_json || actor_user_id || action AS BLOB)) + 64)
                        FROM project_events WHERE project_id=:project),0)
            + COALESCE((SELECT SUM(LENGTH(CAST(result_json || actor_user_id || operation_id AS BLOB)) + 64)
                        FROM operations WHERE project_id=:project),0)
            + COALESCE((SELECT LENGTH(CAST(title || mission || owner_user_id AS BLOB)) + 256
                        FROM projects WHERE project_id=:project),0)
            + COALESCE((SELECT SUM(LENGTH(CAST(user_id || capability AS BLOB)) + 64)
                        FROM project_members WHERE project_id=:project),0)
        """,
            {"project": project_id},
        ).fetchone()[0]
        if self.schema_version >= 2:
            usage += connection.execute(
                "SELECT COALESCE(SUM(LENGTH(CAST(COALESCE(x.response_json,'') AS BLOB))+256),0) "
                "FROM commit_contexts x JOIN commits c ON c.commit_id=x.commit_id WHERE c.project_id=?",
                (project_id,),
            ).fetchone()[0]
        if self.schema_version >= 3:
            usage += connection.execute(
                "SELECT COALESCE(SUM(LENGTH(CAST(job_id || object_id || creator_user_id AS BLOB))+512),0) FROM durable_jobs WHERE project_id=?",
                (project_id,),
            ).fetchone()[0]
            usage += connection.execute(
                "SELECT COALESCE(SUM(e.byte_length+256),0) FROM durable_job_events e JOIN durable_jobs j ON j.job_id=e.job_id WHERE j.project_id=?",
                (project_id,),
            ).fetchone()[0]
            usage += connection.execute(
                "SELECT COALESCE(SUM(b.byte_length+256),0) FROM durable_job_blobs b JOIN durable_jobs j ON j.job_id=b.job_id WHERE j.project_id=?",
                (project_id,),
            ).fetchone()[0]
        if self.schema_version >= 4:
            usage += connection.execute(
                "SELECT COALESCE(SUM(s.byte_length+256),0) FROM durable_geometry_stages s JOIN durable_jobs j ON j.job_id=s.job_id WHERE j.project_id=?",
                (project_id,),
            ).fetchone()[0]
        if self.schema_version >= 5:
            usage += connection.execute("SELECT COUNT(*)*512 FROM record_dependencies d JOIN commits c ON c.commit_id=d.commit_id WHERE c.project_id=?", (project_id,)).fetchone()[0]
            usage += connection.execute("SELECT COALESCE(SUM(m.byte_length+256),0) FROM durable_simulation_monitors m JOIN durable_jobs j ON j.job_id=m.job_id WHERE j.project_id=?", (project_id,)).fetchone()[0]
        if self.schema_version >= 6:
            usage += connection.execute("SELECT COALESCE(SUM(byte_length+512),0) FROM transfer_receipts WHERE project_id=?", (project_id,)).fetchone()[0]
        if usage > self.policy.project_bytes:
            raise QuotaExceeded(
                "Project retained record/metadata budget exhausted; transaction rolled back."
            )

    def _event(
        self,
        connection: sqlite3.Connection,
        actor: Principal,
        project_id: str,
        action: str,
        payload: Mapping[str, object],
    ) -> None:
        connection.execute(
            "INSERT INTO project_events(project_id,actor_user_id,action,payload_json,created_at) VALUES(?,?,?,?,?)",
            (
                project_id,
                actor.user_id,
                action,
                canonical_json_dumps(payload),
                _stamp(),
            ),
        )

    @staticmethod
    def _active(project: Project) -> None:
        require_active_project(project)

    @staticmethod
    def _expected(current: Head, expected: Head) -> None:
        if not isinstance(expected, Head):
            raise InvalidRecord("An expected version and content hash are required.")
        if current != expected:
            raise HeadConflict(current)

    @staticmethod
    def _project_result(project: Project) -> dict[str, object]:
        result = asdict(project)
        result.pop("head")
        result.update(
            version=project.head.version,
            content_hash=project.head.content_hash,
            lifecycle=project.lifecycle.value,
        )
        return result

    def create_project(
        self, actor: Principal, *, title: str, mission: str = "", operation_id: str
    ) -> Project:
        actor.require(write=True)
        _metadata(title, mission)
        identity(operation_id, "operation ID")
        request = _digest({"action": "create", "title": title, "mission": mission})
        with self._transaction(write=True) as connection:
            replay = self._replay(connection, actor, operation_id, request)
            if replay is not None:
                return _project(replay)
            self.files.reserve()
            project_id, stamp = str(uuid4()), _stamp()
            head = _project_head(title, mission, actor.user_id, Lifecycle.ACTIVE, 1)
            connection.execute(
                "INSERT INTO projects VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    project_id,
                    title,
                    mission,
                    actor.user_id,
                    "ACTIVE",
                    head.version,
                    head.content_hash,
                    stamp,
                    stamp,
                ),
            )
            connection.execute(
                "INSERT INTO project_members VALUES(?,?,'OWNER')",
                (project_id, actor.user_id),
            )
            project = self._authorize(connection, actor, project_id)
            result = self._project_result(project)
            self._event(connection, actor, project_id, "project.created", result)
            self._remember(connection, actor, project_id, operation_id, request, result)
            return project

    def get_project(self, actor: Principal, project_id: str) -> Project:
        with self._transaction() as connection:
            return self._authorize(connection, actor, project_id)

    def list_projects(
        self, actor: Principal, *, limit: int = 50, after_id: str = ""
    ) -> tuple[Project, ...]:
        actor.require()
        if type(limit) is not int or not 1 <= limit <= 200:
            raise InvalidRecord("Project page limit must be 1–200.")
        if after_id:
            identity(after_id)
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT p.* FROM projects p JOIN project_members m ON p.project_id=m.project_id "
                "WHERE m.user_id=? AND p.project_id>? AND (p.lifecycle!='DELETED' OR m.capability='OWNER') "
                "ORDER BY p.project_id LIMIT ?",
                (actor.user_id, after_id, limit),
            ).fetchall()
            return tuple(_project(row) for row in rows)

    def change_project(
        self,
        actor: Principal,
        project_id: str,
        *,
        expected: Head,
        operation_id: str,
        title: str | None = None,
        mission: str | None = None,
        lifecycle: Lifecycle | None = None,
        confirmation_project_id: str | None = None,
    ) -> Project:
        """Metadata edits or owner-only recoverable lifecycle changes, never purge."""
        identity(operation_id)
        if lifecycle is not None and not isinstance(lifecycle, Lifecycle):
            raise InvalidRecord("Unknown lifecycle.")
        if not isinstance(expected, Head):
            raise InvalidRecord("Expected project head required.")
        request = _digest(
            {
                "action": "project.change",
                "project_id": project_id,
                "expected": asdict(expected),
                "title": title,
                "mission": mission,
                "lifecycle": lifecycle.value if lifecycle else None,
                "confirmation_project_id": confirmation_project_id,
            }
        )
        with self._transaction(write=True) as connection:
            current = self._authorize(
                connection, actor, project_id, write=True, owner=lifecycle is not None
            )
            replay = self._replay(connection, actor, operation_id, request)
            if replay is not None:
                return _project(replay)
            self._expected(current.head, expected)
            if lifecycle is None:
                self._active(current)
            if lifecycle is Lifecycle.DELETED and confirmation_project_id != project_id:
                raise InvalidRecord(
                    "Tombstone requires exact project ID and expected-version confirmation."
                )
            next_title = current.title if title is None else title
            next_mission = current.mission if mission is None else mission
            next_lifecycle = current.lifecycle if lifecycle is None else lifecycle
            _metadata(next_title, next_mission)
            self.files.reserve()
            head = _project_head(
                next_title,
                next_mission,
                current.owner_user_id,
                next_lifecycle,
                current.head.version + 1,
            )
            connection.execute(
                "UPDATE projects SET title=?,mission=?,lifecycle=?,version=?,content_hash=?,updated_at=? "
                "WHERE project_id=? AND version=? AND content_hash=?",
                (
                    next_title,
                    next_mission,
                    next_lifecycle.value,
                    head.version,
                    head.content_hash,
                    _stamp(),
                    project_id,
                    expected.version,
                    expected.content_hash,
                ),
            )
            result_project = self._authorize(connection, actor, project_id)
            result = self._project_result(result_project)
            self._event(connection, actor, project_id, "project.changed", result)
            self._remember(connection, actor, project_id, operation_id, request, result)
            return result_project

    def set_member(
        self,
        actor: Principal,
        project_id: str,
        *,
        member: Principal,
        capability: Membership | None,
        expected: Head,
        operation_id: str,
    ) -> Project:
        """Trusted adapter resolves an actual account; only grants require active."""
        if capability is None:
            # Deactivation must not prevent the owner from revoking a retained
            # membership. Only granting access requires an active target account.
            identity(member.user_id, "stable member user ID")
        else:
            member.require()
        identity(operation_id)
        if (
            capability is Membership.OWNER
            or capability is not None
            and not isinstance(capability, Membership)
        ):
            raise InvalidRecord("Owner transfer/recovery is not a membership edit.")
        if not isinstance(expected, Head):
            raise InvalidRecord("Expected project head required.")
        request = _digest(
            {
                "action": "member.set",
                "project_id": project_id,
                "member": member.user_id,
                "capability": capability.value if capability else None,
                "expected": asdict(expected),
            }
        )
        with self._transaction(write=True) as connection:
            current = self._authorize(connection, actor, project_id, owner=True)
            replay = self._replay(connection, actor, operation_id, request)
            if replay is not None:
                return _project(replay)
            self._active(current)
            self._expected(current.head, expected)
            if member.user_id == current.owner_user_id:
                raise AccessDenied(
                    "Owner cannot be removed or downgraded by membership edits."
                )
            self.files.reserve()
            if capability is None:
                connection.execute(
                    "DELETE FROM project_members WHERE project_id=? AND user_id=?",
                    (project_id, member.user_id),
                )
            else:
                connection.execute(
                    "INSERT INTO project_members VALUES(?,?,?) ON CONFLICT(project_id,user_id) "
                    "DO UPDATE SET capability=excluded.capability",
                    (project_id, member.user_id, capability.value),
                )
            head = _project_head(
                current.title,
                current.mission,
                current.owner_user_id,
                current.lifecycle,
                current.head.version + 1,
            )
            connection.execute(
                "UPDATE projects SET version=?,content_hash=?,updated_at=? WHERE project_id=?",
                (
                    head.version,
                    head.content_hash,
                    _stamp(),
                    project_id,
                ),
            )
            result_project = self._authorize(connection, actor, project_id)
            result = self._project_result(result_project)
            self._event(
                connection,
                actor,
                project_id,
                "member.changed",
                {
                    "member_user_id": member.user_id,
                    "capability": capability.value if capability else None,
                    "project": result,
                },
            )
            self._remember(connection, actor, project_id, operation_id, request, result)
            return result_project

    @property
    def supports_dependencies(self) -> bool:
        return self.schema_version >= 5

    def _dependencies(self, connection: sqlite3.Connection, commit_id: str) -> tuple[Dependency, ...]:
        if not self.supports_dependencies:
            return ()
        return tuple(Dependency(row[0], row[1], row[2]) for row in connection.execute(
            "SELECT relation,source_commit_id,source_job_id FROM record_dependencies WHERE commit_id=? ORDER BY relation", (commit_id,)))

    def _dependencies_current(self, connection: sqlite3.Connection, commit_id: str) -> bool:
        pending = [(commit_id, 0)]
        seen: set[str] = set()
        while pending:
            current, depth = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            if len(seen) > 256 or depth > 16:
                raise InvalidRecord("Dependency applicability graph exceeds its bounded traversal.")
            for dependency in self._dependencies(connection, current):
                source = connection.execute("SELECT c.commit_id,o.head_commit_id,c.content_hash,c.byte_length FROM commits c JOIN objects o "
                    "ON c.project_id=o.project_id AND c.domain=o.domain AND c.object_id=o.object_id WHERE c.commit_id=?", (dependency.commit_id,)).fetchone()
                if source is None or source[0] != source[1]:
                    return False
                try:
                    self.files.read_blob(source[2], source[3])
                except IntegrityFailure:
                    return False  # Original study history remains readable, but cannot be CURRENT.
                if dependency.job_id is not None:
                    selected = connection.execute("SELECT s.admitted_job_id,s.selected_job_id,e.state FROM durable_jobs j "
                        "JOIN durable_job_selections s ON j.project_id=s.project_id AND j.domain=s.domain AND j.object_id=s.object_id "
                        "JOIN durable_job_events e ON e.job_id=j.job_id WHERE j.job_id=? AND j.source_commit_id=? "
                        "AND e.sequence=(SELECT MAX(sequence) FROM durable_job_events WHERE job_id=j.job_id)",
                        (dependency.job_id, dependency.commit_id)).fetchone()
                    if selected is None or selected[0] != dependency.job_id or selected[1] != dependency.job_id or selected[2] != "COMPLETED":
                        return False
                    references = connection.execute("SELECT content_hash,byte_length FROM durable_job_blobs WHERE job_id=? "
                        "UNION SELECT content_hash,byte_length FROM durable_job_events WHERE job_id=? AND state='COMPLETED'",
                        (dependency.job_id, dependency.job_id))
                    try:
                        for digest, length in references:
                            self.files.read_blob(digest, length)
                    except IntegrityFailure:
                        return False
                pending.append((dependency.commit_id, depth+1))
        return True

    def _dependency_scope(self, connection: sqlite3.Connection, actor: Principal, project_id: str, commit_id: str) -> None:
        if not self.supports_dependencies:
            raise SchemaMismatch("Dependency metadata requires schema5; no existing data was upgraded.")
        identity(commit_id, "commit ID")
        self._authorize(connection, actor, project_id)
        if connection.execute("SELECT 1 FROM commits WHERE project_id=? AND commit_id=?", (project_id, commit_id)).fetchone() is None:
            raise RecordNotFound("Dependency source is not in this authorized project.")

    def dependencies(self, actor: Principal, project_id: str, commit_id: str) -> tuple[Dependency, ...]:
        with self._transaction() as connection:
            self._dependency_scope(connection, actor, project_id, commit_id)
            return self._dependencies(connection, commit_id)

    def dependencies_current(self, actor: Principal, project_id: str, commit_id: str) -> bool:
        with self._transaction() as connection:
            self._dependency_scope(connection, actor, project_id, commit_id)
            return self._dependencies_current(connection, commit_id)

    def save_snapshot(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        input_revision: int,
        payload: RecordPayload,
        expected: Head,
        operation_id: str,
        command_hash: str | None = None,
        purpose: str = "save",
        source_commit_id: str | None = None,
        input_commit_id: str | None = None,
        retain_if_stale: bool = False,
        response_payload: bytes | None = None,
        dependencies: tuple[Dependency, ...] = (),
    ) -> SavedSnapshot:
        identity(domain, "domain")
        identity(object_id, "object ID")
        identity(operation_id, "operation ID")
        if type(input_revision) is not int or not 0 <= input_revision <= 2**63 - 1:
            raise InvalidRecord("Input revision must be a bounded nonnegative integer.")
        if not isinstance(expected, Head) or not isinstance(payload, RecordPayload):
            raise InvalidRecord("A typed payload and expected head are required.")
        payload.validate(self.policy)
        if type(dependencies) is not tuple or len(dependencies) > 16 or any(not isinstance(d, Dependency) for d in dependencies) or len({d.relation for d in dependencies}) != len(dependencies):
            raise InvalidRecord("Use at most 16 distinct typed dependency relations.")
        if dependencies and not self.supports_dependencies:
            raise SchemaMismatch("Dependencies require reviewed schema5; existing storage was not upgraded.")
        if command_hash is not None:
            Head(0, command_hash)
        if purpose not in {
            "save",
            "create",
            "calculation",
            "calculation_input",
            "activate",
            "branch",
        }:
            raise InvalidRecord("Unknown snapshot purpose.")
        if (
            type(retain_if_stale) is not bool
            or retain_if_stale
            and purpose != "calculation"
        ):
            raise InvalidRecord(
                "Only a captured calculation may retain a stale completion."
            )
        if response_payload is not None:
            RecordPayload(response_payload, "cosmos.command-response.v1").validate(
                self.policy
            )
        for ref in (source_commit_id, input_commit_id):
            if ref is not None:
                identity(ref, "source commit ID")
        extended = (
            purpose != "save"
            or command_hash is not None
            or source_commit_id is not None
            or input_commit_id is not None
            or response_payload is not None
            or retain_if_stale
        )
        if extended and self.schema_version < 2:
            raise SchemaMismatch(
                "Foundation v1 requires an explicit reviewed schema upgrade; no automatic migration occurred."
            )
        request = command_hash or _digest(
            {
                "action": "snapshot.save",
                "project_id": project_id,
                "domain": domain,
                "object_id": object_id,
                "input_revision": input_revision,
                "hash": payload.content_hash,
                "schema": payload.schema_id,
                "source_namespace": payload.source_namespace,
                "expected": asdict(expected),
            }
        )
        if extended and command_hash is None:
            request = _digest(
                {
                    "base": request,
                    "purpose": purpose,
                    "source_commit_id": source_commit_id,
                    "input_commit_id": input_commit_id,
                    "retain_if_stale": retain_if_stale,
                    "response_hash": sha256(response_payload or b"").hexdigest(),
                }
            )
        if dependencies and command_hash is None:
            request = _digest({"base": request, "dependencies": [asdict(item) for item in dependencies]})
        with self._transaction(write=True) as connection:
            current_project = self._authorize(connection, actor, project_id, write=True)
            replay = self._replay(connection, actor, operation_id, request)
            if replay is not None:
                return self._read_snapshot(
                    connection, project_id, domain, object_id, replay["commit_id"]
                )
            self._active(current_project)
            row = connection.execute(
                "SELECT * FROM objects WHERE project_id=? AND domain=? AND object_id=?",
                (
                    project_id,
                    domain,
                    object_id,
                ),
            ).fetchone()
            current_head = (
                Head(row["version"], row["content_hash"])
                if row is not None
                else Head.absent()
            )
            selected = current_head == expected
            if not retain_if_stale:
                self._expected(current_head, expected)
            if retain_if_stale and (source_commit_id is None or row is None):
                raise InvalidRecord(
                    "A late result requires a retained source on the existing object."
                )
            for ref in (source_commit_id, input_commit_id):
                if ref is not None:
                    source = connection.execute(
                        "SELECT * FROM commits WHERE project_id=? AND commit_id=?",
                        (project_id, ref),
                    ).fetchone()
                    if source is None:
                        raise RecordNotFound(
                            "Exact authorized source commit is unavailable."
                        )
                    if (
                        ref == source_commit_id
                        and retain_if_stale
                        and (
                            source["domain"] != domain
                            or source["object_id"] != object_id
                            or Head(source["version"], source["content_hash"])
                            != expected
                        )
                    ):
                        raise InvalidRecord(
                            "Calculation source does not match the captured object head."
                        )
            usage = connection.execute(
                "SELECT COALESCE(SUM(byte_length),0) FROM commits WHERE project_id=?",
                (project_id,),
            ).fetchone()[0]
            if usage + len(payload.data) > self.policy.project_bytes:
                raise QuotaExceeded(
                    "Project history budget exhausted; retained evidence was not evicted."
                )
            self.files.reserve(len(payload.data) + len(response_payload or b""))
            self.files.install_blob(payload.data, payload.content_hash)
            if row is None:
                connection.execute(
                    "INSERT INTO objects VALUES(?,?,?,NULL,0,?)",
                    (project_id, domain, object_id, Head.absent().content_hash),
                )
            commit_id, stamp = str(uuid4()), _stamp()
            parent_id = (
                source_commit_id
                if retain_if_stale
                else row["head_commit_id"]
                if row is not None
                else None
            )
            version = connection.execute(
                "SELECT COALESCE(MAX(version),0)+1 FROM commits WHERE project_id=? AND domain=? AND object_id=?",
                (project_id, domain, object_id),
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO commits VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    commit_id,
                    project_id,
                    domain,
                    object_id,
                    parent_id,
                    version,
                    input_revision,
                    payload.content_hash,
                    len(payload.data),
                    payload.schema_id,
                    payload.source_namespace,
                    actor.user_id,
                    stamp,
                ),
            )
            if self.schema_version >= 2:
                connection.execute(
                    "INSERT INTO commit_contexts VALUES(?,?,?,?,?,?)",
                    (
                        commit_id,
                        purpose,
                        source_commit_id,
                        input_commit_id,
                        int(selected),
                        _response_record(response_payload),
                    ),
                )
            for dependency in dependencies:
                connection.execute("INSERT INTO record_dependencies VALUES(?,?,?,?)",
                    (commit_id, dependency.relation, dependency.commit_id, dependency.job_id))
            updated = connection.execute(
                "UPDATE objects SET head_commit_id=?,version=?,content_hash=? "
                "WHERE project_id=? AND domain=? AND object_id=? AND version=? AND content_hash=?",
                (
                    commit_id,
                    version,
                    payload.content_hash,
                    project_id,
                    domain,
                    object_id,
                    expected.version,
                    expected.content_hash,
                ),
            )
            if selected and updated.rowcount != 1:
                raise HeadConflict(current_head)
            self._event(
                connection,
                actor,
                project_id,
                "snapshot.saved",
                {
                    "domain": domain,
                    "object_id": object_id,
                    "commit_id": commit_id,
                    "version": version,
                    "input_revision": input_revision,
                    "source_hash": payload.content_hash,
                    "selected_at_commit": selected,
                    "source_commit_id": source_commit_id,
                    "input_commit_id": input_commit_id,
                    "purpose": purpose,
                },
            )
            self._remember(
                connection,
                actor,
                project_id,
                operation_id,
                request,
                {"commit_id": commit_id, "domain": domain, "object_id": object_id},
            )
            return self._read_snapshot(
                connection, project_id, domain, object_id, commit_id
            )

    def _read_snapshot(
        self,
        connection: sqlite3.Connection,
        project_id: str,
        domain: str,
        object_id: str,
        commit_id: str | None,
    ) -> SavedSnapshot:
        if commit_id is None:
            head = connection.execute(
                "SELECT head_commit_id FROM objects WHERE project_id=? AND domain=? AND object_id=?",
                (
                    project_id,
                    domain,
                    object_id,
                ),
            ).fetchone()
            commit_id = head[0] if head is not None else None
        row = connection.execute(
            "SELECT * FROM commits WHERE project_id=? AND domain=? AND object_id=? AND commit_id=?",
            (
                project_id,
                domain,
                object_id,
                commit_id,
            ),
        ).fetchone()
        if row is None:
            raise RecordNotFound(
                "Exact project/object/commit not found; no latest-record substitution."
            )
        data = self.files.read_blob(row["content_hash"], row["byte_length"])
        context = (
            connection.execute(
                "SELECT * FROM commit_contexts WHERE commit_id=?", (row["commit_id"],)
            ).fetchone()
            if self.schema_version >= 2
            else None
        )
        return SavedSnapshot(
            project_id=project_id,
            domain=domain,
            object_id=object_id,
            commit_id=row["commit_id"],
            parent_commit_id=row["parent_commit_id"],
            input_revision=row["input_revision"],
            head=Head(row["version"], row["content_hash"]),
            schema_id=row["schema_id"],
            source_namespace=row["source_namespace"],
            payload=data,
            creator_user_id=row["creator_user_id"],
            created_at=row["created_at"],
            purpose=context["purpose"] if context else "save",
            source_commit_id=context["source_commit_id"] if context else None,
            input_commit_id=context["input_commit_id"] if context else None,
            selected_at_commit=bool(context["selected_at_commit"]) if context else True,
            response_payload=_response_bytes(
                context["response_json"], self.policy.record_bytes
            )
            if context
            else None,
        )

    def resolve_command(
        self, actor: Principal, project_id: str, *, operation_id: str, command_hash: str
    ) -> SavedSnapshot | None:
        Head(0, command_hash)
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id, write=True)
            replay = self._replay(connection, actor, operation_id, command_hash)
            if replay is None:
                return None
            return self._read_snapshot(
                connection,
                project_id,
                replay["domain"],
                replay["object_id"],
                replay["commit_id"],
            )

    def list_objects(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        limit: int = 20,
        after_id: str = "",
    ) -> tuple[ObjectHead, ...]:
        identity(domain)
        if after_id:
            identity(after_id)
        if type(limit) is not int or not 1 <= limit <= 20:
            raise InvalidRecord("Object page limit must be 1–20.")
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            rows = connection.execute(
                "SELECT * FROM objects WHERE project_id=? AND domain=? AND object_id>? ORDER BY object_id LIMIT ?",
                (project_id, domain, after_id, limit),
            ).fetchall()
            return tuple(
                ObjectHead(
                    row["object_id"],
                    row["head_commit_id"],
                    Head(row["version"], row["content_hash"]),
                )
                for row in rows
            )

    def is_managed_propulsion(self, object_id: str) -> bool:
        """Internal deny-only legacy gate. This never authorizes a scoped read."""
        with self._transaction() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM objects WHERE domain='propulsion' AND object_id=? LIMIT 1",
                    (object_id,),
                ).fetchone()
                is not None
            )

    def get_snapshot(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        commit_id: str | None = None,
    ) -> SavedSnapshot:
        identity(domain)
        identity(object_id)
        if commit_id is not None:
            identity(commit_id)
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            return self._read_snapshot(
                connection, project_id, domain, object_id, commit_id
            )

    def resolve_snapshot(self, actor: Principal, project_id: str, commit_id: str) -> SavedSnapshot:
        identity(commit_id)
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            row = connection.execute("SELECT domain,object_id FROM commits WHERE project_id=? AND commit_id=?", (project_id, commit_id)).fetchone()
            if row is None:
                raise RecordNotFound("Exact commit does not belong to this authorized project.")
            return self._read_snapshot(connection, project_id, row[0], row[1], commit_id)

    def list_domains(self, actor: Principal, project_id: str, *, limit: int = 20, after: str = "") -> tuple[str, ...]:
        if type(limit) is not int or not 1 <= limit <= 100 or not isinstance(after, str) or len(after) > 128:
            raise InvalidRecord("Use bounded domain index pages.")
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            return tuple(row[0] for row in connection.execute("SELECT DISTINCT domain FROM objects WHERE project_id=? AND domain>? ORDER BY domain LIMIT ?", (project_id, after, limit)))

    def project_events(self, actor: Principal, project_id: str, *, limit: int = 20, before: int | None = None) -> tuple[dict[str, object], ...]:
        if type(limit) is not int or not 1 <= limit <= 100 or before is not None and (type(before) is not int or not 0 < before < 2**63):
            raise InvalidRecord("Use bounded project event pages/cursors.")
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            return tuple(dict(row) for row in connection.execute("SELECT * FROM project_events WHERE project_id=? AND sequence<? ORDER BY sequence DESC LIMIT ?", (project_id, before or 2**63-1, limit)))

    def list_commit_ids(
        self,
        actor: Principal,
        project_id: str,
        *,
        domain: str,
        object_id: str,
        limit: int = 50,
        before_version: int | None = None,
    ) -> tuple[str, ...]:
        """Bounded history index; callers explicitly fetch individual source bytes."""
        identity(domain)
        identity(object_id)
        if type(limit) is not int or not 1 <= limit <= 200:
            raise InvalidRecord("History page limit must be 1–200.")
        if before_version is not None and (
            type(before_version) is not int or not 0 < before_version <= 2**63 - 1
        ):
            raise InvalidRecord("Invalid history cursor.")
        with self._transaction() as connection:
            self._authorize(connection, actor, project_id)
            rows = connection.execute(
                "SELECT commit_id FROM commits WHERE project_id=? AND domain=? AND object_id=? "
                "AND version<? ORDER BY version DESC LIMIT ?",
                (project_id, domain, object_id, before_version or 2**63 - 1, limit),
            ).fetchall()
            return tuple(row[0] for row in rows)
