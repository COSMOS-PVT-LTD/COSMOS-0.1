"""W4 extraction pipeline orchestrating KG-019 → KG-023."""

from __future__ import annotations

from knowledge.extraction.w4.claims import extract_claims
from knowledge.extraction.w4.entities import extract_entities
from knowledge.extraction.w4.equations import extract_equation_candidates
from knowledge.extraction.w4.models import ExtractionContext, ExtractionResult
from knowledge.extraction.w4.provenance import EXTRACTOR_NAME, EXTRACTOR_VERSION
from knowledge.extraction.w4.quantities import extract_quantities
from knowledge.extraction.w4.relationships import extract_relationships

__all__ = (
    "W4ExtractionPipeline",
    "extract_document",
)


class W4ExtractionPipeline:
    """Production W4 extractor consuming W3 structured parsed documents."""

    @property
    def extractor_name(self) -> str:
        return EXTRACTOR_NAME

    @property
    def extractor_version(self) -> str:
        return EXTRACTOR_VERSION

    def extract(self, context: ExtractionContext) -> ExtractionResult:
        return extract_document(context)


def extract_document(context: ExtractionContext) -> ExtractionResult:
    """Run the complete W4 extraction pipeline on a parsed document."""

    document = context.parsed_document

    entities = extract_entities(context)
    quantities = extract_quantities(context)
    equations = extract_equation_candidates(context)
    claims = extract_claims(context)
    relationships = extract_relationships(
        context,
        entities=entities,
        quantities=quantities,
        equation_ids=tuple(item.extraction_id for item in equations),
        claim_ids=tuple(item.claim_id for item in claims),
    )

    return ExtractionResult(
        document_id=document.document_id,
        source_id=document.source_id,
        artifact_id=document.artifact_id,
        extractor_name=EXTRACTOR_NAME,
        extractor_version=EXTRACTOR_VERSION,
        entities=entities,
        quantities=quantities,
        equations=equations,
        claims=claims,
        relationships=relationships,
    )
