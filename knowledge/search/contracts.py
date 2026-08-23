"""
COSMOS Knowledge Foundation

Module:
    knowledge.search.contracts

Purpose:
    Backend-neutral search and retrieval contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.search.exceptions import SearchValidationError

__all__ = (
    "NO_VERIFIED_RESULT",
    "RetrievalMode",
    "SearchFilter",
    "SearchOrder",
    "SearchQuery",
    "SearchResult",
    "SearchResultPage",
)

NO_VERIFIED_RESULT = "NO VERIFIED RESULT"


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise SearchValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise SearchValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_limit(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SearchValidationError("limit must be an integer.")

    if value <= 0:
        raise SearchValidationError("limit must be a positive integer.")

    if value > 1000:
        raise SearchValidationError("limit must not exceed 1000.")

    return value


def _validate_offset(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SearchValidationError("offset must be an integer.")

    if value < 0:
        raise SearchValidationError("offset must be non-negative.")

    return value


class RetrievalMode(Enum):
    """Authorized retrieval modes."""

    LEXICAL = "LEXICAL"
    SEMANTIC = "SEMANTIC"
    STRUCTURED = "STRUCTURED"
    HYBRID = "HYBRID"


class SearchOrder(Enum):
    """Deterministic search result ordering."""

    RELEVANCE_DESC = "RELEVANCE_DESC"
    TARGET_ID_ASC = "TARGET_ID_ASC"


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchFilter:
    """Structured search filter criteria."""

    document_id: str | None = None
    lifecycle_state: str | None = None
    target_type: str | None = None

    def matches(self, metadata: dict[str, object]) -> bool:
        """Return True when metadata satisfies the filter."""

        if self.document_id is not None:
            if metadata.get("document_id") != self.document_id:
                return False

        if self.lifecycle_state is not None:
            if metadata.get("lifecycle_state") != self.lifecycle_state:
                return False

        if self.target_type is not None:
            if metadata.get("target_type") != self.target_type:
                return False

        return True


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchQuery:
    """Bounded search query contract."""

    text: str
    mode: RetrievalMode = RetrievalMode.HYBRID
    filters: SearchFilter = SearchFilter()
    order: SearchOrder = SearchOrder.RELEVANCE_DESC
    limit: int = 50
    offset: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "text",
            _validate_non_empty_string("text", self.text),
        )

        if not isinstance(self.mode, RetrievalMode):
            raise SearchValidationError(
                "mode must be a RetrievalMode value."
            )

        if not isinstance(self.filters, SearchFilter):
            raise SearchValidationError(
                "filters must be a SearchFilter instance."
            )

        if not isinstance(self.order, SearchOrder):
            raise SearchValidationError(
                "order must be a SearchOrder value."
            )

        object.__setattr__(self, "limit", _validate_limit(self.limit))
        object.__setattr__(self, "offset", _validate_offset(self.offset))


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchResult:
    """Single deterministic search result with provenance metadata."""

    target_id: str
    target_type: str
    score: float
    document_id: str | None = None
    lifecycle_state: str | None = None
    retrieval_mode: RetrievalMode | None = None
    ranking_reason: str | None = None

    def __post_init__(self) -> None:
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

        if not isinstance(self.score, (int, float)) or isinstance(
            self.score,
            bool,
        ):
            raise SearchValidationError("score must be a number.")

        score = float(self.score)

        if score < 0.0 or score > 1.0:
            raise SearchValidationError(
                "score must be between 0.0 and 1.0."
            )

        object.__setattr__(self, "score", score)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "target_id": self.target_id,
            "target_type": self.target_type,
            "score": self.score,
        }

        if self.document_id is not None:
            payload["document_id"] = self.document_id
        if self.lifecycle_state is not None:
            payload["lifecycle_state"] = self.lifecycle_state
        if self.retrieval_mode is not None:
            payload["retrieval_mode"] = self.retrieval_mode.value
        if self.ranking_reason is not None:
            payload["ranking_reason"] = self.ranking_reason

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class SearchResultPage:
    """Bounded paginated search results."""

    results: tuple[SearchResult, ...]
    total_count: int
    limit: int
    offset: int

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "results": [result.to_mapping() for result in self.results],
            "total_count": self.total_count,
            "limit": self.limit,
            "offset": self.offset,
        }
