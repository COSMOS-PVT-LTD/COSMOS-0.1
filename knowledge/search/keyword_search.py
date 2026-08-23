"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-002).

Frozen Part-3 keyword search surface delegating to W8 KeywordSearchEngine.
"""

from __future__ import annotations

from knowledge.graph.repository import GraphStore
from knowledge.indexing.lexical import LexicalIndex
from knowledge.search.contracts import SearchQuery, SearchResultPage
from knowledge.search.w8.keyword import KeywordSearchEngine

__all__ = ("KeywordSearch",)


class KeywordSearch:
    """Legacy keyword search facade over the canonical W8 keyword engine."""

    def __init__(
        self,
        engine: KeywordSearchEngine,
    ) -> None:
        self._engine = engine

    @classmethod
    def from_lexical_index(
        cls,
        lexical_index: LexicalIndex,
        *,
        source_digest: str,
        store: GraphStore | None = None,
    ) -> KeywordSearch:
        return cls(
            KeywordSearchEngine(
                lexical_index,
                source_digest=source_digest,
                store=store,
            ),
        )

    def search(self, query: SearchQuery) -> SearchResultPage:
        return self._engine.search(query)

    @property
    def canonical_engine(self) -> KeywordSearchEngine:
        return self._engine
