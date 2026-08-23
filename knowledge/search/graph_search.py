"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-002).

Frozen Part-3 graph search surface delegating to W8 GraphSearchEngine.
"""

from __future__ import annotations

from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7.graph_index import GraphIndex
from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.w8.graph_search import GraphSearchEngine

__all__ = ("GraphSearch",)


class GraphSearch:
    """Legacy graph search facade over the canonical W8 graph engine."""

    def __init__(self, engine: GraphSearchEngine) -> None:
        self._engine = engine

    @classmethod
    def from_graph_index(
        cls,
        graph_index: GraphIndex,
        graph_query: GraphQueryService,
        *,
        source_digest: str,
        store: GraphStore | None = None,
        max_traversal_depth: int = 2,
    ) -> GraphSearch:
        return cls(
            GraphSearchEngine(
                graph_index,
                graph_query,
                source_digest=source_digest,
                store=store,
                max_traversal_depth=max_traversal_depth,
            ),
        )

    def search(self, query: SearchQuery) -> SearchResultPage:
        return self._engine.search(query)

    @property
    def canonical_engine(self) -> GraphSearchEngine:
        return self._engine
