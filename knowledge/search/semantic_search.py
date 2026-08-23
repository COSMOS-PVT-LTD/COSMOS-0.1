"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-002).

Frozen Part-3 semantic search surface delegating to W8 SemanticVectorSearchEngine.
"""

from __future__ import annotations

from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7.vector import VectorIndex
from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.w8.semantic import SemanticVectorSearchEngine

__all__ = ("SemanticSearch",)


class SemanticSearch:
    """Legacy semantic search facade over the canonical W8 semantic engine."""

    def __init__(self, engine: SemanticVectorSearchEngine) -> None:
        self._engine = engine

    @classmethod
    def from_vector_index(
        cls,
        vector_index: VectorIndex,
        *,
        source_digest: str,
        store: GraphStore | None = None,
    ) -> SemanticSearch:
        return cls(
            SemanticVectorSearchEngine(
                vector_index,
                source_digest=source_digest,
                store=store,
            ),
        )

    def search(
        self,
        query: SearchQuery,
        *,
        query_vector: tuple[float, ...],
    ) -> SearchResultPage:
        return self._engine.search(query, query_vector=query_vector)

    @property
    def canonical_engine(self) -> SemanticVectorSearchEngine:
        return self._engine
