"""Durable project DTOs and access policy; no filesystem, SQL or API dependency.

These are storage/ownership contracts, not another scientific design aggregate.
Principals must be constructed by a trusted authentication adapter, never from
posted user/role fields. Reviewer/approver roles do not gain engineering writes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256


class ProjectStoreError(Exception):
    """Base for explicit, safe-to-classify authority errors."""


class InvalidRecord(ProjectStoreError):
    pass


class AccessDenied(ProjectStoreError):
    pass


class RecordNotFound(ProjectStoreError):
    pass


class IntegrityFailure(ProjectStoreError):
    pass


class StoreUnavailable(ProjectStoreError):
    pass


class QuotaExceeded(ProjectStoreError):
    pass


class SchemaMismatch(ProjectStoreError):
    pass


class Membership(str, Enum):
    OWNER = "OWNER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class Lifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


def identity(value: str, label: str = "identity") -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value
    ):
        raise InvalidRecord(f"Invalid {label}.")
    return value


@dataclass(frozen=True, slots=True)
class Principal:
    user_id: str
    global_role: str
    active: bool = True

    def require(self, *, write: bool = False) -> None:
        identity(self.user_id, "stable user ID")
        if (
            self.active is not True
            or not isinstance(self.global_role, str)
            or self.global_role
            not in {
                "VIEWER",
                "ENGINEER",
                "REVIEWER",
                "APPROVER",
                "ADMIN",
            }
        ):
            raise AccessDenied("An active authenticated account is required.")
        if write and self.global_role not in {"ENGINEER", "ADMIN"}:
            raise AccessDenied("Global role does not permit engineering writes.")


@dataclass(frozen=True, slots=True)
class Head:
    version: int
    content_hash: str

    def __post_init__(self) -> None:
        if type(self.version) is not int or not 0 <= self.version < 2**63:
            raise InvalidRecord("Version must be a bounded nonnegative integer.")
        if not isinstance(self.content_hash, str) or not re.fullmatch(
            r"[0-9a-f]{64}", self.content_hash
        ):
            raise InvalidRecord("Expected a lowercase SHA-256 content hash.")

    @classmethod
    def absent(cls) -> Head:
        return cls(0, sha256(b"").hexdigest())


class HeadConflict(ProjectStoreError):
    def __init__(self, current: Head) -> None:
        super().__init__("Saved state changed; reload and reconcile before saving.")
        self.current = current


class OperationConflict(ProjectStoreError):
    """An operation ID was reused with a different request."""


@dataclass(frozen=True, slots=True)
class Project:
    project_id: str
    title: str
    mission: str
    owner_user_id: str
    lifecycle: Lifecycle
    head: Head
    created_at: str
    updated_at: str


def require_project_access(
    actor: Principal,
    project: Project,
    capability: Membership | None,
    *,
    write: bool = False,
    owner: bool = False,
) -> None:
    """Pure membership/global-role policy, shared by repository adapters."""
    actor.require(write=write or owner)
    if capability is None or owner and capability is not Membership.OWNER:
        raise AccessDenied("Project membership does not permit this operation.")
    if write and capability not in {Membership.OWNER, Membership.EDITOR}:
        raise AccessDenied("Project is read-only for this member.")
    if project.lifecycle is Lifecycle.DELETED and capability is not Membership.OWNER:
        raise AccessDenied("Only the owner can inspect/restore a tombstoned project.")


def require_active_project(project: Project) -> None:
    if project.lifecycle is not Lifecycle.ACTIVE:
        raise AccessDenied(
            "Archived/tombstoned projects are read-only; explicitly restore first."
        )


@dataclass(frozen=True, slots=True)
class SavedSnapshot:
    project_id: str
    domain: str
    object_id: str
    commit_id: str
    parent_commit_id: str | None
    input_revision: int
    head: Head
    schema_id: str
    source_namespace: str
    payload: bytes
    creator_user_id: str
    created_at: str
    purpose: str = "save"
    source_commit_id: str | None = None
    input_commit_id: str | None = None
    selected_at_commit: bool = True
    response_payload: bytes | None = None


@dataclass(frozen=True, slots=True)
class ObjectHead:
    object_id: str
    commit_id: str
    head: Head


@dataclass(frozen=True, slots=True)
class StoragePolicy:
    record_bytes: int = 16 * 1024 * 1024
    blob_bytes: int = 256 * 1024 * 1024
    project_bytes: int = 2 * 1024 * 1024 * 1024
    store_bytes: int = 10 * 1024 * 1024 * 1024
    busy_timeout_ms: int = 2000

    def __post_init__(self) -> None:
        values = (
            self.record_bytes,
            self.blob_bytes,
            self.project_bytes,
            self.store_bytes,
            self.busy_timeout_ms,
        )
        if any(type(value) is not int or value <= 0 for value in values):
            raise InvalidRecord("Storage limits must be positive integers.")
        if self.record_bytes > self.blob_bytes or self.busy_timeout_ms > 60_000:
            raise InvalidRecord("Invalid record/blob limit or busy timeout.")
