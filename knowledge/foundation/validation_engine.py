"""Lifecycle and schema validators for engineering knowledge."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.correlation import Correlation
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.physical_law import PhysicalLaw
from knowledge.validation.contradiction import ConflictRecord, detect_numeric_conflicts

__all__ = ("ValidationFinding", "ValidationSuite", "validate_engineering_entity")


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationFinding:
    check: str
    passed: bool
    detail: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationSuite:
    passed: bool
    findings: tuple[ValidationFinding, ...]
    conflicts: tuple[ConflictRecord, ...]


def validate_engineering_entity(
    *,
    entity_id: str,
    lifecycle: KnowledgeLifecycle,
    provenance: ProvenanceTrace,
    statement: str,
    applicability: str | None,
    numeric_claims: tuple[tuple[str, str, str, float, str], ...] = (),
) -> ValidationSuite:
    findings = (
        ValidationFinding(
            check="schema",
            passed=bool(entity_id.strip() and statement.strip()),
            detail="identity and statement present",
        ),
        ValidationFinding(
            check="provenance",
            passed=bool(provenance.source_reference_id.strip() and provenance.document_id.strip()),
            detail="source and document identifiers present",
        ),
        ValidationFinding(
            check="applicability",
            passed=lifecycle is not KnowledgeLifecycle.APPROVED or bool(applicability and applicability.strip()),
            detail="approved entities require applicability",
        ),
        ValidationFinding(
            check="authority",
            passed=lifecycle is not KnowledgeLifecycle.APPROVED or bool(provenance.reviewer),
            detail="approved entities require a reviewer",
        ),
    )
    conflicts = detect_numeric_conflicts(numeric_claims) if numeric_claims else ()
    passed = all(item.passed for item in findings) and not conflicts
    return ValidationSuite(passed=passed, findings=findings, conflicts=conflicts)


def applicability_of(entity: PhysicalLaw | Correlation) -> str | None:
    if isinstance(entity, PhysicalLaw):
        return entity.applicability
    return entity.geometry or entity.applicable_fluid
