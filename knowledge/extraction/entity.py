"""
COSMOS Knowledge Foundation

Module:
    knowledge.extraction.entity

Purpose:
    Engineering entity extraction candidate contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.extraction.exceptions import ExtractionValidationError

__all__ = (
    "CandidateEntityExtraction",
    "ExtractedEntityKind",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ExtractionValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ExtractionValidationError(f"{field_name} must not be blank.")

    return cleaned


class ExtractedEntityKind(Enum):
    """Kinds of engineering entities that may be extracted as candidates."""

    MATERIAL = "MATERIAL"
    COMPONENT = "COMPONENT"
    SUBSYSTEM = "SUBSYSTEM"
    QUANTITY = "QUANTITY"
    VARIABLE = "VARIABLE"
    CONSTANT = "CONSTANT"
    DOMAIN = "DOMAIN"
    PROCESS = "PROCESS"
    EXPERIMENT = "EXPERIMENT"


_ENTITY_KIND_TO_CANONICAL: dict[ExtractedEntityKind, CanonicalEntityType] = {
    ExtractedEntityKind.MATERIAL: CanonicalEntityType.MATERIAL,
    ExtractedEntityKind.COMPONENT: CanonicalEntityType.OTHER,
    ExtractedEntityKind.SUBSYSTEM: CanonicalEntityType.SUBSYSTEM,
    ExtractedEntityKind.QUANTITY: CanonicalEntityType.QUANTITY,
    ExtractedEntityKind.VARIABLE: CanonicalEntityType.VARIABLE,
    ExtractedEntityKind.CONSTANT: CanonicalEntityType.CONSTANT,
    ExtractedEntityKind.DOMAIN: CanonicalEntityType.ENGINEERING_DOMAIN,
    ExtractedEntityKind.PROCESS: CanonicalEntityType.OTHER,
    ExtractedEntityKind.EXPERIMENT: CanonicalEntityType.OTHER,
}


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEntityExtraction:
    """
    Candidate reference to a canonical engineering entity extracted from a source.

    Does not instantiate canonical domain models.
    """

    extraction_id: str
    document_id: str
    extracted_label: str
    entity_kind: ExtractedEntityKind
    canonical_entity_type: CanonicalEntityType
    provenance: SourceProvenanceRecord
    lifecycle_state: GraphLifecycleState = GraphLifecycleState.CANDIDATE

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "extraction_id",
            _validate_non_empty_string("extraction_id", self.extraction_id),
        )
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "extracted_label",
            _validate_non_empty_string(
                "extracted_label",
                self.extracted_label,
            ),
        )

        if not isinstance(self.entity_kind, ExtractedEntityKind):
            raise ExtractionValidationError(
                "entity_kind must be an ExtractedEntityKind value."
            )

        if not isinstance(self.canonical_entity_type, CanonicalEntityType):
            raise ExtractionValidationError(
                "canonical_entity_type must be a CanonicalEntityType value."
            )

        expected_type = _ENTITY_KIND_TO_CANONICAL[self.entity_kind]

        if self.canonical_entity_type != expected_type:
            raise ExtractionValidationError(
                "canonical_entity_type must match entity_kind mapping."
            )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise ExtractionValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        if not isinstance(self.lifecycle_state, GraphLifecycleState):
            raise ExtractionValidationError(
                "lifecycle_state must be a GraphLifecycleState value."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "extraction_id": self.extraction_id,
            "document_id": self.document_id,
            "extracted_label": self.extracted_label,
            "entity_kind": self.entity_kind.value,
            "canonical_entity_type": self.canonical_entity_type.value,
            "provenance": self.provenance.to_mapping(),
            "lifecycle_state": self.lifecycle_state.value,
        }
