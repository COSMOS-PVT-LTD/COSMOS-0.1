"""
COSMOS Knowledge Foundation

Module:
    knowledge.indexing.builder

Purpose:
    Index build and rebuild orchestration over authoritative graph knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.lexical import (
    InMemoryLexicalIndex,
    build_lexical_index_from_store,
)
from knowledge.indexing.models import IndexLifecycleState
from knowledge.indexing.semantic import (
    InMemorySemanticIndex,
    build_semantic_index_from_store,
)

__all__ = (
    "KnowledgeIndexBundle",
    "KnowledgeIndexBuilder",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class KnowledgeIndexBundle:
    """Materialized lexical and semantic indexes for a graph snapshot."""

    source_digest: str
    lexical_index: InMemoryLexicalIndex
    semantic_index: InMemorySemanticIndex
    lifecycle_state: IndexLifecycleState = IndexLifecycleState.VALID

    def is_stale(self, store: GraphStore) -> bool:
        """Return True when indexes are stale relative to the graph store."""

        current_digest = canonical_graph_record_digest(store.snapshot())

        return (
            self.source_digest != current_digest
            or self.lexical_index.is_stale(current_digest)
            or self.semantic_index.is_stale(current_digest)
        )


class KnowledgeIndexBuilder:
    """Build and rebuild deterministic knowledge indexes from graph stores."""

    def build(self, store: GraphStore) -> KnowledgeIndexBundle:
        """Build lexical and semantic indexes from the current graph state."""

        lexical_index = build_lexical_index_from_store(store)
        semantic_index = build_semantic_index_from_store(store)

        return KnowledgeIndexBundle(
            source_digest=lexical_index.metadata().source_digest,
            lexical_index=lexical_index,
            semantic_index=semantic_index,
        )

    def rebuild(self, store: GraphStore) -> KnowledgeIndexBundle:
        """Rebuild indexes from authoritative graph knowledge."""

        return self.build(store)
