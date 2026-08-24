"""Source-faithful equation candidate contracts. Not approved knowledge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.extraction.equation import CandidateEquationExtraction, ExtractionConfidence
from knowledge.graph.contracts import ProvenanceReference
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import ExtractionProvenance, ReviewStatus, SourceProvenanceRecord
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = (
    "EquationClassification",
    "EquationValidationState",
    "SourceEquationCandidate",
    "ValidatedEquationCandidate",
    "VariableBinding",
)


class EquationValidationState(Enum):
    NOT_VALIDATED = "NOT_VALIDATED"
    VALIDATION_IN_PROGRESS = "VALIDATION_IN_PROGRESS"
    VALID = "VALID"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    NON_AUTHORITATIVE = "NON_AUTHORITATIVE"
    AMBIGUOUS = "AMBIGUOUS"
    EXTRACTION_UNAVAILABLE = "EXTRACTION_UNAVAILABLE"


class EquationClassification(Enum):
    UNKNOWN = "UNKNOWN"
    PHYSICAL_LAW = "PHYSICAL_LAW"
    CORRELATION = "CORRELATION"
    EMPIRICAL = "EMPIRICAL"
    IDENTITY = "IDENTITY"
    MATERIAL_RELATION = "MATERIAL_RELATION"


@dataclass(frozen=True, slots=True, kw_only=True)
class VariableBinding:
    symbol: str
    definition: str | None
    unit: str | None
    ambiguous: bool = False
    ambiguity_note: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceEquationCandidate:
    candidate_id: str
    source_id: str
    document_id: str
    page_number: int | None
    section_id: str | None
    region_id: str | None
    label: str | None
    raw_text: str
    latex: str | None
    mathml: str | None
    image_reference: str | None
    variables: tuple[VariableBinding, ...]
    constants: tuple[str, ...]
    units: tuple[str, ...]
    assumptions: tuple[str, ...]
    applicability: str | None
    confidence: float
    provenance: ProvenanceTrace
    validation_state: EquationValidationState = EquationValidationState.NOT_VALIDATED
    classification: EquationClassification = EquationClassification.UNKNOWN
    version: str = "1.0.0"
    ocr_text: str | None = None

    def to_extraction(self) -> CandidateEquationExtraction:
        if not self.raw_text.strip():
            raise ValueError("Cannot convert an empty equation candidate.")
        return CandidateEquationExtraction(
            extraction_id=self.candidate_id,
            document_id=self.document_id,
            raw_representation=self.raw_text,
            latex_representation=self.latex,
            provenance=SourceProvenanceRecord(
                anchor=ProvenanceReference(
                    source_id=self.source_id or None,
                    document_id=self.document_id or None,
                    page=self.page_number,
                    section=self.section_id,
                    equation=self.label,
                ),
                extraction=ExtractionProvenance(
                    extractor_tool="cosmos-equation-detector",
                    extractor_version="1.0.0",
                    review_status=ReviewStatus.CANDIDATE,
                ),
            ),
            confidence_band=_band(self.confidence),
            confidence_score=self.confidence,
            lifecycle_state=GraphLifecycleState.EXTRACTED,
            variable_symbols=tuple(item.symbol for item in self.variables),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatedEquationCandidate:
    candidate: SourceEquationCandidate
    state: EquationValidationState
    schema_ok: bool
    source_ok: bool
    unit_state: EquationValidationState
    dimension_state: EquationValidationState
    semantic_state: EquationValidationState
    applicability_state: EquationValidationState
    reasons: tuple[str, ...]
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    extraction_state: EquationValidationState = EquationValidationState.NOT_VALIDATED
    syntax_state: EquationValidationState = EquationValidationState.UNKNOWN
    contradiction_state: EquationValidationState = EquationValidationState.UNKNOWN


def _band(score: float) -> ExtractionConfidence:
    if score >= 0.75:
        return ExtractionConfidence.HIGH
    if score >= 0.4:
        return ExtractionConfidence.MEDIUM
    return ExtractionConfidence.LOW
