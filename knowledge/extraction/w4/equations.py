"""Equation extraction from W3 parsed equations (NEW KG-021)."""

from __future__ import annotations

from knowledge.extraction.equation import (
    CandidateEquationExtraction,
    ExtractionConfidence,
)
from knowledge.extraction.w4.exceptions import ExtractionInputError
from knowledge.extraction.w4.identity import deterministic_extraction_id
from knowledge.extraction.w4.models import ExtractionContext
from knowledge.extraction.w4.provenance import to_source_provenance
from knowledge.graph.lifecycle import GraphLifecycleState

__all__ = (
    "extract_equation_candidates",
)

_FORBIDDEN_TOKENS = ("__import__", "eval(", "exec(", "os.system", "${")


def _reject_dangerous_equation_text(text: str) -> None:
    lowered = text.lower()

    for token in _FORBIDDEN_TOKENS:
        if token in lowered:
            raise ExtractionInputError(
                "Equation text contains disallowed executable patterns."
            )


def extract_equation_candidates(
    context: ExtractionContext,
) -> tuple[CandidateEquationExtraction, ...]:
    """Produce equation extraction candidates from W3 ParsedEquation artifacts."""

    document = context.parsed_document
    equations: list[CandidateEquationExtraction] = []

    for parsed in document.equations:
        _reject_dangerous_equation_text(parsed.normalized_text)
        extraction_id = deterministic_extraction_id(
            "eq-ext",
            document.document_id,
            parsed.equation_id,
            parsed.normalized_text,
        )

        equations.append(
            CandidateEquationExtraction(
                extraction_id=extraction_id,
                document_id=document.document_id,
                raw_representation=parsed.normalized_text,
                provenance=to_source_provenance(
                    parsed.provenance,
                    equation_id=parsed.equation_id,
                ),
                confidence_band=ExtractionConfidence.MEDIUM,
                confidence_score=0.7,
                lifecycle_state=GraphLifecycleState.EXTRACTED,
                variable_symbols=parsed.variable_references,
            ),
        )

    return tuple(sorted(equations, key=lambda item: item.extraction_id))
