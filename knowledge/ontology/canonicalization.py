"""Canonicalization of W4 extraction candidates for KG-024."""

from __future__ import annotations

from knowledge.extraction.entity import CandidateEntityExtraction
from knowledge.extraction.w4.models import ExtractionResult
from knowledge.ontology.exceptions import CanonicalizationError, OntologyValidationError
from knowledge.ontology.identity import deterministic_ontology_id
from knowledge.ontology.models import (
    CanonicalizationMapping,
    CanonicalizationResult,
    CanonicalizationStatus,
    NormalizedTerm,
)
from knowledge.ontology.registry import OntologyRegistry, OntologyTermNotFoundError
from knowledge.ontology.validation import normalize_observed_term

__all__ = (
    "canonicalize_entity_candidate",
    "canonicalize_extraction_result",
    "resolve_canonical_term_id",
)


def resolve_canonical_term_id(
    registry: OntologyRegistry,
    observed_label: str,
) -> str | None:
    """
    Resolve an observed label to a canonical ontology term identifier.

    Uses exact canonical-name match and controlled alias lookup only.
    Does not perform fuzzy or semantic inference.
    """

    normalized = normalize_observed_term(observed_label)
    normalized_fold = normalized.casefold()
    canonical_matches: list[str] = []

    for term in registry.list_terms():
        term_normalized = normalize_observed_term(term.canonical_name)

        if (
            term_normalized == normalized
            or term_normalized.casefold() == normalized_fold
        ):
            canonical_matches.append(term.term_id)

    if len(canonical_matches) > 1:
        return None

    if len(canonical_matches) == 1:
        return canonical_matches[0]

    try:
        return registry.resolve_alias(normalized).term_id
    except OntologyTermNotFoundError:
        pass

    try:
        return registry.resolve_alias(observed_label.strip()).term_id
    except OntologyTermNotFoundError:
        return None


def canonicalize_entity_candidate(
    candidate: CandidateEntityExtraction,
    registry: OntologyRegistry,
) -> CanonicalizationMapping:
    """Canonicalize a single W4 entity extraction candidate."""

    if not isinstance(candidate, CandidateEntityExtraction):
        raise OntologyValidationError(
            "candidate must be a CandidateEntityExtraction instance."
        )

    if not isinstance(registry, OntologyRegistry):
        raise OntologyValidationError(
            "registry must be an OntologyRegistry instance."
        )

    try:
        normalized_label = normalize_observed_term(candidate.extracted_label)
    except ValueError as exc:
        raise CanonicalizationError(
            "Entity candidate label is not canonicalizable."
        ) from exc

    normalized_term = NormalizedTerm(
        raw_label=candidate.extracted_label,
        normalized_label=normalized_label,
    )
    canonical_term_id = resolve_canonical_term_id(
        registry,
        candidate.extracted_label,
    )
    status = (
        CanonicalizationStatus.RESOLVED
        if canonical_term_id is not None
        else CanonicalizationStatus.UNRESOLVED
    )
    mapping_id = deterministic_ontology_id(
        "can",
        candidate.document_id,
        candidate.extraction_id,
        normalized_label,
    )

    return CanonicalizationMapping(
        mapping_id=mapping_id,
        extraction_id=candidate.extraction_id,
        observed_label=candidate.extracted_label,
        normalized_term=normalized_term,
        canonical_term_id=canonical_term_id,
        status=status,
        provenance=candidate.provenance,
        confidence_score=0.9 if status is CanonicalizationStatus.RESOLVED else 0.3,
    )


def canonicalize_extraction_result(
    extraction_result: ExtractionResult,
    registry: OntologyRegistry,
) -> CanonicalizationResult:
    """Canonicalize all entity candidates from a W4 extraction result."""

    if not isinstance(extraction_result, ExtractionResult):
        raise OntologyValidationError(
            "extraction_result must be an ExtractionResult instance."
        )

    mappings = tuple(
        canonicalize_entity_candidate(entity, registry)
        for entity in sorted(
            extraction_result.entities,
            key=lambda item: item.extraction_id,
        )
    )

    return CanonicalizationResult(
        document_id=extraction_result.document_id,
        mappings=mappings,
    )
