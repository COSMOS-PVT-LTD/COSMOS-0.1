"""
COSMOS Knowledge Foundation

Module:
    knowledge.extraction.equation

Purpose:
    Equation extraction candidate contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.extraction.exceptions import ExtractionValidationError

__all__ = (
    "CandidateEquationExtraction",
    "ExtractionConfidence",
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


class ExtractionConfidence(Enum):
    """Discrete extraction confidence bands."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEquationExtraction:
    """
    Candidate equation extracted from a source document.

    This is not an approved canonical Equation model instance.
    """

    extraction_id: str
    document_id: str
    raw_representation: str
    latex_representation: str | None = None
    provenance: SourceProvenanceRecord
    confidence_band: ExtractionConfidence = ExtractionConfidence.LOW
    confidence_score: float = 0.0
    lifecycle_state: GraphLifecycleState = GraphLifecycleState.EXTRACTED
    variable_symbols: tuple[str, ...] = ()

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
            "raw_representation",
            _validate_non_empty_string(
                "raw_representation",
                self.raw_representation,
            ),
        )
        object.__setattr__(
            self,
            "latex_representation",
            _validate_optional_non_empty_string(
                "latex_representation",
                self.latex_representation,
            ),
        )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise ExtractionValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        if not isinstance(self.confidence_band, ExtractionConfidence):
            raise ExtractionValidationError(
                "confidence_band must be an ExtractionConfidence value."
            )

        object.__setattr__(
            self,
            "confidence_score",
            _validate_confidence_score(self.confidence_score),
        )

        if not isinstance(self.lifecycle_state, GraphLifecycleState):
            raise ExtractionValidationError(
                "lifecycle_state must be a GraphLifecycleState value."
            )

        if self.lifecycle_state is GraphLifecycleState.APPROVED:
            raise ExtractionValidationError(
                "Extracted equations must not be created in APPROVED state."
            )

        if not isinstance(self.variable_symbols, tuple):
            raise ExtractionValidationError(
                "variable_symbols must be a tuple."
            )

        for index, symbol in enumerate(self.variable_symbols):
            if not isinstance(symbol, str) or not symbol.strip():
                raise ExtractionValidationError(
                    f"variable_symbols[{index}] must be a non-blank string."
                )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "extraction_id": self.extraction_id,
            "document_id": self.document_id,
            "raw_representation": self.raw_representation,
            "provenance": self.provenance.to_mapping(),
            "confidence_band": self.confidence_band.value,
            "confidence_score": self.confidence_score,
            "lifecycle_state": self.lifecycle_state.value,
            "variable_symbols": list(self.variable_symbols),
        }

        if self.latex_representation is not None:
            payload["latex_representation"] = self.latex_representation

        return payload


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)
