"""Keyword search for KG-036 (W8)."""

from __future__ import annotations

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.lexical import LexicalIndex, require_fresh_lexical_index, tokenize_text
from knowledge.search.contracts import (
    RetrievalMode,
    SearchOrder,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.exceptions import SearchValidationError

__all__ = (
    "KeywordSearchEngine",
)


def _result_metadata(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "lifecycle_state": result.lifecycle_state,
        "target_type": result.target_type,
    }


class KeywordSearchEngine:
    """Deterministic keyword retrieval over a lexical index."""

    def __init__(
        self,
        lexical_index: LexicalIndex,
        *,
        source_digest: str,
        store: GraphStore | None = None,
    ) -> None:
        self._lexical_index = lexical_index
        self._source_digest = source_digest
        self._store = store

    def search(self, query: SearchQuery) -> SearchResultPage:
        """Execute keyword search over the lexical index."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance.",
            )

        self._require_fresh_indexes()
        query_terms = tokenize_text(query.text)
        matches = self._lexical_index.lookup(query_terms)

        results = tuple(
            SearchResult(
                target_id=entry.target_id,
                target_type=entry.target_type,
                score=1.0,
                document_id=entry.document_id,
                lifecycle_state=entry.lifecycle_state,
                retrieval_mode=RetrievalMode.LEXICAL,
                ranking_reason="keyword_exact_token_match",
            )
            for entry in matches
        )

        ordered = self._order_results(results, query.order)
        filtered = tuple(
            result
            for result in ordered
            if query.filters.matches(_result_metadata(result))
        )
        page = filtered[query.offset : query.offset + query.limit]

        return SearchResultPage(
            results=page,
            total_count=len(filtered),
            limit=query.limit,
            offset=query.offset,
        )

    def _order_results(
        self,
        results: tuple[SearchResult, ...],
        order: SearchOrder,
    ) -> tuple[SearchResult, ...]:
        if order is SearchOrder.TARGET_ID_ASC:
            return tuple(sorted(results, key=lambda item: item.target_id))

        return tuple(
            sorted(
                results,
                key=lambda item: (-item.score, item.target_id),
            ),
        )

    def _require_fresh_indexes(self) -> None:
        require_fresh_lexical_index(
            self._lexical_index,
            self._source_digest,
        )

        if self._store is not None:
            live_digest = canonical_graph_record_digest(self._store.snapshot())

            if live_digest != self._source_digest:
                raise IndexStaleError(
                    "Keyword search indexes are stale relative to authoritative "
                    "graph knowledge.",
                )
