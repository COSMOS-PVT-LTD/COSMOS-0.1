"""Hybrid search for KG-039 (W8)."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.exceptions import IndexStaleError
from knowledge.indexing.w7.bundle import W7IndexBundle
from knowledge.indexing.w7.vector import deterministic_reference_vector
from knowledge.search.contracts import (
    RetrievalMode,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.exceptions import SearchValidationError
from knowledge.search.w8.graph_search import GraphSearchEngine
from knowledge.search.w8.keyword import KeywordSearchEngine
from knowledge.search.w8.semantic import SemanticVectorSearchEngine

__all__ = (
    "HybridComponentWeights",
    "HybridSearchEngine",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class HybridComponentWeights:
    """Explicit hybrid fusion weights."""

    keyword: float = 0.40
    semantic: float = 0.35
    graph: float = 0.25

    def __post_init__(self) -> None:
        for field_name, value in (
            ("keyword", self.keyword),
            ("semantic", self.semantic),
            ("graph", self.graph),
        ):
            if value < 0.0:
                raise SearchValidationError(
                    f"hybrid weight '{field_name}' must be non-negative.",
                )

        total = self.keyword + self.semantic + self.graph

        if total <= 0.0:
            raise SearchValidationError(
                "hybrid weights must sum to a positive value.",
            )


def _result_metadata(result: SearchResult) -> dict[str, object]:
    return {
        "document_id": result.document_id,
        "lifecycle_state": result.lifecycle_state,
        "target_type": result.target_type,
    }


class HybridSearchEngine:
    """Controlled fusion of keyword, semantic, and graph retrieval."""

    def __init__(
        self,
        index_bundle: W7IndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
        *,
        weights: HybridComponentWeights | None = None,
        use_keyword: bool = True,
        use_semantic: bool = True,
        use_graph: bool = True,
    ) -> None:
        self._index_bundle = index_bundle
        self._graph_query = graph_query
        self._store = store
        self._weights = weights or HybridComponentWeights()
        self._use_keyword = use_keyword
        self._use_semantic = use_semantic
        self._use_graph = use_graph
        self._source_digest = index_bundle.source_digest

        self._keyword_engine = KeywordSearchEngine(
            index_bundle.lexical_index,
            source_digest=self._source_digest,
            store=store,
        )
        self._semantic_engine = SemanticVectorSearchEngine(
            index_bundle.vector_index,
            source_digest=self._source_digest,
            store=store,
        )
        self._graph_engine = GraphSearchEngine(
            index_bundle.graph_index,
            graph_query,
            source_digest=self._source_digest,
            store=store,
        )

    def search(self, query: SearchQuery) -> SearchResultPage:
        """Execute hybrid search with explicit component fusion."""

        if not isinstance(query, SearchQuery):
            raise SearchValidationError(
                "query must be a SearchQuery instance.",
            )

        if self._index_bundle.is_stale(self._store):
            raise IndexStaleError(
                "Hybrid search indexes are stale relative to authoritative graph knowledge.",
            )

        active_weights = self._active_weights()
        component_results: dict[str, dict[str, SearchResult]] = {
            "keyword": {},
            "semantic": {},
            "graph": {},
        }

        if self._use_keyword:
            keyword_page = self._keyword_engine.search(query)

            for result in keyword_page.results:
                component_results["keyword"][result.target_id] = result

        if self._use_semantic:
            query_vector = deterministic_reference_vector(
                target_id=query.text,
                dimension=self._index_bundle.vector_index.dimension(),
            )
            semantic_page = self._semantic_engine.search(
                query,
                query_vector=query_vector,
            )

            for result in semantic_page.results:
                component_results["semantic"][result.target_id] = result

        if self._use_graph:
            graph_page = self._graph_engine.search(query)

            for result in graph_page.results:
                component_results["graph"][result.target_id] = result

        all_target_ids = sorted(
            set(component_results["keyword"])
            | set(component_results["semantic"])
            | set(component_results["graph"]),
        )

        fused: list[SearchResult] = []

        for target_id in all_target_ids:
            keyword_score = (
                component_results["keyword"][target_id].score
                if target_id in component_results["keyword"]
                else 0.0
            )
            semantic_score = (
                component_results["semantic"][target_id].score
                if target_id in component_results["semantic"]
                else 0.0
            )
            graph_score = (
                component_results["graph"][target_id].score
                if target_id in component_results["graph"]
                else 0.0
            )

            final_score = min(
                1.0,
                (active_weights.get("keyword", 0.0) * keyword_score)
                + (active_weights.get("semantic", 0.0) * semantic_score)
                + (active_weights.get("graph", 0.0) * graph_score),
            )

            source = (
                component_results["keyword"].get(target_id)
                or component_results["semantic"].get(target_id)
                or component_results["graph"].get(target_id)
            )

            if source is None:
                continue

            contributors = tuple(
                component
                for component, bucket in component_results.items()
                if target_id in bucket
            )

            fused.append(
                SearchResult(
                    target_id=source.target_id,
                    target_type=source.target_type,
                    score=final_score,
                    document_id=source.document_id,
                    lifecycle_state=source.lifecycle_state,
                    retrieval_mode=RetrievalMode.HYBRID,
                    ranking_reason=(
                        "hybrid_fusion:"
                        + ",".join(contributors)
                    ),
                ),
            )

        ordered = tuple(
            sorted(
                fused,
                key=lambda item: (-item.score, item.target_id),
            ),
        )
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

    def _active_weights(self) -> dict[str, float]:
        components: dict[str, float] = {}

        if self._use_keyword:
            components["keyword"] = self._weights.keyword

        if self._use_semantic:
            components["semantic"] = self._weights.semantic

        if self._use_graph:
            components["graph"] = self._weights.graph

        total = sum(components.values())

        if total <= 0.0:
            raise SearchValidationError(
                "At least one hybrid retrieval component must be active.",
            )

        return {
            component: weight / total
            for component, weight in components.items()
        }
