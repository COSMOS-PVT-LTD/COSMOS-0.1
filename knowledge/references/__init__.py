"""Rights-aware reference ingestion — additive, never treats UNKNOWN as cleared."""

from __future__ import annotations

from knowledge.references.document_class import DocumentClass
from knowledge.references.rights import (
    INGESTIBLE_RIGHTS,
    RightsRecord,
    RightsStatus,
    rights_allow_ingestion,
)
from knowledge.references.ingestion import ReferenceIngestRequest, validate_reference_ingest

__all__ = (
    "INGESTIBLE_RIGHTS",
    "DocumentClass",
    "ReferenceIngestRequest",
    "RightsRecord",
    "RightsStatus",
    "rights_allow_ingestion",
    "validate_reference_ingest",
)
