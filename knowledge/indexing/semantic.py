"""
COSMOS Knowledge Foundation

Module:
    knowledge.indexing.semantic

Purpose:
    Backend-neutral semantic indexing abstraction without embedding lock-in.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.graph.repository import GraphStore
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.lexical import tokenize_text
from knowledge.indexing.models import (
    IndexEntry,
    IndexLifecycleState,
    IndexMetadata,
    IndexStatistics,
)

__all__ = (
    "InMemorySemanticIndex",
    "SemanticIndex",
    "semantic_similarity_score",
)


def semantic_similarity_score(
    left_terms: tuple[str, ...],
    right_terms: tuple[str, ...],
) -> float:
    """Return a deterministic overlap-based semantic similarity score."""

    if not left_terms or not right_terms:
        return 0.0

    left_set = set(left_terms)
    right_set = set(right_terms)
    union = left_set | right_set

    if not union:
        return 0.0

    return len(left_set & right_set) / len(union)


class SemanticIndex(Protocol):
    """Semantic index provider abstraction."""

    def metadata(self) -> IndexMetadata:
        """Return index metadata."""

    def statistics(self) -> IndexStatistics:
        """Return aggregate index statistics."""

    def entries(self) -> tuple[IndexEntry, ...]:
        """Return semantic entries in deterministic order."""

    def similarity(
        self,
        query_terms: tuple[str, ...],
        *,
        limit: int,
    ) -> tuple[tuple[IndexEntry, float], ...]:
        """Return ranked semantic matches with deterministic tie-breaking."""

    def is_stale(self, source_digest: str) -> bool:
        """Return True when the semantic index is stale."""


class InMemorySemanticIndex:
    """
    Reference semantic index using deterministic term-overlap scoring.

    This is an offline-capable abstraction, not an embedding engine.
    """

    def __init__(
        self,
        *,
        index_id: str,
        source_digest: str,
        entries: Sequence[IndexEntry],
    ) -> None:
        self._index_id = index_id.strip()
        self._source_digest = source_digest.strip()
        sorted_entries = tuple(
            sorted(entries, key=lambda entry: entry.entry_id)
        )
        seen_entry_ids: set[str] = set()

        for entry in sorted_entries:
            if entry.entry_id in seen_entry_ids:
                raise IndexValidationError(
                    f"Duplicate semantic entry_id '{entry.entry_id}'."
                )

            seen_entry_ids.add(entry.entry_id)

        self._entries = sorted_entries

    def metadata(self) -> IndexMetadata:
        return IndexMetadata(
            index_id=self._index_id,
            source_digest=self._source_digest,
            entry_count=len(self._entries),
            lifecycle_state=IndexLifecycleState.VALID,
        )

    def statistics(self) -> IndexStatistics:
        target_ids = {entry.target_id for entry in self._entries}

        unique_terms = {
            term for entry in self._entries for term in entry.terms
        }

        return IndexStatistics(
            entry_count=len(self._entries),
            unique_term_count=len(unique_terms),
            target_count=len(target_ids),
        )

    def entries(self) -> tuple[IndexEntry, ...]:
        return self._entries

    def similarity(
        self,
        query_terms: tuple[str, ...],
        *,
        limit: int,
    ) -> tuple[tuple[IndexEntry, float], ...]:
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise IndexValidationError("limit must be an integer.")

        if limit < 0:
            raise IndexValidationError("limit must be non-negative.")

        normalized_terms = tuple(
            sorted(
                {
                    term.strip().lower()
                    for term in query_terms
                    if term.strip()
                }
            )
        )

        if not normalized_terms or limit == 0:
            return ()

        scored = [
            (
                entry,
                semantic_similarity_score(normalized_terms, entry.terms),
            )
            for entry in self._entries
        ]

        filtered = [
            (entry, score)
            for entry, score in scored
            if score > 0.0
        ]

        ranked = sorted(
            filtered,
            key=lambda item: (-item[1], item[0].entry_id),
        )

        return tuple(ranked[:limit])

    def is_stale(self, source_digest: str) -> bool:
        return self._source_digest != source_digest.strip()


def build_semantic_index_from_store(
    store: GraphStore,
    *,
    index_id: str = "semantic-default",
) -> InMemorySemanticIndex:
    """Build a semantic index from graph store searchable properties."""

    record = store.snapshot()
    source_digest = canonical_graph_record_digest(record)
    entries: list[IndexEntry] = []

    for node in sorted(record.nodes, key=lambda item: item.node_id):
        searchable_values: list[str] = [node.node_type]

        for key in (
            "extracted_label",
            "canonical_name",
            "confidence_band",
        ):
            value = node.properties.get(key)

            if isinstance(value, str) and value.strip():
                searchable_values.append(value)

        terms = tuple(
            sorted(
                {
                    token
                    for value in searchable_values
                    for token in tokenize_text(value)
                }
            )
        )

        if not terms:
            continue

        lifecycle_value = node.properties.get("lifecycle_state")
        document_id = node.properties.get("document_id")

        entries.append(
            IndexEntry(
                entry_id=f"sem:{node.node_id}",
                target_id=node.node_id,
                target_type=node.node_type,
                terms=terms,
                document_id=str(document_id)
                if isinstance(document_id, str)
                else None,
                lifecycle_state=str(lifecycle_value)
                if lifecycle_value is not None
                else None,
            )
        )

    return InMemorySemanticIndex(
        index_id=index_id,
        source_digest=source_digest,
        entries=entries,
    )


def require_fresh_semantic_index(
    index: SemanticIndex,
    source_digest: str,
) -> None:
    """Raise when the semantic index is stale."""

    if index.is_stale(source_digest):
        raise IndexStaleError(
            "Semantic index is stale relative to authoritative knowledge."
        )
