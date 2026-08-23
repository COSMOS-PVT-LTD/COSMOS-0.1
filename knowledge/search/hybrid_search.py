"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-002).

Frozen Part-3 hybrid search surface delegating to W8 HybridSearchEngine.
"""

from __future__ import annotations

from knowledge.graph.query import GraphQueryService
from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7.bundle import W7IndexBundle
from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.w8.hybrid import HybridComponentWeights, HybridSearchEngine

__all__ = ("HybridSearch",)


class HybridSearch:
    """Legacy hybrid search facade over the canonical W8 hybrid engine."""

    def __init__(self, engine: HybridSearchEngine) -> None:
        self._engine = engine

    @classmethod
    def from_w7_bundle(
        cls,
        bundle: W7IndexBundle,
        graph_query: GraphQueryService,
        store: GraphStore,
        *,
        weights: HybridComponentWeights | None = None,
    ) -> HybridSearch:
        return cls(
            HybridSearchEngine(
                bundle,
                graph_query,
                store,
                weights=weights,
            ),
        )

    def search(self, query: SearchQuery) -> SearchResultPage:
        return self._engine.search(query)

    @property
    def canonical_engine(self) -> HybridSearchEngine:
        return self._engine
