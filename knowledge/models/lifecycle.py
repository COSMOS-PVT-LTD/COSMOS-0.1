"""Shared engineering-knowledge lifecycle, provenance, and V&V records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

__all__ = (
    "KnowledgeLifecycle",
    "ProvenanceTrace",
    "UncertaintyRecord",
    "VerificationRecord",
    "VersionRecord",
)


class KnowledgeLifecycle(Enum):
    """Mandatory lifecycle for production engineering knowledge."""

    IMPORTED = "IMPORTED"
    EXTRACTED = "EXTRACTED"
    CANDIDATE = "CANDIDATE"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"
    SUPERSEDED = "SUPERSEDED"


def _require_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-blank string.")
    return value.strip()


@dataclass(frozen=True, slots=True, kw_only=True)
class ProvenanceTrace:
    """Source trace required for every engineering knowledge entity."""

    source_reference_id: str
    document_id: str
    chapter: str | None = None
    section: str | None = None
    page: int | None = None
    extraction_method: str = "manual"
    reviewer: str | None = None
    version: str = "1.0.0"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_reference_id",
            _require_text("source_reference_id", self.source_reference_id),
        )
        object.__setattr__(self, "document_id", _require_text("document_id", self.document_id))
        if self.page is not None and self.page <= 0:
            raise ValueError("page must be a positive integer when set.")


@dataclass(frozen=True, slots=True, kw_only=True)
class VerificationRecord:
    """Verification or validation evidence attached to an engineering entity."""

    method: str
    status: str
    evidence: str
    reviewer: str | None = None
    date: datetime | None = None
    confidence: float | None = None
    limitations: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", _require_text("method", self.method))
        object.__setattr__(self, "status", _require_text("status", self.status))
        object.__setattr__(self, "evidence", _require_text("evidence", self.evidence))
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0.")
        if self.date is None:
            object.__setattr__(self, "date", datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True, kw_only=True)
class UncertaintyRecord:
    """Explicit uncertainty attached to a prediction or property."""

    kind: str
    magnitude: float
    unit: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", _require_text("kind", self.kind))
        if not isinstance(self.magnitude, (int, float)) or self.magnitude < 0:
            raise ValueError("magnitude must be a non-negative number.")


@dataclass(frozen=True, slots=True, kw_only=True)
class VersionRecord:
    """Immutable version metadata. Approved entities are superseded, not edited."""

    entity_version: str
    schema_version: str = "1.0.0"
    author: str
    change_reason: str
    created_at: datetime | None = None
    supersedes_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "entity_version", _require_text("entity_version", self.entity_version))
        object.__setattr__(self, "author", _require_text("author", self.author))
        object.__setattr__(self, "change_reason", _require_text("change_reason", self.change_reason))
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
