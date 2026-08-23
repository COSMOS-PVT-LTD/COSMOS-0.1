"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-002).

Frozen Part-3 search engine surface delegating to KnowledgeSearchEngine.
"""

from __future__ import annotations

from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.builder import KnowledgeIndexBundle
from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.engine import KnowledgeSearchEngine

__all__ = ("SearchEngine", "KnowledgeSearchEngine")


class SearchEngine(KnowledgeSearchEngine):
    """Legacy search engine alias delegating to the canonical KnowledgeSearchEngine."""

    def __init__(
        self,
        index_bundle: KnowledgeIndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
    ) -> None:
        super().__init__(index_bundle, graph_query, store)

    def search(self, query: SearchQuery) -> SearchResultPage:
        return super().search(query)
