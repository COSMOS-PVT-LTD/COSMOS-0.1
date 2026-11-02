"""Coordinator-owned append-only attempts over the existing authority/IO lock."""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4

from infrastructure.persistence.sqlite_projects import SQLiteProjectRepository
from systems.contracts.geometry import GeometryBuildEvent
from systems.contracts.geometry.build import validate_events
from systems.persistence.job_repository import (
    TERMINAL,
    BlobAttachment,
    DurableJob,
    JobEvent,
    JobState,
    MonitorReceipt,
    StageReceipt,
    StoredBlob,
)
from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import (
    AccessDenied,
    Head,
    InvalidRecord,
    Principal,
    QuotaExceeded,
    RecordNotFound,
    SavedSnapshot,
    SchemaMismatch,
    identity,
)


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def message(code: str, **detail: object) -> RecordPayload:
    return RecordPayload.from_mapping({"code": code, **detail}, "cosmos.durable-job-event.v1")


# The existing solver samples every max(1,max_iterations//500) plus endpoints.
# Across its1..50,000 iteration envelope there are at most1001 events.
MAX_MONITORS = 1024


class SQLiteJobRepository:
    """Trusted coordinator adapter; never expose advance/recover to clients."""

    def __init__(self, repository: SQLiteProjectRepository) -> None:
        self.repository = repository
        if repository.schema_version >= 3:
            self.verify_integrity()

    def _schema(self) -> None:
        if self.repository.schema_version < 3:
            raise SchemaMismatch("Durable jobs require explicit schema3; the existing store was not upgraded.")

    @property
    def supports_monitors(self) -> bool:
        return self.repository.schema_version >= 5

    def _monitor_schema(self) -> None:
        if not self.supports_monitors:
            raise SchemaMismatch("Durable simulation monitors require schema5; existing storage was not upgraded.")

    @staticmethod
    def _monitor_header(row: sqlite3.Row) -> MonitorReceipt:
        return MonitorReceipt(row["sequence"], row["run_id"], row["content_hash"], row["byte_length"], row["created_at"])

    @staticmethod
    def _monitor_value(raw: bytes) -> dict[str, Any]:
        value = json.loads(raw)
        if type(value) is not dict or set(value) != {"seq", "iteration", "normalized_residual", "power_imbalance_w", "correlation_id"}:
            raise InvalidRecord("Exact original simulation monitor fields required.")
        if type(value["seq"]) is not int or not 0 <= value["seq"] < MAX_MONITORS or type(value["iteration"]) is not int or not 0 <= value["iteration"] <= 50_000:
            raise InvalidRecord("Invalid bounded simulation monitor sequence/iteration.")
        identity(value["correlation_id"], "native simulation run")
        for key in ("normalized_residual", "power_imbalance_w"):
            if type(value[key]) not in {int, float} or not math.isfinite(value[key]):
                raise InvalidRecord("Monitor quantities must be finite original numbers.")
        if value["normalized_residual"] < 0:
            raise InvalidRecord("Normalized equation residual cannot be negative.")
        return value

    def _monitor_transcript(self, connection: sqlite3.Connection, job_id: str) -> tuple[dict[str, Any], ...]:
        rows = connection.execute("SELECT * FROM durable_simulation_monitors WHERE job_id=? ORDER BY sequence", (job_id,)).fetchall()
        if len(rows) > MAX_MONITORS:
            raise InvalidRecord("Simulation monitor budget exceeded.")
        values: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            value = self._monitor_value(self.repository.files.read_blob(row["content_hash"], row["byte_length"]))
            if value["seq"] != index or row["sequence"] != index or value["correlation_id"] != row["run_id"]:
                raise InvalidRecord("Simulation monitor source/header mismatch.")
            if values and (value["correlation_id"] != values[0]["correlation_id"] or value["iteration"] <= values[-1]["iteration"]):
                raise InvalidRecord("Simulation monitor identity/iteration order changed.")
            values.append(value)
        if values and self._row(connection, job_id)["domain"] != "simulation-benchmark":
            raise InvalidRecord("Simulation monitors require an admitted benchmark study.")
        return tuple(values)

    def append_monitor(self, job_id: str, payload: RecordPayload) -> MonitorReceipt:
        self._monitor_schema()
        payload.validate(self.repository.policy)
        if payload.schema_id != "cosmos.simulation-monitor.v1" or payload.source_namespace != "p07-software-fixtures":
            raise InvalidRecord("Exact simulation monitor schema/source namespace required.")
        value = self._monitor_value(payload.data)
        with self.repository._transaction(write=True) as connection:
            job = self._read(connection, job_id)
            previous = self._monitor_transcript(connection, job_id)
            if value["seq"] < len(previous):
                row = connection.execute("SELECT * FROM durable_simulation_monitors WHERE job_id=? AND sequence=?", (job_id, value["seq"])).fetchone()
                if row["content_hash"] != payload.content_hash:
                    raise InvalidRecord("Monitor retry differs from original bytes.")
                return self._monitor_header(row)
            if job.domain != "simulation-benchmark" or job.state not in {JobState.RUNNING, JobState.CANCEL_REQUESTED} or value["seq"] != len(previous):
                raise InvalidRecord("Monitor must extend its admitted running study's contiguous transcript.")
            if previous and (value["correlation_id"] != previous[0]["correlation_id"] or value["iteration"] <= previous[-1]["iteration"]):
                raise InvalidRecord("Simulation monitor identity/iteration order changed.")
            self.repository.files.reserve(len(payload.data))
            self.repository.files.install_blob(payload.data, payload.content_hash)
            connection.execute("INSERT INTO durable_simulation_monitors VALUES(?,?,?,?,?,?)",
                (job_id, value["seq"], value["correlation_id"], payload.content_hash, len(payload.data), stamp()))
            self.repository._check_project_budget(connection, job.project_id)
            row = connection.execute("SELECT * FROM durable_simulation_monitors WHERE job_id=? AND sequence=?", (job_id, value["seq"])).fetchone()
            return self._monitor_header(row)

    def list_monitors(self, actor: Principal, project_id: str, job_id: str, *, after: int = -1, limit: int = 20) -> tuple[MonitorReceipt, ...]:
        self._monitor_schema()
        if type(after) is not int or not -1 <= after < MAX_MONITORS or type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidRecord("Use bounded simulation monitor paging.")
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            if self._row(connection, job_id)["project_id"] != project_id:
                raise RecordNotFound("Monitor is not in this authorized project.")
            return tuple(self._monitor_header(row) for row in connection.execute(
                "SELECT * FROM durable_simulation_monitors WHERE job_id=? AND sequence>? ORDER BY sequence LIMIT ?", (job_id, after, limit)))

    def monitor_source(self, actor: Principal, project_id: str, job_id: str, sequence: int) -> bytes:
        if type(sequence) is not int or not 0 <= sequence < MAX_MONITORS:
            raise InvalidRecord("Invalid simulation monitor sequence.")
        rows = self.list_monitors(actor, project_id, job_id, after=sequence-1, limit=1)
        if not rows or rows[0].sequence != sequence:
            raise RecordNotFound("Exact simulation monitor is unavailable.")
        return self.repository.files.read_blob(rows[0].content_hash, rows[0].byte_length)

    def verify_monitors(self, job_id: str, sources: tuple[bytes, ...]) -> None:
        self._monitor_schema()
        with self.repository._transaction() as connection:
            self._monitor_transcript(connection, job_id)
            rows = connection.execute("SELECT content_hash,byte_length FROM durable_simulation_monitors WHERE job_id=? ORDER BY sequence", (job_id,)).fetchall()
            if tuple((row[0], row[1]) for row in rows) != tuple((sha256(value).hexdigest(), len(value)) for value in sources):
                raise InvalidRecord("Terminal simulation monitor transcript differs from retained originals.")

    @property
    def supports_stages(self) -> bool:
        return self.repository.schema_version >= 4

    def _stage_schema(self) -> None:
        if not self.supports_stages:
            raise SchemaMismatch("Incremental native stages require reviewed schema4; no existing data was upgraded.")

    @staticmethod
    def _stage_header(row: sqlite3.Row) -> StageReceipt:
        return StageReceipt(row["sequence"], row["native_job_id"], row["state"], row["stage"],
                            row["content_hash"], row["byte_length"], row["created_at"])

    def _stage_transcript(self, connection: sqlite3.Connection, job_id: str) -> tuple[GeometryBuildEvent, ...]:
        rows = connection.execute("SELECT * FROM durable_geometry_stages WHERE job_id=? ORDER BY sequence", (job_id,)).fetchall()
        if len(rows) > 128:
            raise InvalidRecord("Native stage transcript exceeds its retained event budget.")
        events = []
        for row in rows:
            raw = self.repository.files.read_blob(row["content_hash"], row["byte_length"])
            event = GeometryBuildEvent.from_json(raw.decode("utf-8"))
            if (event.seq, event.job_id, event.state.value, event.stage, event.timestamp) != (
                row["sequence"], row["native_job_id"], row["state"], row["stage"], row["created_at"]):
                raise InvalidRecord("Native stage header disagrees with its immutable source.")
            events.append(event)
        if events:
            job = self._row(connection, job_id)
            source = self.repository._read_snapshot(connection, job["project_id"], job["domain"], job["object_id"], job["source_commit_id"])
            if not self._geometry_stage_source(source):
                raise InvalidRecord("Geometry stages require a geometry source.")
            correlation = json.loads(json.loads(source.payload)["request_json"])["correlation_id"]
            validate_events(tuple(events), events[0].job_id, correlation)
        return tuple(events)

    @staticmethod
    def _geometry_stage_source(source: SavedSnapshot) -> bool:
        return (source.domain == "geometry-fixture" and source.source_namespace == "p07-software-fixtures") or (
            source.domain == "engine-nozzle-build" and source.schema_id == "cosmos.engine-nozzle-build-input.v1"
            and isinstance(source.source_namespace, str) and source.source_namespace.startswith("engine-design-")) or (
            source.domain == "engine-component-build" and source.schema_id == "cosmos.engine-component-build-input.v1"
            and isinstance(source.source_namespace,str) and source.source_namespace.startswith("engine-component-")) or (
            source.domain == "picogk-component-build" and source.schema_id == "cosmos.picogk-component-build.v1"
            and isinstance(source.source_namespace,str) and source.source_namespace.startswith("engine-component-"))

    def append_stage(self, job_id: str, payload: RecordPayload) -> StageReceipt:
        """Called by the trusted host coordinator, not a client/native process."""
        self._stage_schema()
        payload.validate(self.repository.policy)
        if payload.schema_id != "cosmos.geometry-stage.v1":
            raise InvalidRecord("Exact geometry stage schema/source namespace is required.")
        event = GeometryBuildEvent.from_json(payload.data.decode("utf-8"))
        with self.repository._transaction(write=True) as connection:
            job = self._read(connection, job_id)
            source = self.repository._read_snapshot(connection, job.project_id, job.domain, job.object_id, job.source_commit_id)
            if not self._geometry_stage_source(source) or payload.source_namespace != source.source_namespace:
                raise InvalidRecord("Geometry stage must match its exact admitted source domain/schema/namespace.")
            previous = self._stage_transcript(connection, job_id)
            if event.seq < len(previous):
                row = connection.execute("SELECT * FROM durable_geometry_stages WHERE job_id=? AND sequence=?", (job_id, event.seq)).fetchone()
                if row["content_hash"] != payload.content_hash:
                    raise InvalidRecord("Native stage retry differs from its original bytes.")
                return self._stage_header(row)
            if job.state not in {JobState.RUNNING, JobState.CANCEL_REQUESTED} or len(previous) >= 128:
                raise InvalidRecord("Cannot append native stages to a terminal or full attempt.")
            correlation = json.loads(json.loads(source.payload)["request_json"])["correlation_id"]
            validate_events((*previous, event), previous[0].job_id if previous else event.job_id, correlation)
            self.repository.files.reserve(len(payload.data))
            self.repository.files.install_blob(payload.data, payload.content_hash)
            connection.execute("INSERT INTO durable_geometry_stages VALUES(?,?,?,?,?,?,?,?)",
                (job_id, event.seq, event.job_id, event.state.value, event.stage, payload.content_hash, len(payload.data), event.timestamp))
            self.repository._check_project_budget(connection, job.project_id)
            row = connection.execute("SELECT * FROM durable_geometry_stages WHERE job_id=? AND sequence=?", (job_id, event.seq)).fetchone()
            return self._stage_header(row)

    def list_stages(self, actor: Principal, project_id: str, job_id: str, *, after: int = -1, limit: int = 20) -> tuple[StageReceipt, ...]:
        self._stage_schema()
        if type(after) is not int or not -1 <= after < 128 or type(limit) is not int or not 1 <= limit <= 100:
            raise InvalidRecord("Use bounded native stage paging.")
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            if self._row(connection, job_id)["project_id"] != project_id:
                raise RecordNotFound("Native stages are not in this authorized project.")
            return tuple(self._stage_header(row) for row in connection.execute(
                "SELECT * FROM durable_geometry_stages WHERE job_id=? AND sequence>? ORDER BY sequence LIMIT ?", (job_id, after, limit)))

    def verify_stages(self, job_id: str, sources: tuple[bytes, ...]) -> None:
        """Trusted completion gate, independent of whether the actor was revoked.

        Revocation prevents selection/reads, not retention of the admitted work's
        original terminal evidence. This method is not a client read endpoint.
        """
        self._stage_schema()
        with self.repository._transaction() as connection:
            self._row(connection, job_id)
            self._stage_transcript(connection, job_id)
            rows = connection.execute("SELECT content_hash,byte_length FROM durable_geometry_stages WHERE job_id=? ORDER BY sequence", (job_id,)).fetchall()
            if tuple((row[0], row[1]) for row in rows) != tuple((sha256(value).hexdigest(), len(value)) for value in sources):
                raise InvalidRecord("Terminal candidate differs from its incrementally retained native transcript.")

    def stage_source(self, actor: Principal, project_id: str, job_id: str, sequence: int) -> bytes:
        if type(sequence) is not int or not 0 <= sequence < 128:
            raise InvalidRecord("Invalid exact stage sequence.")
        items = self.list_stages(actor, project_id, job_id, after=sequence-1, limit=1)
        if not items or items[0].sequence != sequence:
            raise RecordNotFound("Exact retained native stage is unavailable.")
        return self.repository.files.read_blob(items[0].content_hash, items[0].byte_length)

    def _row(self, connection: sqlite3.Connection, job_id: str) -> sqlite3.Row:
        identity(job_id, "job ID")
        row = connection.execute("SELECT * FROM durable_jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise RecordNotFound("Exact durable attempt is unavailable.")
        return row

    def _read(self, connection: sqlite3.Connection, job_id: str, through: int | None = None) -> DurableJob:
        row = self._row(connection, job_id)
        events = tuple(JobEvent(item["sequence"], JobState(item["state"]), item["content_hash"],
                                item["byte_length"], item["created_at"])
                       for item in connection.execute("SELECT * FROM durable_job_events WHERE job_id=? AND sequence<=? ORDER BY sequence",
                                                      (job_id, through if through is not None else 2**63-1)))
        if not events or any(event.sequence != i for i, event in enumerate(events)):
            raise InvalidRecord("Durable attempt event sequence is incomplete.")
        payload = self.repository.files.read_blob(events[-1].content_hash, events[-1].byte_length)
        source = connection.execute("SELECT head_commit_id FROM objects WHERE project_id=? AND domain=? AND object_id=?",
                                    (row["project_id"], row["domain"], row["object_id"])).fetchone()
        selected = connection.execute("SELECT selected_job_id,admitted_job_id FROM durable_job_selections WHERE project_id=? AND domain=? AND object_id=?",
                                      (row["project_id"], row["domain"], row["object_id"])).fetchone()
        blobs = tuple(StoredBlob(item["name"], item["content_hash"], item["byte_length"], item["kind"])
                      for item in connection.execute("SELECT * FROM durable_job_blobs WHERE job_id=? ORDER BY name", (job_id,))) if events[-1].state is JobState.COMPLETED else ()
        return DurableJob(job_id, row["project_id"], row["domain"], row["object_id"], row["source_commit_id"],
                          row["creator_user_id"], row["retry_of"], events, payload, blobs,
                          bool(selected and selected[0] == selected[1] == job_id and events[-1].state is JobState.COMPLETED),
                          bool(source and source[0] == row["source_commit_id"] and self.repository._dependencies_current(connection, row["source_commit_id"])))

    def _append(self, connection: sqlite3.Connection, job_id: str, state: JobState, payload: RecordPayload) -> None:
        payload.validate(self.repository.policy)
        self.repository.files.reserve(len(payload.data))
        self.repository.files.install_blob(payload.data, payload.content_hash)
        sequence = connection.execute("SELECT COUNT(*) FROM durable_job_events WHERE job_id=?", (job_id,)).fetchone()[0]
        if sequence >= 128:
            raise QuotaExceeded("Durable attempt event budget exhausted; no records evicted.")
        connection.execute("INSERT INTO durable_job_events VALUES(?,?,?,?,?,?)",
                           (job_id, sequence, state.value, payload.content_hash, len(payload.data), stamp()))

    def admit(self, actor: Principal, source: SavedSnapshot, *, operation_id: str,
              request_hash: str, retry_of: str | None = None) -> DurableJob:
        self._schema()
        Head(0, request_hash)
        repo = self.repository
        with repo._transaction(write=True) as connection:
            project = repo._authorize(connection, actor, source.project_id, write=True)
            replay = repo._replay(connection, actor, operation_id, request_hash)
            if replay is not None:
                return self._read(connection, replay["job_id"], replay["event_sequence"])
            repo._active(project)
            if not repo._dependencies_current(connection, source.commit_id):
                raise InvalidRecord("Captured upstream dependency is stale; retain history and select fresh inputs explicitly.")
            actual = repo._read_snapshot(connection, source.project_id, source.domain, source.object_id, None)
            repo._expected(actual.head, source.head)
            if actual.commit_id != source.commit_id:
                raise InvalidRecord("Attempt source must be the exact selected input commit.")
            if retry_of is not None:
                previous = self._read(connection, retry_of)
                if previous.project_id != source.project_id or previous.source_commit_id != source.commit_id or previous.state not in TERMINAL:
                    raise InvalidRecord("Retry requires a terminal exact-source attempt in this project.")
            outstanding = connection.execute("SELECT COUNT(*) FROM durable_jobs j JOIN durable_job_events e ON e.job_id=j.job_id "
                "WHERE e.sequence=(SELECT MAX(sequence) FROM durable_job_events WHERE job_id=j.job_id) "
                "AND e.state IN ('QUEUED','RUNNING','CANCEL_REQUESTED')").fetchone()[0]
            if outstanding >= 32:
                raise QuotaExceeded("Durable pending-attempt limit reached; cancel or recover explicitly.")
            job_id = str(uuid4())
            connection.execute("INSERT INTO durable_jobs(job_id,project_id,domain,object_id,source_commit_id,creator_user_id,retry_of,created_at) VALUES(?,?,?,?,?,?,?,?)",
                               (job_id, source.project_id, source.domain, source.object_id, source.commit_id, actor.user_id, retry_of, stamp()))
            self._append(connection, job_id, JobState.QUEUED, message("ADMITTED", source_commit_id=source.commit_id, source_head=asdict(source.head)))
            connection.execute("INSERT INTO durable_job_selections VALUES(?,?,?,?,NULL) ON CONFLICT(project_id,domain,object_id) "
                               "DO UPDATE SET admitted_job_id=excluded.admitted_job_id",
                               (source.project_id, source.domain, source.object_id, job_id))
            repo._remember(connection, actor, source.project_id, operation_id, request_hash, {"job_id": job_id, "event_sequence": 0})
            return self._read(connection, job_id)

    def get(self, actor: Principal, project_id: str, job_id: str) -> DurableJob:
        self._schema()
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            row = self._row(connection, job_id)
            if row["project_id"] != project_id:
                raise RecordNotFound("Attempt not in this authorized project.")
            return self._read(connection, job_id)

    def resolve_command(self, actor: Principal, project_id: str, *, operation_id: str, request_hash: str) -> DurableJob | None:
        self._schema()
        Head(0, request_hash)
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id, write=True)
            replay = self.repository._replay(connection, actor, operation_id, request_hash)
            if replay is None:
                return None
            if "job_id" not in replay:
                raise InvalidRecord("Operation is not an attempt receipt.")
            job = self._read(connection, replay["job_id"], replay["event_sequence"])
            if job.project_id != project_id:
                raise RecordNotFound("Attempt receipt is not in this project.")
            return job

    def list_ids(self, actor: Principal, project_id: str, *, object_id: str | None = None,
                 limit: int = 20, before: int | None = None, domain: str | None = None) -> tuple[tuple[int, str], ...]:
        self._schema()
        if object_id is not None:
            identity(object_id, "object ID")
        if domain is not None:
            identity(domain, "job domain")
        if type(limit) is not int or not 1 <= limit <= 100 or (before is not None and (type(before) is not int or not 0 < before <= 2**63-1)):
            raise InvalidRecord("Use a bounded job history page/cursor.")
        with self.repository._transaction() as connection:
            self.repository._authorize(connection, actor, project_id)
            return tuple((row[0], row[1]) for row in connection.execute(
                "SELECT ordinal,job_id FROM durable_jobs WHERE project_id=? AND (? IS NULL OR object_id=?) AND ordinal<? AND (? IS NULL OR domain=?) ORDER BY ordinal DESC LIMIT ?",
                (project_id, object_id, object_id, before if before is not None else 2**63-1, domain, domain, limit)))

    def cancel(self, actor: Principal, project_id: str, job_id: str, *, expected: Head,
               operation_id: str, request_hash: str) -> DurableJob:
        self._schema()
        Head(0, request_hash)
        repo = self.repository
        with repo._transaction(write=True) as connection:
            repo._active(repo._authorize(connection, actor, project_id, write=True))
            replay = repo._replay(connection, actor, operation_id, request_hash)
            if replay is not None:
                return self._read(connection, replay["job_id"], replay["event_sequence"])
            job = self._read(connection, job_id)
            if job.project_id != project_id:
                raise RecordNotFound("Attempt not in this authorized project.")
            repo._expected(job.head, expected)
            if job.state in TERMINAL or job.state is JobState.CANCEL_REQUESTED:
                raise InvalidRecord("Attempt is terminal or cancellation was already requested.")
            self._append(connection, job_id, JobState.CANCEL_REQUESTED, message("CANCEL_REQUESTED", actor_user_id=actor.user_id))
            repo._remember(connection, actor, project_id, operation_id, request_hash, {"job_id": job_id, "event_sequence": len(job.events)})
            return self._read(connection, job_id)

    def advance(self, job_id: str, state: JobState, payload: RecordPayload, *,
                attachments: tuple[BlobAttachment, ...] = (), actor: Principal | None = None,
                selection_allowed: bool = True) -> DurableJob:
        """Install bytes then append terminal metadata atomically. Coordinator only."""
        self._schema()
        repo = self.repository
        if type(selection_allowed) is not bool:
            raise InvalidRecord("Trusted completion selection gate must be a Boolean.")
        if not isinstance(state, JobState) or state in {JobState.QUEUED, JobState.CANCEL_REQUESTED}:
            raise InvalidRecord("Invalid coordinator transition.")
        with repo._transaction(write=True) as connection:
            job = self._read(connection, job_id)
            if job.state in TERMINAL:
                raise InvalidRecord("Terminal attempts cannot be rewritten.")
            if job.state is JobState.CANCEL_REQUESTED and state is not JobState.INTERRUPTED:
                state, attachments = JobState.CANCELLED, ()
                payload = message("CANCELLED", candidate_receipt=payload.data.decode("utf-8"))
            if attachments and state is not JobState.COMPLETED:
                raise InvalidRecord("Only completed candidates may retain exchange attachments.")
            if len(attachments) > 16 or len({item.name for item in attachments}) != len(attachments):
                raise InvalidRecord("Bounded unique attachment names required.")
            for item in attachments:
                identity(item.name, "attachment name")
                if item.kind not in {"source", "artifact", "diagnostic"}:
                    raise InvalidRecord("Unknown attachment kind.")
                repo.files.reserve(len(item.data))
                repo.files.install_blob(item.data, item.content_hash)
            self._append(connection, job_id, state, payload)
            for item in attachments:
                connection.execute("INSERT INTO durable_job_blobs VALUES(?,?,?,?,?)",
                                   (job_id, item.name, item.content_hash, len(item.data), item.kind))
            if state is JobState.COMPLETED and selection_allowed and actor is not None and actor.user_id == job.creator_user_id and job.current_input:
                try:
                    repo._active(repo._authorize(connection, actor, job.project_id, write=True))
                except AccessDenied:
                    pass  # Retain historical output, never select revoked/archived work.
                else:
                    connection.execute("UPDATE durable_job_selections SET selected_job_id=? WHERE project_id=? AND domain=? AND object_id=? AND admitted_job_id=?",
                                       (job_id, job.project_id, job.domain, job.object_id, job_id))
            repo._check_project_budget(connection, job.project_id)
            return self._read(connection, job_id)

    def blob(self, actor: Principal, project_id: str, job_id: str, name: str) -> bytes:
        job = self.get(actor, project_id, job_id)
        match = next((item for item in job.blobs if item.name == name), None)
        if match is None:
            raise RecordNotFound("Exact retained attachment is unavailable.")
        return self.repository.files.read_blob(match.content_hash, match.byte_length)

    def recover(self) -> int:
        """Call once after acquiring the app coordinator lease, never per read."""
        self._schema()
        with self.repository._transaction(write=True) as connection:
            rows = connection.execute("SELECT j.job_id,e.state FROM durable_jobs j JOIN durable_job_events e ON e.job_id=j.job_id "
                "WHERE e.sequence=(SELECT MAX(sequence) FROM durable_job_events WHERE job_id=j.job_id) "
                "AND e.state IN ('QUEUED','RUNNING','CANCEL_REQUESTED')").fetchall()
            for row in rows:
                self._append(connection, row[0], JobState.INTERRUPTED, message("COORDINATOR_RESTART", previous_state=row[1], auto_retried=False))
                project_id = self._row(connection, row[0])["project_id"]
                self.repository._check_project_budget(connection, project_id)
            return len(rows)

    def verify_integrity(self) -> None:
        self._schema()
        with self.repository._transaction() as connection:
            for row in connection.execute("SELECT content_hash,byte_length FROM durable_job_events UNION SELECT content_hash,byte_length FROM durable_job_blobs"):
                self.repository.files.read_blob(row[0], row[1])
            for row in connection.execute("SELECT job_id FROM durable_jobs"):
                job = self._read(connection, row[0])
                json.loads(job.payload)
                if sha256(job.payload).hexdigest() != job.events[-1].content_hash:
                    raise InvalidRecord("Attempt receipt checksum mismatch.")
                if self.supports_stages:
                    self._stage_transcript(connection, job.job_id)
                if self.supports_monitors:
                    self._monitor_transcript(connection, job.job_id)
