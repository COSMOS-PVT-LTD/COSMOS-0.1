"""Extended W9 validation orchestration for KG-BLOCK-013 Phase C capabilities."""

from __future__ import annotations

from knowledge.validation.ambiguity_detector import detect_ambiguities
from knowledge.validation.citation_validator import validate_citations
from knowledge.validation.engine import ValidationEngine
from knowledge.validation.identity import validation_report_digest
from knowledge.validation.models import ValidationContext, ValidationFinding, ValidationReport

__all__ = (
    "ValidationEnginePhaseC",
    "validate_context_extended",
)


class ValidationEnginePhaseC(ValidationEngine):
    """W9 validation engine extended with Phase-C citation and ambiguity checks."""

    def validate(self, context: ValidationContext) -> ValidationReport:
        base_report = super().validate(context)
        phase_c_findings: list[ValidationFinding] = []
        phase_c_findings.extend(validate_citations(context))
        phase_c_findings.extend(detect_ambiguities(context))

        if not phase_c_findings:
            return base_report

        merged = tuple(
            sorted(
                (*base_report.findings, *phase_c_findings),
                key=lambda item: item.finding_id,
            ),
        )
        digest = validation_report_digest(
            *(finding.finding_id for finding in merged),
        )

        return ValidationReport(findings=merged, report_digest=digest)


def validate_context_extended(context: ValidationContext) -> ValidationReport:
    """Validate a context using the Phase-C extended validation engine."""

    return ValidationEnginePhaseC().validate(context)
