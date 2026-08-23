"""Deterministic retrieval diagnostics for controlled local search (Step 6)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from knowledge.search.contracts import SearchQuery, SearchResult, SearchResultPage

__all__ = (
    "RetrievalDiagnosticEntry",
    "RetrievalDiagnostics",
    "build_retrieval_diagnostics",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RetrievalDiagnosticEntry:
    """Per-result retrieval diagnostic record."""

    target_id: str
    score: float
    retrieval_mode: str
    ranking_reason: str
    document_id: str | None
    lifecycle_state: str | None

    def to_mapping(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "lifecycle_state": self.lifecycle_state,
            "ranking_reason": self.ranking_reason,
            "retrieval_mode": self.retrieval_mode,
            "score": self.score,
            "target_id": self.target_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class RetrievalDiagnostics:
    """Deterministic retrieval diagnostics for a search result page."""

    query_text: str
    retrieval_mode: str
    total_count: int
    returned_count: int
    entries: tuple[RetrievalDiagnosticEntry, ...]
    report_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "entries": [entry.to_mapping() for entry in self.entries],
            "query_text": self.query_text,
            "report_digest": self.report_digest,
            "retrieval_mode": self.retrieval_mode,
            "returned_count": self.returned_count,
            "total_count": self.total_count,
        }


def _entry_from_result(result: SearchResult) -> RetrievalDiagnosticEntry:
    return RetrievalDiagnosticEntry(
        target_id=result.target_id,
        score=result.score,
        retrieval_mode=(
            result.retrieval_mode.value
            if result.retrieval_mode is not None
            else "UNKNOWN"
        ),
        ranking_reason=result.ranking_reason or "",
        document_id=result.document_id,
        lifecycle_state=result.lifecycle_state,
    )


def _diagnostics_digest(
    query: SearchQuery,
    page: SearchResultPage,
    entries: tuple[RetrievalDiagnosticEntry, ...],
) -> str:
    payload = {
        "entries": [entry.to_mapping() for entry in entries],
        "limit": page.limit,
        "offset": page.offset,
        "query_text": query.text,
        "retrieval_mode": query.mode.value if query.mode is not None else "UNKNOWN",
        "total_count": page.total_count,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_retrieval_diagnostics(
    query: SearchQuery,
    page: SearchResultPage,
) -> RetrievalDiagnostics:
    """Build deterministic retrieval diagnostics from a search result page."""

    entries = tuple(_entry_from_result(result) for result in page.results)
    digest = _diagnostics_digest(query, page, entries)

    return RetrievalDiagnostics(
        query_text=query.text,
        retrieval_mode=query.mode.value if query.mode is not None else "UNKNOWN",
        total_count=page.total_count,
        returned_count=len(entries),
        entries=entries,
        report_digest=digest,
    )
