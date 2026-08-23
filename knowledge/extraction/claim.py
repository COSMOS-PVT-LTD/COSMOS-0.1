"""
COSMOS Knowledge Foundation

Module:
    knowledge.extraction.claim

Purpose:
    Relationship and claim extraction candidate contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.extraction.exceptions import ExtractionValidationError

__all__ = (
    "CandidateClaimExtraction",
    "CandidateRelationshipExtraction",
    "ClaimConflictVisibility",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ExtractionValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ExtractionValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_confidence_score(value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ExtractionValidationError(
            "confidence_score must be a number between 0.0 and 1.0."
        )

    score = float(value)

    if score < 0.0 or score > 1.0:
        raise ExtractionValidationError(
            "confidence_score must be between 0.0 and 1.0."
        )

    return score


class ClaimConflictVisibility(Enum):
    """Visibility state for potentially conflicting claims."""

    NONE = "NONE"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    CONFIRMED_CONFLICT = "CONFIRMED_CONFLICT"


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateClaimExtraction:
    """Candidate engineering claim extracted from a source."""

    claim_id: str
    document_id: str
    claim_text: str
    provenance: SourceProvenanceRecord
    lifecycle_state: GraphLifecycleState = GraphLifecycleState.CANDIDATE
    conflict_visibility: ClaimConflictVisibility = ClaimConflictVisibility.NONE
    confidence_score: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "claim_id",
            _validate_non_empty_string("claim_id", self.claim_id),
        )
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "claim_text",
            _validate_non_empty_string("claim_text", self.claim_text),
        )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise ExtractionValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        if not isinstance(self.lifecycle_state, GraphLifecycleState):
            raise ExtractionValidationError(
                "lifecycle_state must be a GraphLifecycleState value."
            )

        if not isinstance(self.conflict_visibility, ClaimConflictVisibility):
            raise ExtractionValidationError(
                "conflict_visibility must be a ClaimConflictVisibility value."
            )

        object.__setattr__(
            self,
            "confidence_score",
            _validate_confidence_score(self.confidence_score),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "claim_id": self.claim_id,
            "document_id": self.document_id,
            "claim_text": self.claim_text,
            "provenance": self.provenance.to_mapping(),
            "lifecycle_state": self.lifecycle_state.value,
            "conflict_visibility": self.conflict_visibility.value,
            "confidence_score": self.confidence_score,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateRelationshipExtraction:
    """Candidate relationship between extracted entities or claims."""

    relationship_id: str
    document_id: str
    relationship_type: str
    source_extraction_id: str
    target_extraction_id: str
    provenance: SourceProvenanceRecord
    lifecycle_state: GraphLifecycleState = GraphLifecycleState.CANDIDATE
    confidence_score: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "relationship_id",
            _validate_non_empty_string(
                "relationship_id",
                self.relationship_id,
            ),
        )
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "relationship_type",
            _validate_non_empty_string(
                "relationship_type",
                self.relationship_type,
            ),
        )
        object.__setattr__(
            self,
            "source_extraction_id",
            _validate_non_empty_string(
                "source_extraction_id",
                self.source_extraction_id,
            ),
        )
        object.__setattr__(
            self,
            "target_extraction_id",
            _validate_non_empty_string(
                "target_extraction_id",
                self.target_extraction_id,
            ),
        )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise ExtractionValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        if not isinstance(self.lifecycle_state, GraphLifecycleState):
            raise ExtractionValidationError(
                "lifecycle_state must be a GraphLifecycleState value."
            )

        object.__setattr__(
            self,
            "confidence_score",
            _validate_confidence_score(self.confidence_score),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "relationship_id": self.relationship_id,
            "document_id": self.document_id,
            "relationship_type": self.relationship_type,
            "source_extraction_id": self.source_extraction_id,
            "target_extraction_id": self.target_extraction_id,
            "provenance": self.provenance.to_mapping(),
            "lifecycle_state": self.lifecycle_state.value,
            "confidence_score": self.confidence_score,
        }
