"""Public exports for knowledge.indexing.w7 (KG-BLOCK-010 W7)."""

from __future__ import annotations

from knowledge.indexing.w7.bundle import W7IndexBuilder, W7IndexBundle
from knowledge.indexing.w7.graph_index import (
    GraphIndex,
    GraphIndexAdjacency,
    InMemoryGraphIndex,
    build_graph_index_from_store,
    require_fresh_graph_index,
)
from knowledge.indexing.w7.vector import (
    InMemoryVectorIndex,
    VectorIndex,
    VectorRecord,
    build_reference_vector_index_from_store,
    build_vector_index_from_records,
    cosine_similarity,
    deterministic_reference_vector,
    require_fresh_vector_index,
    validate_vector_components,
)

__all__ = (
    "GraphIndex",
    "GraphIndexAdjacency",
    "InMemoryGraphIndex",
    "InMemoryVectorIndex",
    "VectorIndex",
    "VectorRecord",
    "W7IndexBuilder",
    "W7IndexBundle",
    "build_graph_index_from_store",
    "build_reference_vector_index_from_store",
    "build_vector_index_from_records",
    "cosine_similarity",
    "deterministic_reference_vector",
    "require_fresh_graph_index",
    "require_fresh_vector_index",
    "validate_vector_components",
)
