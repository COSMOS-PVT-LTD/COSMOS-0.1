"""W7 index bundle orchestration for KG-BLOCK-010."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.builder import KnowledgeIndexBuilder, KnowledgeIndexBundle
from knowledge.indexing.models import IndexLifecycleState
from knowledge.indexing.w7.graph_index import (
    InMemoryGraphIndex,
    build_graph_index_from_store,
)
from knowledge.indexing.w7.vector import (
    InMemoryVectorIndex,
    build_reference_vector_index_from_store,
)

__all__ = (
    "W7IndexBuilder",
    "W7IndexBundle",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class W7IndexBundle:
    """Materialized W7 indexes for a graph snapshot."""

    source_digest: str
    lexical_semantic_bundle: KnowledgeIndexBundle
    vector_index: InMemoryVectorIndex
    graph_index: InMemoryGraphIndex
    lifecycle_state: IndexLifecycleState = IndexLifecycleState.VALID

    @property
    def lexical_index(self):
        return self.lexical_semantic_bundle.lexical_index

    @property
    def semantic_index(self):
        return self.lexical_semantic_bundle.semantic_index

    def is_stale(self, store: GraphStore) -> bool:
        """Return True when any W7 index is stale relative to the graph store."""

        current_digest = canonical_graph_record_digest(store.snapshot())

        return (
            self.source_digest != current_digest
            or self.lexical_semantic_bundle.is_stale(store)
            or self.vector_index.is_stale(current_digest)
            or self.graph_index.is_stale(current_digest)
        )


class W7IndexBuilder:
    """Build and rebuild deterministic W7 indexes from graph stores."""

    def __init__(
        self,
        *,
        vector_dimension: int = 8,
    ) -> None:
        self._vector_dimension = vector_dimension
        self._base_builder = KnowledgeIndexBuilder()

    def build(self, store: GraphStore) -> W7IndexBundle:
        """Build lexical, semantic, vector, and graph indexes."""

        lexical_semantic_bundle = self._base_builder.build(store)
        vector_index = build_reference_vector_index_from_store(
            store,
            dimension=self._vector_dimension,
        )
        graph_index = build_graph_index_from_store(store)

        return W7IndexBundle(
            source_digest=lexical_semantic_bundle.source_digest,
            lexical_semantic_bundle=lexical_semantic_bundle,
            vector_index=vector_index,
            graph_index=graph_index,
        )

    def rebuild(self, store: GraphStore) -> W7IndexBundle:
        """Rebuild all W7 indexes from authoritative graph knowledge."""

        return self.build(store)
