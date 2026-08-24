"""Explicit staged equation validation. UNKNOWN is not PASS."""

from __future__ import annotations

from knowledge.equations.ast import parse_equation
from knowledge.equations.models import (
    EquationValidationState,
    SourceEquationCandidate,
    ValidatedEquationCandidate,
)
from knowledge.models.dimension_check import check_dimensional_consistency
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("validate_equation_candidate",)


def validate_equation_candidate(candidate: SourceEquationCandidate) -> ValidatedEquationCandidate:
    reasons: list[str] = []
    schema_ok = bool(candidate.candidate_id and candidate.raw_text.strip())
    if not schema_ok:
        reasons.append("schema: missing candidate identity or raw text")

    source_ok = bool(
        candidate.source_id.strip()
        and candidate.document_id.strip()
        and candidate.provenance.source_reference_id.strip()
        and candidate.page_number
    )
    if not source_ok:
        reasons.append("source: provenance incomplete")

    unit_state = (
        EquationValidationState.VALID
        if candidate.units
        else EquationValidationState.UNKNOWN
    )
    if unit_state is EquationValidationState.UNKNOWN:
        reasons.append("units: none recovered from source")

    dimension_state = _dimension_state(candidate)
    reasons.append(f"dimensions: {dimension_state.value}")

    ambiguous = any(item.ambiguous for item in candidate.variables)
    semantic_state = (
        EquationValidationState.AMBIGUOUS
        if ambiguous
        else EquationValidationState.REVIEW_REQUIRED
    )
    if ambiguous:
        reasons.append("semantic: ambiguous variable requires review")

    applicability_state = (
        EquationValidationState.VALID
        if candidate.applicability
        else EquationValidationState.UNKNOWN
    )

    if not schema_ok:
        state = EquationValidationState.INVALID
    elif not source_ok:
        state = EquationValidationState.NON_AUTHORITATIVE
    elif dimension_state is EquationValidationState.VALIDATION_FAILURE:
        state = EquationValidationState.VALIDATION_FAILURE
    elif ambiguous:
        state = EquationValidationState.AMBIGUOUS
    elif dimension_state is EquationValidationState.UNKNOWN:
        state = EquationValidationState.UNKNOWN
    else:
        state = EquationValidationState.REVIEW_REQUIRED

    syntax_state = (
        EquationValidationState.VALID
        if parse_equation(candidate.raw_text) is not None
        else EquationValidationState.REVIEW_REQUIRED
    )
    extraction_state = (
        EquationValidationState.VALID
        if candidate.raw_text.strip()
        else EquationValidationState.EXTRACTION_UNAVAILABLE
    )
    if syntax_state is EquationValidationState.REVIEW_REQUIRED:
        reasons.append("syntax: source equation did not parse into an AST")

    return ValidatedEquationCandidate(
        candidate=candidate,
        state=state,
        schema_ok=schema_ok,
        source_ok=source_ok,
        unit_state=unit_state,
        dimension_state=dimension_state,
        semantic_state=semantic_state,
        applicability_state=applicability_state,
        reasons=tuple(reasons),
        lifecycle=KnowledgeLifecycle.CANDIDATE,
        extraction_state=extraction_state,
        syntax_state=syntax_state,
    )


def _dimension_state(candidate: SourceEquationCandidate) -> EquationValidationState:
    from knowledge.foundation.variable_catalog import SI_EXPONENTS

    expression = candidate.raw_text.replace("×", "*")
    if "=" not in expression:
        return EquationValidationState.UNKNOWN
    symbols = [item.symbol for item in candidate.variables]
    missing = [symbol for symbol in symbols if symbol not in SI_EXPONENTS]
    if missing:
        return EquationValidationState.UNKNOWN
    mapping = {symbol: SI_EXPONENTS[symbol] for symbol in symbols}
    result = check_dimensional_consistency(expression, mapping)
    if result.passed:
        return EquationValidationState.VALID
    return EquationValidationState.VALIDATION_FAILURE
