"""
COSMOS Knowledge Foundation

Module:
    knowledge.indexing.models

Purpose:
    Index contracts and metadata for deterministic knowledge indexing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.indexing.exceptions import IndexValidationError

__all__ = (
    "IndexEntry",
    "IndexLifecycleState",
    "IndexMetadata",
    "IndexStatistics",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise IndexValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise IndexValidationError(f"{field_name} must not be blank.")

    return cleaned


class IndexLifecycleState(Enum):
    """Lifecycle state for a materialized index."""

    MISSING = "MISSING"
    BUILDING = "BUILDING"
    VALID = "VALID"
    STALE = "STALE"
    REBUILD_REQUIRED = "REBUILD_REQUIRED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True, kw_only=True)
class IndexEntry:
    """Single deterministic index entry referencing authoritative knowledge."""

    entry_id: str
    target_id: str
    target_type: str
    terms: tuple[str, ...]
    document_id: str | None = None
    lifecycle_state: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "entry_id",
            _validate_non_empty_string("entry_id", self.entry_id),
        )
        object.__setattr__(
            self,
            "target_id",
            _validate_non_empty_string("target_id", self.target_id),
        )
        object.__setattr__(
            self,
            "target_type",
            _validate_non_empty_string("target_type", self.target_type),
        )

        if not isinstance(self.terms, tuple):
            raise IndexValidationError("terms must be a tuple.")

        normalized_terms = tuple(
            sorted(
                {
                    _validate_non_empty_string("term", term).lower()
                    for term in self.terms
                }
            )
        )

        object.__setattr__(self, "terms", normalized_terms)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "entry_id": self.entry_id,
            "target_id": self.target_id,
            "target_type": self.target_type,
            "terms": list(self.terms),
        }

        if self.document_id is not None:
            payload["document_id"] = self.document_id
        if self.lifecycle_state is not None:
            payload["lifecycle_state"] = self.lifecycle_state

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class IndexMetadata:
    """Metadata describing a materialized index snapshot."""

    index_id: str
    source_digest: str
    entry_count: int
    lifecycle_state: IndexLifecycleState

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "index_id",
            _validate_non_empty_string("index_id", self.index_id),
        )
        object.__setattr__(
            self,
            "source_digest",
            _validate_non_empty_string("source_digest", self.source_digest),
        )

        if not isinstance(self.entry_count, int) or isinstance(
            self.entry_count,
            bool,
        ):
            raise IndexValidationError("entry_count must be an integer.")

        if self.entry_count < 0:
            raise IndexValidationError("entry_count must be non-negative.")

        if not isinstance(self.lifecycle_state, IndexLifecycleState):
            raise IndexValidationError(
                "lifecycle_state must be an IndexLifecycleState value."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "index_id": self.index_id,
            "source_digest": self.source_digest,
            "entry_count": self.entry_count,
            "lifecycle_state": self.lifecycle_state.value,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class IndexStatistics:
    """Aggregate statistics for an index."""

    entry_count: int
    unique_term_count: int
    target_count: int

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "entry_count": self.entry_count,
            "unique_term_count": self.unique_term_count,
            "target_count": self.target_count,
        }
