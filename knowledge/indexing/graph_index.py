"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-003).

Frozen Part-3 graph index surface — alias to canonical W7 InMemoryGraphIndex.
"""

from __future__ import annotations

from knowledge.indexing.w7.graph_index import (
    InMemoryGraphIndex,
    build_graph_index_from_store,
)

__all__ = ("GraphIndex", "build_graph_index_from_store")

GraphIndex = InMemoryGraphIndex
