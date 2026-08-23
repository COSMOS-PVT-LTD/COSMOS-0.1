"""Public exports for knowledge.indexing."""

from __future__ import annotations

from knowledge.indexing.builder import KnowledgeIndexBuilder, KnowledgeIndexBundle
from knowledge.indexing.exceptions import (
    IndexError,
    IndexNotFoundError,
    IndexStaleError,
    IndexValidationError,
)
from knowledge.indexing.lexical import (
    InMemoryLexicalIndex,
    LexicalIndex,
    build_lexical_index_from_store,
    require_fresh_lexical_index,
    tokenize_text,
)
from knowledge.indexing.models import (
    IndexEntry,
    IndexLifecycleState,
    IndexMetadata,
    IndexStatistics,
)
from knowledge.indexing.semantic import (
    InMemorySemanticIndex,
    SemanticIndex,
    build_semantic_index_from_store,
    require_fresh_semantic_index,
    semantic_similarity_score,
)

__all__ = (
    "IndexEntry",
    "IndexError",
    "IndexLifecycleState",
    "IndexMetadata",
    "IndexNotFoundError",
    "IndexStaleError",
    "IndexStatistics",
    "IndexValidationError",
    "InMemoryLexicalIndex",
    "InMemorySemanticIndex",
    "KnowledgeIndexBuilder",
    "KnowledgeIndexBundle",
    "LexicalIndex",
    "SemanticIndex",
    "build_lexical_index_from_store",
    "build_semantic_index_from_store",
    "require_fresh_lexical_index",
    "require_fresh_semantic_index",
    "semantic_similarity_score",
    "tokenize_text",
)
