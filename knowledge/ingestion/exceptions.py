"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion.exceptions

Purpose:
    Ingestion-layer exceptions for document adapter contracts.
"""

from __future__ import annotations

from knowledge.graph.exceptions import GraphError, GraphValidationError

__all__ = (
    "IngestionAdapterError",
    "IngestionError",
    "IngestionValidationError",
)


class IngestionError(GraphError):
    """Base class for ingestion-layer failures."""


class IngestionValidationError(GraphValidationError):
    """Indicate that an ingestion contract failed validation."""


class IngestionAdapterError(IngestionError):
    """Indicate that an ingestion adapter operation failed."""
