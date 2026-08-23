"""W4 extraction models and result envelope for KG-BLOCK-007."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.extraction.claim import (
    CandidateClaimExtraction,
    CandidateRelationshipExtraction,
)
from knowledge.extraction.entity import CandidateEntityExtraction
from knowledge.extraction.equation import CandidateEquationExtraction, ExtractionConfidence
from knowledge.extraction.exceptions import ExtractionValidationError
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.parsers.w3.models import StructuredParsedDocument

__all__ = (
    "CandidateQuantityExtraction",
    "ExtractionContext",
    "ExtractionResult",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ExtractionValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ExtractionValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionContext:
    """
    Bounded extraction input combining W3 output with normalized source text.

    StructuredParsedDocument does not embed full source text; normalized_content
    supplies prose for candidate extraction while W3 elements provide structure.
    """

    parsed_document: StructuredParsedDocument
    normalized_content: str

    def __post_init__(self) -> None:
        if not isinstance(self.parsed_document, StructuredParsedDocument):
            raise ExtractionValidationError(
                "parsed_document must be a StructuredParsedDocument instance."
            )

        if not isinstance(self.normalized_content, str):
            raise ExtractionValidationError("normalized_content must be a string.")


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateQuantityExtraction:
    """Extraction-layer quantity candidate — not a canonical Quantity model."""

    extraction_id: str
    document_id: str
    raw_text: str
    provenance: SourceProvenanceRecord
    numeric_value: float | None = None
    unit_token: str | None = None
    dimensionless: bool = False
    ambiguous: bool = False
    confidence_band: ExtractionConfidence = ExtractionConfidence.LOW
    confidence_score: float = 0.5

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
            "raw_text",
            _validate_non_empty_string("raw_text", self.raw_text),
        )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise ExtractionValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        if not isinstance(self.confidence_band, ExtractionConfidence):
            raise ExtractionValidationError(
                "confidence_band must be an ExtractionConfidence value."
            )

        if not isinstance(self.dimensionless, bool):
            raise ExtractionValidationError("dimensionless must be a boolean.")

        if not isinstance(self.ambiguous, bool):
            raise ExtractionValidationError("ambiguous must be a boolean.")

        score = float(self.confidence_score)

        if score < 0.0 or score > 1.0:
            raise ExtractionValidationError(
                "confidence_score must be between 0.0 and 1.0."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ambiguous": self.ambiguous,
            "confidence_band": self.confidence_band.value,
            "confidence_score": self.confidence_score,
            "dimensionless": self.dimensionless,
            "document_id": self.document_id,
            "extraction_id": self.extraction_id,
            "provenance": self.provenance.to_mapping(),
            "raw_text": self.raw_text,
        }

        if self.numeric_value is not None:
            payload["numeric_value"] = self.numeric_value
        if self.unit_token is not None:
            payload["unit_token"] = self.unit_token

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionResult:
    """Complete W4 extraction output envelope."""

    document_id: str
    source_id: str
    artifact_id: str
    extractor_name: str
    extractor_version: str
    entities: tuple[CandidateEntityExtraction, ...] = ()
    quantities: tuple[CandidateQuantityExtraction, ...] = ()
    equations: tuple[CandidateEquationExtraction, ...] = ()
    claims: tuple[CandidateClaimExtraction, ...] = ()
    relationships: tuple[CandidateRelationshipExtraction, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )
        object.__setattr__(
            self,
            "extractor_name",
            _validate_non_empty_string("extractor_name", self.extractor_name),
        )
        object.__setattr__(
            self,
            "extractor_version",
            _validate_non_empty_string("extractor_version", self.extractor_version),
        )

        for field_name, items in (
            ("entities", self.entities),
            ("quantities", self.quantities),
            ("equations", self.equations),
            ("claims", self.claims),
            ("relationships", self.relationships),
        ):
            if not isinstance(items, tuple):
                raise ExtractionValidationError(f"{field_name} must be a tuple.")

    def to_mapping(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "claims": [item.to_mapping() for item in self.claims],
            "document_id": self.document_id,
            "entities": [item.to_mapping() for item in self.entities],
            "equations": [item.to_mapping() for item in self.equations],
            "extractor_name": self.extractor_name,
            "extractor_version": self.extractor_version,
            "quantities": [item.to_mapping() for item in self.quantities],
            "relationships": [item.to_mapping() for item in self.relationships],
            "source_id": self.source_id,
        }
