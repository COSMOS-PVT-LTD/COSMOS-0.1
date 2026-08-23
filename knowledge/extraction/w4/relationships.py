"""Relationship extraction (NEW KG-023)."""

from __future__ import annotations

from knowledge.extraction.claim import CandidateRelationshipExtraction
from knowledge.extraction.entity import CandidateEntityExtraction
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.extraction.w4.models import CandidateQuantityExtraction, ExtractionContext
from knowledge.extraction.w4.provenance import to_source_provenance
from knowledge.graph.lifecycle import GraphLifecycleState

__all__ = (
    "extract_relationships",
)


def _section_key(provenance: object) -> str | None:
    anchor = getattr(provenance, "anchor", None)

    if anchor is None:
        return None

    return getattr(anchor, "section", None)


def extract_relationships(
    context: ExtractionContext,
    *,
    entities: tuple[CandidateEntityExtraction, ...],
    quantities: tuple[CandidateQuantityExtraction, ...],
    equation_ids: tuple[str, ...],
    claim_ids: tuple[str, ...],
) -> tuple[CandidateRelationshipExtraction, ...]:
    """Extract candidate relationships between co-located extraction artifacts."""

    document = context.parsed_document
    relationships: list[CandidateRelationshipExtraction] = []
    entity_by_section: dict[str, str] = {}

    for entity in entities:
        section = _section_key(entity.provenance)

        if section is not None:
            entity_by_section[section] = entity.extraction_id

    for quantity in quantities:
        section = _section_key(quantity.provenance)

        if section is None or section not in entity_by_section:
            continue

        entity_id = entity_by_section[section]
        relationship_id = deterministic_extraction_id(
            "rel",
            document.document_id,
            "quantity-describes-entity",
            quantity.extraction_id,
            entity_id,
        )

        relationships.append(
            CandidateRelationshipExtraction(
                relationship_id=relationship_id,
                document_id=document.document_id,
                relationship_type="quantity_DESCRIBES_entity",
                source_extraction_id=quantity.extraction_id,
                target_extraction_id=entity_id,
                provenance=quantity.provenance,
                lifecycle_state=GraphLifecycleState.CANDIDATE,
                confidence_score=0.6,
            ),
        )

    if claim_ids and entities:
        claim_id = claim_ids[0]
        entity_id = entities[0].extraction_id
        paragraph_prov = document.paragraphs[0].provenance if document.paragraphs else None

        if paragraph_prov is not None:
            relationships.append(
                CandidateRelationshipExtraction(
                    relationship_id=deterministic_extraction_id(
                        "rel",
                        document.document_id,
                        "claim-about-entity",
                        claim_id,
                        entity_id,
                    ),
                    document_id=document.document_id,
                    relationship_type="claim_ABOUT_entity",
                    source_extraction_id=claim_id,
                    target_extraction_id=entity_id,
                    provenance=to_source_provenance(paragraph_prov),
                    lifecycle_state=GraphLifecycleState.CANDIDATE,
                    confidence_score=0.5,
                ),
            )

    if equation_ids and entities:
        equation_id = equation_ids[0]
        entity_id = entities[0].extraction_id
        equation = document.equations[0] if document.equations else None

        if equation is not None:
            relationships.append(
                CandidateRelationshipExtraction(
                    relationship_id=deterministic_extraction_id(
                        "rel",
                        document.document_id,
                        "equation-describes-entity",
                        equation_id,
                        entity_id,
                    ),
                    document_id=document.document_id,
                    relationship_type="equation_DESCRIBES_entity",
                    source_extraction_id=equation_id,
                    target_extraction_id=entity_id,
                    provenance=to_source_provenance(
                        equation.provenance,
                        equation_id=equation.equation_id,
                    ),
                    lifecycle_state=GraphLifecycleState.CANDIDATE,
                    confidence_score=0.55,
                ),
            )

    deduped = {relationship.relationship_id: relationship for relationship in relationships}

    return tuple(sorted(deduped.values(), key=lambda item: item.relationship_id))
