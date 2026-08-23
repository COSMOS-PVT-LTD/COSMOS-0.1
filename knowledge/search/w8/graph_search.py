"""Graph search for KG-038 (W8)."""

from __future__ import annotations

from knowledge.graph.exceptions import GraphQueryError
from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.lexical import tokenize_text
from knowledge.indexing.w7.graph_index import GraphIndex, require_fresh_graph_index
from knowledge.search.contracts import (
    RetrievalMode,
    SearchOrder,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.exceptions import RetrievalError, SearchValidationError

__all__ = (
    "GraphSearchEngine",
)


def _result_metadata(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "lifecycle_state": result.lifecycle_state,
        "target_type": result.target_type,
    }


class GraphSearchEngine:
    """Graph-aware retrieval using graph index and query abstractions."""

    def __init__(
        self,
        graph_index: GraphIndex,
        graph_query: GraphQueryService,
        *,
        source_digest: str,
        store: GraphStore | None = None,
        max_traversal_depth: int = 2,
    ) -> None:
        self._graph_index = graph_index
        self._graph_query = graph_query
        self._source_digest = source_digest
        self._store = store
        self._max_traversal_depth = max_traversal_depth

    def search(self, query: SearchQuery) -> SearchResultPage:
        """Execute graph-aware search with bounded traversal relevance."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance.",
            )

        self._require_fresh_indexes()
        query_terms = tokenize_text(query.text)

        if not query_terms:
            return SearchResultPage(
                results=(),
                total_count=0,
                limit=query.limit,
                offset=query.offset,
            )

        query_term_set = set(query_terms)
        results: list[SearchResult] = []

        for adjacency in self._graph_index.adjacency():
            searchable_values = [
                adjacency.node_id,
                adjacency.node_type,
            ]

            if adjacency.document_id:
                searchable_values.append(adjacency.document_id)

            try:
                node = self._graph_query.get_entity(adjacency.node_id)

                for key in (
                    "extracted_label",
                    "canonical_name",
                ):
                    value = node.properties.get(key)

                    if isinstance(value, str) and value.strip():
                        searchable_values.append(value)
            except GraphQueryError:
                pass

            node_terms = {
                token
                for value in searchable_values
                for token in tokenize_text(value)
            }
            matching_terms = query_term_set & node_terms

            if not matching_terms:
                continue

            try:
                traversal = self._graph_query.traverse(
                    adjacency.node_id,
                    self._max_traversal_depth,
                )
            except GraphQueryError as exc:
                raise RetrievalError(
                    "Graph traversal failed during graph search.",
                ) from exc

            property_score = len(matching_terms) / len(query_term_set | node_terms)
            traversal_bonus = min(
                1.0,
                0.1 + (0.05 * len(traversal.nodes)),
            )
            score = min(1.0, (0.7 * property_score) + (0.3 * traversal_bonus))

            try:
                metadata = self._graph_query.provenance_metadata(adjacency.node_id)
            except GraphQueryError:
                metadata = {
                    "document_id": adjacency.document_id,
                    "lifecycle_state": adjacency.lifecycle_state,
                    "target_type": adjacency.node_type,
                }

            candidate = SearchResult(
                target_id=adjacency.node_id,
                target_type=adjacency.node_type,
                score=score,
                document_id=str(metadata.get("document_id"))
                if metadata.get("document_id") is not None
                else adjacency.document_id,
                lifecycle_state=str(metadata.get("lifecycle_state"))
                if metadata.get("lifecycle_state") is not None
                else adjacency.lifecycle_state,
                retrieval_mode=RetrievalMode.STRUCTURED,
                ranking_reason="graph_index_traversal_match",
            )

            if query.filters.matches(_result_metadata(candidate)):
                results.append(candidate)

        ordered = self._order_results(tuple(results), query.order)
        page = ordered[query.offset : query.offset + query.limit]

        return SearchResultPage(
            results=page,
            total_count=len(ordered),
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
        require_fresh_graph_index(self._graph_index, self._source_digest)

        if self._store is not None:
            live_digest = canonical_graph_record_digest(self._store.snapshot())

            if live_digest != self._source_digest:
                raise IndexStaleError(
                    "Graph search indexes are stale relative to authoritative "
                    "graph knowledge.",
                )
