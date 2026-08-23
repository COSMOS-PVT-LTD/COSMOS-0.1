"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-003).

Frozen Part-3 semantic index surface — alias to canonical InMemorySemanticIndex.
"""

from __future__ import annotations

from knowledge.indexing.semantic import (
    InMemorySemanticIndex,
    build_semantic_index_from_store,
)

__all__ = ("SemanticIndex", "build_semantic_index_from_store")

SemanticIndex = InMemorySemanticIndex
