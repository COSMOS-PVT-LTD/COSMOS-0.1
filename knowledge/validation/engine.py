"""Validation engine orchestrator for KG-BLOCK-009."""

from __future__ import annotations

from knowledge.validation.conflicts import detect_conflicts
from knowledge.validation.duplicates import detect_duplicates
from knowledge.validation.identity import validation_report_digest
from knowledge.validation.models import ValidationContext, ValidationFinding, ValidationReport
from knowledge.validation.provenance import validate_provenance
from knowledge.validation.registry import ValidationRuleRegistry
from knowledge.validation.schema import validate_schema
from knowledge.validation.units import validate_units

__all__ = (
    "ValidationEngine",
    "validate_context",
)


class ValidationEngine:
    """Orchestrate KG-040 → KG-044 validation without mutating inputs."""

    def __init__(self, registry: ValidationRuleRegistry | None = None) -> None:
        self._registry = registry or ValidationRuleRegistry()

    @property
    def registry(self) -> ValidationRuleRegistry:
        return self._registry

    def validate(self, context: ValidationContext) -> ValidationReport:
        """Run the complete W9 validation pipeline."""

        if not isinstance(context, ValidationContext):
            raise TypeError("context must be a ValidationContext instance.")

        findings: list[ValidationFinding] = []
        findings.extend(validate_schema(context))
        findings.extend(validate_provenance(context))
        findings.extend(validate_units(context))
        findings.extend(detect_duplicates(context))
        findings.extend(detect_conflicts(context))

        ordered = tuple(sorted(findings, key=lambda item: item.finding_id))
        digest = validation_report_digest(
            *(finding.finding_id for finding in ordered),
        )

        return ValidationReport(findings=ordered, report_digest=digest)


def validate_context(context: ValidationContext) -> ValidationReport:
    """Validate a context using the default validation engine."""

    return ValidationEngine().validate(context)
