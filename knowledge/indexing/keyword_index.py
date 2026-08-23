"""
COMPATIBILITY FACADE (KG-BLOCK-013 Phase B — COMPAT-003).

Frozen Part-3 keyword index surface — alias to canonical InMemoryLexicalIndex.
"""

from __future__ import annotations

from knowledge.indexing.lexical import InMemoryLexicalIndex, build_lexical_index_from_store

__all__ = ("KeywordIndex", "build_keyword_index_from_store")

KeywordIndex = InMemoryLexicalIndex
build_keyword_index_from_store = build_lexical_index_from_store
