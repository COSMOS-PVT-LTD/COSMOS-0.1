"""
KG-BLOCK-007 W4 extraction package.

Production extraction engines producing frozen candidate contracts.
Does not modify knowledge.extraction contract modules.
"""

from __future__ import annotations

from knowledge.extraction.w4.claims import extract_claims
from knowledge.extraction.w4.entities import extract_entities
from knowledge.extraction.w4.equations import extract_equation_candidates
from knowledge.extraction.w4.exceptions import (
    ExtractionContentError,
    ExtractionInputError,
    ExtractionQuantityError,
    ExtractionRelationshipError,
    UnsupportedExtractionError,
)
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.extraction.w4.models import (
    CandidateQuantityExtraction,
    ExtractionContext,
    ExtractionResult,
)
from knowledge.extraction.w4.pipeline import W4ExtractionPipeline, extract_document
from knowledge.extraction.w4.provenance import EXTRACTOR_NAME, EXTRACTOR_VERSION, to_source_provenance
from knowledge.extraction.w4.quantities import extract_quantities
from knowledge.extraction.w4.registry import (
    ExtractionOrchestrator,
    ExtractionRegistry,
    StructuredDocumentExtractor,
    build_default_extraction_registry,
)
from knowledge.extraction.w4.relationships import extract_relationships

__all__ = (
    "EXTRACTOR_NAME",
    "EXTRACTOR_VERSION",
    "CandidateQuantityExtraction",
    "ExtractionContentError",
    "ExtractionContext",
    "ExtractionInputError",
    "ExtractionOrchestrator",
    "ExtractionQuantityError",
    "ExtractionRegistry",
    "ExtractionRelationshipError",
    "ExtractionResult",
    "StructuredDocumentExtractor",
    "UnsupportedExtractionError",
    "W4ExtractionPipeline",
    "build_default_extraction_registry",
    "deterministic_extraction_id",
    "extract_claims",
    "extract_document",
    "extract_entities",
    "extract_equation_candidates",
    "extract_quantities",
    "extract_relationships",
    "to_source_provenance",
)
