"""Public exports for knowledge.search."""

from __future__ import annotations

from knowledge.search.contracts import (
    NO_VERIFIED_RESULT,
    RetrievalMode,
    SearchFilter,
    SearchOrder,
    SearchQuery,
    SearchResult,
    SearchResultPage,
)
from knowledge.search.engine import KnowledgeSearchEngine
from knowledge.search.exceptions import (
    ContextAssemblyError,
    RankingError,
    RetrievalError,
    SearchError,
    SearchValidationError,
)

__all__ = (
    "ContextAssemblyError",
    "KnowledgeSearchEngine",
    "NO_VERIFIED_RESULT",
    "RankingError",
    "RetrievalError",
    "RetrievalMode",
    "SearchError",
    "SearchFilter",
    "SearchOrder",
    "SearchQuery",
    "SearchResult",
    "SearchResultPage",
    "SearchValidationError",
)
