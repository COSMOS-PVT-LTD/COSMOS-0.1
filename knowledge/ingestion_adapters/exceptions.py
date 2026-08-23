"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion_adapters.exceptions

Purpose:
    Format adapter exceptions for KG-BLOCK-005 W2 ingestion.
"""

from __future__ import annotations

from knowledge.ingestion.exceptions import IngestionAdapterError

__all__ = (
    "AdapterExecutionError",
    "AdapterValidationError",
    "RepositoryBoundaryError",
    "UnsupportedContentError",
)


class AdapterValidationError(IngestionAdapterError):
    """Indicate that adapter input failed validation."""


class AdapterExecutionError(IngestionAdapterError):
    """Indicate that adapter execution failed."""


class UnsupportedContentError(AdapterExecutionError):
    """Indicate that artifact content cannot be ingested by the adapter."""


class RepositoryBoundaryError(AdapterExecutionError):
    """Indicate that repository ingestion violated configured boundaries."""
