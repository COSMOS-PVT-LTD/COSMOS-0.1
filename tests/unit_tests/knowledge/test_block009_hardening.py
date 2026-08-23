"""Engineering-review hardening tests for KG-BLOCK-009."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphLifecycleState
from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology import (
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    canonicalize_extraction_result,
)
from knowledge.validation import (
    ValidationCategory,
    ValidationContext,
    ValidationEngine,
    ValidationRule,
    ValidationRuleError,
    ValidationRuleRegistry,
    ValidationSeverity,
    ValidationStatus,
    validate_context,
    validate_schema,
)
from tests.unit_tests.knowledge.extraction.test_w4_extraction import _parse_and_extract


def _build_registry() -> OntologyRegistry:
    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-material-lox",
            canonical_name="Liquid Oxygen",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="LOX",
                    canonical_term_id="term-material-lox",
                ),
            ),
        ),
    )
    return registry


def test_schema_accepts_quantity_relationship_endpoints() -> None:
    """KG-040 must not flag valid quantity→entity relationship endpoints."""

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Propulsion",
                "Material: LOX",
                "Operating pressure 5 MPa.",
            ],
        ),
    )
    findings = validate_schema(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
        ),
    )

    assert extraction.relationships
    assert not any(finding.rule_id == "VAL-SCH-002" for finding in findings)


def test_validation_rule_registry_rejects_duplicate_rule_ids() -> None:
    """Validation rule registry must reject duplicate rule identifiers."""

    registry = ValidationRuleRegistry()

    def _noop_validator(_context: ValidationContext) -> tuple[()]:
        return ()

    rule = ValidationRule(
        rule_id="VAL-TEST-001",
        name="noop",
        category=ValidationCategory.SCHEMA,
        severity=ValidationSeverity.LOW,
        description="noop",
        validator=_noop_validator,
    )
    registry.register(rule)

    with pytest.raises(ValidationRuleError, match="already registered"):
        registry.register(rule)


def test_validation_does_not_mutate_extraction_inputs() -> None:
    """W9 validation must be observational and must not mutate W4 artifacts."""

    extraction = _parse_and_extract("Material: LOX\nThe chamber pressure is 20 bar.\n")
    canonical = canonicalize_extraction_result(extraction, _build_registry())
    before_extraction = extraction.to_mapping()
    before_canonical = canonical.to_mapping()

    validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )

    assert extraction.to_mapping() == before_extraction
    assert canonical.to_mapping() == before_canonical


def test_validation_does_not_promote_candidate_lifecycle() -> None:
    """W9 validation must not promote extraction candidates to approved facts."""

    extraction = _parse_and_extract("Material: LOX\n")
    validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
        ),
    )

    assert all(
        entity.lifecycle_state is GraphLifecycleState.CANDIDATE
        for entity in extraction.entities
    )


def test_finding_ids_are_stable_across_repeated_runs() -> None:
    """Validation finding IDs must be stable across repeated evaluation."""

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Chamber",
                "Pressure is 5 MPa.",
                "Pressure is 20 MPa.",
            ],
        ),
    )
    context = ValidationContext(extraction_result=extraction)

    first = ValidationEngine().validate(context)
    second = ValidationEngine().validate(context)

    assert [finding.finding_id for finding in first.findings] == [
        finding.finding_id for finding in second.findings
    ]


def test_validation_engine_empty_context_is_safe() -> None:
    """Validation engine must accept an empty context without raising."""

    report = ValidationEngine().validate(ValidationContext())

    assert report.findings == ()
    assert report.report_digest


def test_w4_w5_integration_avoids_provenance_false_positives() -> None:
    """Valid W4→W5 integration must not emit provenance document mismatches."""

    extraction = _parse_and_extract("Material: LOX\nOperating pressure 5 MPa.\n")
    canonical = canonicalize_extraction_result(extraction, _build_registry())
    report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )

    provenance_findings = [
        finding
        for finding in report.findings
        if finding.category is ValidationCategory.PROVENANCE
        and finding.status is ValidationStatus.INVALID
    ]

    assert not provenance_findings
