"""
COSMOS Knowledge Foundation

Module:
    knowledge.indexing.lexical

Purpose:
    Deterministic lexical indexing over graph knowledge targets.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol

from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.graph.repository import GraphStore
from knowledge.indexing.exceptions import (
    IndexNotFoundError,
    IndexStaleError,
    IndexValidationError,
)
from knowledge.indexing.models import (
    IndexEntry,
    IndexLifecycleState,
    IndexMetadata,
    IndexStatistics,
)

__all__ = (
    "InMemoryLexicalIndex",
    "LexicalIndex",
    "tokenize_text",
)

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize_text(value: str) -> tuple[str, ...]:
    """Return deterministic normalized tokens from searchable text."""

    if not isinstance(value, str):
        raise IndexValidationError("value must be a string.")

    tokens = tuple(
        sorted(
            {
                match.group(0)
                for match in _TOKEN_PATTERN.finditer(value.lower())
            }
        )
    )

    return tokens


class LexicalIndex(Protocol):
    """Backend-neutral lexical index contract."""

    def metadata(self) -> IndexMetadata:
        """Return index metadata."""

    def statistics(self) -> IndexStatistics:
        """Return aggregate index statistics."""

    def entries(self) -> tuple[IndexEntry, ...]:
        """Return all index entries in deterministic order."""

    def lookup(self, query_terms: tuple[str, ...]) -> tuple[IndexEntry, ...]:
        """Return entries matching all query terms."""

    def is_stale(self, source_digest: str) -> bool:
        """Return True when the index is stale relative to source knowledge."""


class InMemoryLexicalIndex:
    """Reference in-memory lexical index implementation."""

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
                    f"Duplicate lexical entry_id '{entry.entry_id}'."
                )

            seen_entry_ids.add(entry.entry_id)

        self._entries = sorted_entries
        self._term_to_entry_ids: dict[str, tuple[str, ...]] = {}

        for entry in self._entries:
            for term in entry.terms:
                existing = self._term_to_entry_ids.get(term, ())
                if entry.entry_id not in existing:
                    self._term_to_entry_ids[term] = tuple(
                        sorted((*existing, entry.entry_id))
                    )

        self._entries_by_id = {
            entry.entry_id: entry for entry in self._entries
        }

    def metadata(self) -> IndexMetadata:
        return IndexMetadata(
            index_id=self._index_id,
            source_digest=self._source_digest,
            entry_count=len(self._entries),
            lifecycle_state=IndexLifecycleState.VALID,
        )

    def statistics(self) -> IndexStatistics:
        target_ids = {entry.target_id for entry in self._entries}

        return IndexStatistics(
            entry_count=len(self._entries),
            unique_term_count=len(self._term_to_entry_ids),
            target_count=len(target_ids),
        )

    def entries(self) -> tuple[IndexEntry, ...]:
        return self._entries

    def lookup(self, query_terms: tuple[str, ...]) -> tuple[IndexEntry, ...]:
        if not query_terms:
            return ()

        normalized_terms = tuple(
            sorted(
                {
                    term.strip().lower()
                    for term in query_terms
                    if term.strip()
                }
            )
        )

        if not normalized_terms:
            return ()

        candidate_sets = [
            set(self._term_to_entry_ids.get(term, ()))
            for term in normalized_terms
        ]

        matching_ids = sorted(set.intersection(*candidate_sets))

        return tuple(
            self._entries_by_id[entry_id]
            for entry_id in matching_ids
            if entry_id in self._entries_by_id
        )

    def is_stale(self, source_digest: str) -> bool:
        return self._source_digest != source_digest.strip()


def build_lexical_index_from_store(
    store: GraphStore,
    *,
    index_id: str = "lexical-default",
) -> InMemoryLexicalIndex:
    """Build a lexical index from graph store node searchable properties."""

    record = store.snapshot()
    source_digest = canonical_graph_record_digest(record)
    entries: list[IndexEntry] = []

    for node in sorted(record.nodes, key=lambda item: item.node_id):
        searchable_values: list[str] = [node.node_type]

        for key in (
            "extracted_label",
            "canonical_name",
            "document_id",
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
                entry_id=f"lex:{node.node_id}",
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

    return InMemoryLexicalIndex(
        index_id=index_id,
        source_digest=source_digest,
        entries=entries,
    )


def require_fresh_lexical_index(
    index: LexicalIndex,
    source_digest: str,
) -> None:
    """Raise when the lexical index is missing or stale."""

    if index.metadata().lifecycle_state is IndexLifecycleState.MISSING:
        raise IndexNotFoundError("Lexical index is missing.")

    if index.is_stale(source_digest):
        raise IndexStaleError(
            "Lexical index is stale relative to authoritative knowledge."
        )
