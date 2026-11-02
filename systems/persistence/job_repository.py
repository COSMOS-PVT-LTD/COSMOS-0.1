"""Durable attempt DTOs. Runtime futures/process handles are never stored."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from systems.persistence.project_repository import RecordPayload
from systems.projects.authority import Head, Principal, SavedSnapshot


class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    INTERRUPTED = "INTERRUPTED"


TERMINAL = frozenset({JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED, JobState.INTERRUPTED})


@dataclass(frozen=True)
class BlobAttachment:
    name: str
    data: bytes
    content_hash: str
    kind: str


@dataclass(frozen=True)
class StoredBlob:
    name: str
    content_hash: str
    byte_length: int
    kind: str


@dataclass(frozen=True)
class JobEvent:
    sequence: int
    state: JobState
    content_hash: str
    byte_length: int
    created_at: str


@dataclass(frozen=True)
class StageReceipt:
    sequence: int
    native_job_id: str
    state: str
    stage: str
    content_hash: str
    byte_length: int
    created_at: str


@dataclass(frozen=True)
class MonitorReceipt:
    sequence: int
    run_id: str
    content_hash: str
    byte_length: int
    created_at: str


@dataclass(frozen=True)
class DurableJob:
    job_id: str
    project_id: str
    domain: str
    object_id: str
    source_commit_id: str
    creator_user_id: str
    retry_of: str | None
    events: tuple[JobEvent, ...]
    payload: bytes
    blobs: tuple[StoredBlob, ...]
    selected: bool
    current_input: bool

    @property
    def state(self) -> JobState:
        return self.events[-1].state

    @property
    def head(self) -> Head:
        return Head(len(self.events), self.events[-1].content_hash)


class JobRepository(Protocol):
    @property
    def supports_monitors(self) -> bool: ...
    def append_monitor(self, job_id: str, payload: RecordPayload) -> MonitorReceipt: ...
    def list_monitors(self, actor: Principal, project_id: str, job_id: str, *, after: int = -1, limit: int = 20) -> tuple[MonitorReceipt, ...]: ...
    def monitor_source(self, actor: Principal, project_id: str, job_id: str, sequence: int) -> bytes: ...
    def verify_monitors(self, job_id: str, sources: tuple[bytes, ...]) -> None: ...
    @property
    def supports_stages(self) -> bool: ...
    def append_stage(self, job_id: str, payload: RecordPayload) -> StageReceipt: ...
    def verify_stages(self, job_id: str, sources: tuple[bytes, ...]) -> None: ...
    def list_stages(self, actor: Principal, project_id: str, job_id: str, *, after: int = -1, limit: int = 20) -> tuple[StageReceipt, ...]: ...
    def stage_source(self, actor: Principal, project_id: str, job_id: str, sequence: int) -> bytes: ...
    def resolve_command(self, actor: Principal, project_id: str, *, operation_id: str, request_hash: str) -> DurableJob | None: ...
    def admit(self, actor: Principal, source: SavedSnapshot, *, operation_id: str,
              request_hash: str, retry_of: str | None = None) -> DurableJob: ...
    def get(self, actor: Principal, project_id: str, job_id: str) -> DurableJob: ...
    def list_ids(self, actor: Principal, project_id: str, *, object_id: str | None = None,
                 limit: int = 20, before: int | None = None, domain: str | None = None) -> tuple[tuple[int, str], ...]: ...
    def cancel(self, actor: Principal, project_id: str, job_id: str, *, expected: Head,
               operation_id: str, request_hash: str) -> DurableJob: ...
    def advance(self, job_id: str, state: JobState, payload: RecordPayload, *,
                attachments: tuple[BlobAttachment, ...] = (), actor: Principal | None = None,
                selection_allowed: bool = True) -> DurableJob: ...
    def blob(self, actor: Principal, project_id: str, job_id: str, name: str) -> bytes: ...
