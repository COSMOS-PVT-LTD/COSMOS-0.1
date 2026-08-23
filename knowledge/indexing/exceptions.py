"""
COSMOS Knowledge Foundation

Module:
    knowledge.indexing.exceptions

Purpose:
    Indexing-layer exceptions.
"""

from __future__ import annotations

from knowledge.graph.exceptions import GraphError, GraphValidationError

__all__ = (
    "IndexError",
    "IndexNotFoundError",
    "IndexStaleError",
    "IndexValidationError",
)


class IndexError(GraphError):
    """Base class for indexing-layer failures."""


class IndexValidationError(GraphValidationError, IndexError):
    """Indicate that an indexing contract failed validation."""


class IndexNotFoundError(IndexError):
    """Indicate that a required index is missing."""


class IndexStaleError(IndexError):
    """Indicate that an index is stale relative to authoritative knowledge."""
