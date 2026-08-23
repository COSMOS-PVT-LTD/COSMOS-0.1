"""
COSMOS Knowledge Foundation

Module:
    knowledge.search.engine

Purpose:
    Backend-neutral search engine over knowledge indexes and graph queries.
"""

from __future__ import annotations

from knowledge.graph.exceptions import GraphQueryError
from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.builder import KnowledgeIndexBundle
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.lexical import require_fresh_lexical_index, tokenize_text
from knowledge.indexing.semantic import require_fresh_semantic_index
from knowledge.search.contracts import (
    NO_VERIFIED_RESULT,
    RetrievalMode,
    SearchOrder,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.exceptions import RetrievalError, SearchValidationError

__all__ = (
    "KnowledgeSearchEngine",
)


def _result_metadata(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "lifecycle_state": result.lifecycle_state,
        "target_type": result.target_type,
    }


class KnowledgeSearchEngine:
    """Execute bounded search queries over indexed graph knowledge."""

    def __init__(
        self,
        index_bundle: KnowledgeIndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
    ) -> None:
        self._index_bundle = index_bundle
        self._graph_query = graph_query
        self._store = store
        self._source_digest = index_bundle.source_digest

    def search(self, query: SearchQuery) -> SearchResultPage:
        """Execute a bounded search query."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance."
            )

        require_fresh_lexical_index(
            self._index_bundle.lexical_index,
            self._source_digest,
        )
        require_fresh_semantic_index(
            self._index_bundle.semantic_index,
            self._source_digest,
        )

        live_digest = canonical_graph_record_digest(self._store.snapshot())

        if live_digest != self._source_digest:
            raise IndexStaleError(
                "Search indexes are stale relative to authoritative "
                "graph knowledge."
            )

        query_terms = tokenize_text(query.text)

        if query.mode is RetrievalMode.LEXICAL:
            results = self._lexical_results(query_terms, query)
        elif query.mode is RetrievalMode.SEMANTIC:
            results = self._semantic_results(query_terms, query)
        elif query.mode is RetrievalMode.STRUCTURED:
            results = self._structured_results(query)
        elif query.mode is RetrievalMode.HYBRID:
            results = self._hybrid_results(query_terms, query)
        else:
            raise SearchValidationError("Unsupported retrieval mode.")

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

    def _lexical_results(
        self,
        query_terms: tuple[str, ...],
        query: SearchQuery,
    ) -> tuple[SearchResult, ...]:
        matches = self._index_bundle.lexical_index.lookup(query_terms)

        return tuple(
            SearchResult(
                target_id=entry.target_id,
                target_type=entry.target_type,
                score=1.0,
                document_id=entry.document_id,
                lifecycle_state=entry.lifecycle_state,
                retrieval_mode=RetrievalMode.LEXICAL,
                ranking_reason="lexical_term_match",
            )
            for entry in matches
        )

    def _semantic_results(
        self,
        query_terms: tuple[str, ...],
        query: SearchQuery,
    ) -> tuple[SearchResult, ...]:
        ranked = self._index_bundle.semantic_index.similarity(
            query_terms,
            limit=query.limit + query.offset,
        )

        return tuple(
            SearchResult(
                target_id=entry.target_id,
                target_type=entry.target_type,
                score=score,
                document_id=entry.document_id,
                lifecycle_state=entry.lifecycle_state,
                retrieval_mode=RetrievalMode.SEMANTIC,
                ranking_reason="semantic_term_overlap",
            )
            for entry, score in ranked
        )

    def _structured_results(
        self,
        query: SearchQuery,
    ) -> tuple[SearchResult, ...]:
        query_terms = tokenize_text(query.text)

        if not query_terms:
            return ()

        results: list[SearchResult] = []
        query_term_set = set(query_terms)

        for node in self._store.list_nodes():
            searchable_values: list[str] = [node.node_type, node.node_id]

            for key in (
                "extracted_label",
                "canonical_name",
                "document_id",
            ):
                value = node.properties.get(key)

                if isinstance(value, str) and value.strip():
                    searchable_values.append(value)

            node_terms = {
                token
                for value in searchable_values
                for token in tokenize_text(value)
            }
            matching_terms = query_term_set & node_terms

            if not matching_terms:
                continue

            union_terms = query_term_set | node_terms
            score = len(matching_terms) / len(union_terms)

            try:
                metadata = self._graph_query.provenance_metadata(node.node_id)
            except GraphQueryError:
                metadata = {
                    "document_id": node.properties.get("document_id"),
                    "lifecycle_state": node.properties.get("lifecycle_state"),
                    "target_type": node.node_type,
                }

            candidate = SearchResult(
                target_id=node.node_id,
                target_type=node.node_type,
                score=score,
                document_id=str(metadata.get("document_id"))
                if metadata.get("document_id") is not None
                else None,
                lifecycle_state=str(metadata.get("lifecycle_state"))
                if metadata.get("lifecycle_state") is not None
                else None,
                retrieval_mode=RetrievalMode.STRUCTURED,
                ranking_reason="structured_property_match",
            )

            if query.filters.matches(_result_metadata(candidate)):
                results.append(candidate)

        return tuple(results)

    def _hybrid_results(
        self,
        query_terms: tuple[str, ...],
        query: SearchQuery,
    ) -> tuple[SearchResult, ...]:
        lexical = {
            result.target_id: result
            for result in self._lexical_results(query_terms, query)
        }
        semantic = {
            result.target_id: result
            for result in self._semantic_results(query_terms, query)
        }

        graph_relevance: dict[str, float] = {}

        for result in lexical.values():
            try:
                neighbors = self._graph_query.neighbors(result.target_id)
            except GraphQueryError as exc:
                raise RetrievalError(
                    "Graph relevance lookup failed during hybrid retrieval."
                ) from exc

            graph_relevance[result.target_id] = min(
                1.0,
                0.2 + (0.1 * len(neighbors)),
            )

        combined_scores: dict[str, SearchResult] = {}

        for target_id in sorted(set(lexical) | set(semantic)):
            lexical_result = lexical.get(target_id)
            semantic_result = semantic.get(target_id)

            lexical_score = lexical_result.score if lexical_result else 0.0
            semantic_score = semantic_result.score if semantic_result else 0.0
            graph_score = graph_relevance.get(target_id, 0.0)

            provenance_bonus = 0.0
            lifecycle_state = (
                lexical_result.lifecycle_state
                if lexical_result is not None
                else semantic_result.lifecycle_state
                if semantic_result is not None
                else None
            )

            if lifecycle_state in {"CANDIDATE", "EXTRACTED"}:
                provenance_bonus = 0.05

            score = min(
                1.0,
                (0.45 * lexical_score)
                + (0.35 * semantic_score)
                + (0.15 * graph_score)
                + provenance_bonus,
            )

            source = lexical_result or semantic_result

            if source is None:
                continue

            combined_scores[target_id] = SearchResult(
                target_id=source.target_id,
                target_type=source.target_type,
                score=score,
                document_id=source.document_id,
                lifecycle_state=source.lifecycle_state,
                retrieval_mode=RetrievalMode.HYBRID,
                ranking_reason=(
                    "hybrid_lexical_semantic_graph_provenance"
                ),
            )

        if not combined_scores:
            return ()

        return tuple(
            combined_scores[target_id]
            for target_id in sorted(combined_scores)
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
            )
        )

    def current_source_digest(self) -> str:
        """Return the authoritative source digest used by this engine."""

        return self._source_digest

    def refresh_source_digest(self) -> str:
        """Recompute source digest from the current graph store."""

        return canonical_graph_record_digest(self._store.snapshot())

    def no_verified_result(self) -> str:
        """Return the explicit no-verified-result sentinel."""

        return NO_VERIFIED_RESULT
