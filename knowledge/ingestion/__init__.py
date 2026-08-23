"""
COSMOS Knowledge Foundation — document ingestion adapter contracts.
"""

from __future__ import annotations

from knowledge.ingestion.base import (
    IngestionAdapter,
    supports_source_format,
    validate_adapter_request,
)
from knowledge.ingestion.exceptions import (
    IngestionAdapterError,
    IngestionError,
    IngestionValidationError,
)
from knowledge.ingestion.models import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    IngestionStage,
    NormalizedDocumentFormat,
    SourceFormat,
)

__all__ = (
    "IngestionAdapter",
    "IngestionAdapterError",
    "IngestionArtifactRef",
    "IngestionError",
    "IngestionRequest",
    "IngestionResult",
    "IngestionStage",
    "IngestionValidationError",
    "NormalizedDocumentFormat",
    "SourceFormat",
    "supports_source_format",
    "validate_adapter_request",
)
