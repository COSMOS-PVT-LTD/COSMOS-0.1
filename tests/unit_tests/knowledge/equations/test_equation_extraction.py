"""Equation extraction — source-faithful candidates, explicit validation states."""

from __future__ import annotations

from knowledge.equations import (
    CONTRADICTION_DETECTED,
    EquationValidationState,
    REPRESENTATION_CONFLICT,
    SourceEquationCandidate,
    detect_equation_conflicts,
    detect_representation_conflicts,
    detect_source_equations,
    review_validated_equation,
    validate_equation_candidate,
)
from knowledge.equations.models import VariableBinding
from knowledge.foundation.equation_approval import EquationReviewDecision
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace


def _pages(*lines: str) -> tuple[tuple[int, str], ...]:
    return ((1, "\n".join(lines)),)


def test_detects_labeled_reynolds_identity() -> None:
    candidates = detect_source_equations(
        _pages(
            "Chapter 1 Fluid Mechanics Identities",
            "1.1 Reynolds number",
            "Eq. 1 Re = rho * V * D / mu",
            "Assumption: single characteristic velocity and length.",
            "Valid for internal and external viscous flows.",
        ),
        source_id="SRC-RE",
        document_id="DOC-RE",
        reference_id="REF-RE",
    )
    assert len(candidates) == 1
    item = candidates[0]
    assert item.raw_text == "Re = rho * V * D / mu"
    assert item.label is not None and "1" in item.label
    assert item.latex is None
    assert {binding.symbol for binding in item.variables} >= {"Re", "rho", "V", "D", "mu"}
    assert item.assumptions
    assert item.applicability
    validated = validate_equation_candidate(item)
    assert validated.dimension_state is EquationValidationState.VALID
    assert validated.state is EquationValidationState.REVIEW_REQUIRED
    assert validated.lifecycle is KnowledgeLifecycle.CANDIDATE


def test_missing_equation_is_not_guessed() -> None:
    candidates = detect_source_equations(
        _pages("This page has words but no identity."),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )
    assert candidates == ()


def test_missing_provenance_is_non_authoritative() -> None:
    candidate = SourceEquationCandidate(
        candidate_id="EQ-MISSING",
        source_id="",
        document_id="DOC",
        page_number=None,
        section_id=None,
        region_id=None,
        label=None,
        raw_text="Re = rho * V * D / mu",
        latex=None,
        mathml=None,
        image_reference=None,
        variables=(),
        constants=(),
        units=(),
        assumptions=(),
        applicability=None,
        confidence=0.2,
        provenance=ProvenanceTrace(
            source_reference_id="REF-X",
            document_id="DOC",
            extraction_method="manual",
        ),
    )
    validated = validate_equation_candidate(candidate)
    assert validated.state is EquationValidationState.NON_AUTHORITATIVE
    try:
        review_validated_equation(
            validated,
            EquationReviewDecision.APPROVE,
            reviewer="reviewer",
        )
        raise AssertionError("missing provenance must not approve")
    except ValueError:
        pass


def test_dimensional_inconsistency_is_validation_failure() -> None:
    candidates = detect_source_equations(
        _pages("Eq. 1 Re = rho * V * D * mu"),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )
    validated = validate_equation_candidate(candidates[0])
    assert validated.dimension_state is EquationValidationState.VALIDATION_FAILURE
    assert validated.state is EquationValidationState.VALIDATION_FAILURE


def test_ambiguous_variable_requires_review() -> None:
    candidates = detect_source_equations(
        _pages("Eq. 1 Re = u * V * D / mu"),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )
    validated = validate_equation_candidate(candidates[0])
    assert any(item.ambiguous for item in candidates[0].variables)
    assert validated.state in {
        EquationValidationState.AMBIGUOUS,
        EquationValidationState.REVIEW_REQUIRED,
    }


def test_contradictory_sources_are_not_silently_chosen() -> None:
    left, right = detect_source_equations(
        _pages("Eq. 1 Re = rho * V * D / mu"),
        source_id="SRC-A",
        document_id="DOC-A",
        reference_id="REF-A",
    ) + detect_source_equations(
        _pages("Eq. 1 Re = rho * V * D * mu"),
        source_id="SRC-B",
        document_id="DOC-B",
        reference_id="REF-B",
    )
    conflicts = detect_equation_conflicts((left, right))
    assert conflicts
    assert conflicts[0].reason == CONTRADICTION_DETECTED


def test_representation_conflict() -> None:
    native = detect_source_equations(
        _pages("Eq. 1 Re = rho * V * D / mu"),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )[0]
    ocr = SourceEquationCandidate(
        candidate_id="ocr-1",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        section_id=None,
        region_id=None,
        label="Eq. 1",
        raw_text="Re = p * V * D / mu",
        latex=None,
        mathml=None,
        image_reference="img-1",
        variables=(VariableBinding(symbol="Re", definition=None, unit=None),),
        constants=(),
        units=(),
        assumptions=(),
        applicability=None,
        confidence=0.2,
        provenance=native.provenance,
        ocr_text="Re = p * V * D / mu",
    )
    conflicts = detect_representation_conflicts(native, ocr)
    assert conflicts
    assert conflicts[0].reason == REPRESENTATION_CONFLICT


def test_unknown_symbols_are_not_pass() -> None:
    candidates = detect_source_equations(
        _pages("Eq. 1 Foo = Bar * Baz"),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )
    validated = validate_equation_candidate(candidates[0])
    assert validated.dimension_state is EquationValidationState.UNKNOWN
    assert validated.state is not EquationValidationState.VALID


def test_fail_safe_split_and_collision_cases() -> None:
    assert detect_source_equations(
        ((1, "Eq. 1 Re = rho * V"), (2, "D / mu")),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )[0].raw_text == "Re = rho * V"
    multi = detect_source_equations(
        _pages("Eq. 1 Re = rho * V * D / mu  Eq. 2 Nu = 0.023 * Re"),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    )
    assert len(multi) >= 1
    assert detect_source_equations(
        _pages("Figure 1 shows the channel. Table 1 lists symbols."),
        source_id="SRC",
        document_id="DOC",
        reference_id="REF",
    ) == ()


def test_golden_equation_shapes_from_source_text() -> None:
    corpus = (
        "a = b + c",
        "sigma = p * r / t",
        "q = k * dT / dx",
        "Re = rho * V * D / mu",
    )
    for expression in corpus:
        found = detect_source_equations(
            _pages(f"Eq. 1 {expression}"),
            source_id="SRC",
            document_id="DOC",
            reference_id="REF",
        )
        assert found
        assert found[0].raw_text == expression
