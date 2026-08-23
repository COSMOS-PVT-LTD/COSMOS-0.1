"""Semantic vector search for KG-037 (W8)."""

from __future__ import annotations

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.w7.vector import VectorIndex, require_fresh_vector_index
from knowledge.search.contracts import (
    RetrievalMode,
    SearchOrder,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.exceptions import SearchValidationError

__all__ = (
    "SemanticVectorSearchEngine",
)


def _result_metadata(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "lifecycle_state": result.lifecycle_state,
        "target_type": result.target_type,
    }


class SemanticVectorSearchEngine:
    """Deterministic semantic retrieval using caller-supplied query vectors."""

    def __init__(
        self,
        vector_index: VectorIndex,
        *,
        source_digest: str,
        store: GraphStore | None = None,
    ) -> None:
        self._vector_index = vector_index
        self._source_digest = source_digest
        self._store = store

    def search(
        self,
        query: SearchQuery,
        *,
        query_vector: tuple[float, ...],
    ) -> SearchResultPage:
        """Execute semantic search using an explicit query vector."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance.",
            )

        self._require_fresh_indexes()

        ranked = self._vector_index.similarity(
            query_vector,
            limit=query.limit + query.offset,
        )

        results = tuple(
            SearchResult(
                target_id=record.target_id,
                target_type=record.target_type,
                score=max(0.0, min(1.0, score)),
                document_id=record.document_id,
                lifecycle_state=record.lifecycle_state,
                retrieval_mode=RetrievalMode.SEMANTIC,
                ranking_reason="semantic_vector_cosine_similarity",
            )
            for record, score in ranked
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
        require_fresh_vector_index(self._vector_index, self._source_digest)

        if self._store is not None:
            live_digest = canonical_graph_record_digest(self._store.snapshot())

            if live_digest != self._source_digest:
                raise IndexStaleError(
                    "Semantic search indexes are stale relative to authoritative "
                    "graph knowledge.",
                )
