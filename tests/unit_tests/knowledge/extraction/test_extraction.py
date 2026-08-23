"""Unit tests for knowledge.extraction contracts."""

from __future__ import annotations

import pytest

from knowledge.extraction import (
    CandidateClaimExtraction,
    CandidateEntityExtraction,
    CandidateEquationExtraction,
    CandidateRelationshipExtraction,
    ClaimConflictVisibility,
    ExtractedEntityKind,
    ExtractionConfidence,
    ExtractionValidationError,
)
from knowledge.graph import GraphLifecycleState
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.graph import ProvenanceReference


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=3),
    )


def test_candidate_equation_extraction_rejects_approved_state() -> None:
    """Extracted equations must not be auto-approved."""

    with pytest.raises(ExtractionValidationError):
        CandidateEquationExtraction(
            extraction_id="EQ-EXT-001",
            document_id="DOC-001",
            raw_representation="P = F / A",
            provenance=_provenance(),
            lifecycle_state=GraphLifecycleState.APPROVED,
        )


def test_candidate_equation_extraction_valid_construction() -> None:
    """Equation extraction candidates must retain provenance and confidence."""

    candidate = CandidateEquationExtraction(
        extraction_id="EQ-EXT-001",
        document_id="DOC-001",
        raw_representation="P = F / A",
        latex_representation="P = \\frac{F}{A}",
        provenance=_provenance(),
        confidence_band=ExtractionConfidence.MEDIUM,
        confidence_score=0.6,
        variable_symbols=("P", "F", "A"),
    )

    assert candidate.lifecycle_state is GraphLifecycleState.EXTRACTED
    assert candidate.confidence_band is ExtractionConfidence.MEDIUM


def test_candidate_entity_extraction_requires_kind_type_alignment() -> None:
    """Entity kind and canonical entity type must remain aligned."""

    with pytest.raises(ExtractionValidationError):
        CandidateEntityExtraction(
            extraction_id="ENT-001",
            document_id="DOC-001",
            extracted_label="LOX",
            entity_kind=ExtractedEntityKind.MATERIAL,
            canonical_entity_type=CanonicalEntityType.QUANTITY,
            provenance=_provenance(),
        )


def test_candidate_entity_extraction_valid_construction() -> None:
    """Entity extraction candidates must remain non-authoritative."""

    candidate = CandidateEntityExtraction(
        extraction_id="ENT-001",
        document_id="DOC-001",
        extracted_label="Liquid Oxygen",
        entity_kind=ExtractedEntityKind.MATERIAL,
        canonical_entity_type=CanonicalEntityType.MATERIAL,
        provenance=_provenance(),
    )

    assert candidate.lifecycle_state is GraphLifecycleState.CANDIDATE


def test_candidate_claim_extraction_preserves_conflict_visibility() -> None:
    """Claims must preserve conflict visibility metadata."""

    claim = CandidateClaimExtraction(
        claim_id="CLM-001",
        document_id="DOC-001",
        claim_text="Chamber pressure exceeds design limit.",
        provenance=_provenance(),
        conflict_visibility=ClaimConflictVisibility.POTENTIAL_CONFLICT,
        confidence_score=0.4,
    )

    assert claim.conflict_visibility is ClaimConflictVisibility.POTENTIAL_CONFLICT


def test_candidate_relationship_extraction_valid_construction() -> None:
    """Relationship extraction candidates must retain endpoint references."""

    relationship = CandidateRelationshipExtraction(
        relationship_id="REL-EXT-001",
        document_id="DOC-001",
        relationship_type="references",
        source_extraction_id="ENT-001",
        target_extraction_id="EQ-EXT-001",
        provenance=_provenance(),
    )

    assert relationship.lifecycle_state is GraphLifecycleState.CANDIDATE
