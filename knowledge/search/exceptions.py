"""
COSMOS Knowledge Foundation

Module:
    knowledge.search.exceptions

Purpose:
    Search and retrieval layer exceptions.
"""

from __future__ import annotations

from knowledge.indexing.exceptions import IndexError
from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "ContextAssemblyError",
    "RankingError",
    "RetrievalError",
    "SearchError",
    "SearchValidationError",
)


class SearchError(IndexError):
    """Base class for search-layer failures."""


class SearchValidationError(GraphValidationError, SearchError):
    """Indicate that a search contract failed validation."""


class RetrievalError(SearchError):
    """Indicate that a retrieval operation failed."""


class RankingError(SearchError):
    """Indicate that ranking or evidence assembly failed."""


class ContextAssemblyError(SearchError):
    """Indicate that reasoning-context assembly failed."""
