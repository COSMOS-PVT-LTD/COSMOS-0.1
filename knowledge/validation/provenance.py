"""Provenance validation for KG-041."""

from __future__ import annotations

from knowledge.extraction.w4.models import ExtractionResult
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology.models import CanonicalizationResult
from knowledge.validation.models import (
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "validate_provenance",
)

_RULE_MISSING_ANCHOR = "VAL-PRV-001"
_RULE_DOCUMENT_MISMATCH = "VAL-PRV-002"
_RULE_BROKEN_CHAIN = "VAL-PRV-003"


def validate_provenance(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Validate provenance integrity across W4/W5 artifacts."""

    findings: list[ValidationFinding] = []

    if context.extraction_result is not None:
        findings.extend(
            _validate_extraction_provenance(
                context.extraction_result,
                expected_document_id=context.document_id,
                expected_source_id=context.source_id,
            ),
        )

    if context.canonicalization_result is not None and context.extraction_result is not None:
        findings.extend(
            _validate_canonicalization_provenance_chain(
                context.extraction_result,
                context.canonicalization_result,
            ),
        )

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _validate_provenance_record(
    *,
    object_id: str,
    provenance: SourceProvenanceRecord,
    expected_document_id: str | None,
    expected_source_id: str | None,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    anchor = provenance.anchor

    if not anchor.source_id and not anchor.document_id:
        findings.append(
            make_finding(
                rule_id=_RULE_MISSING_ANCHOR,
                object_id=object_id,
                severity=ValidationSeverity.HIGH,
                category=ValidationCategory.PROVENANCE,
                status=ValidationStatus.INVALID,
                message="Provenance anchor is missing source and document identity.",
                provenance=provenance,
            ),
        )

    if expected_document_id is not None and anchor.document_id != expected_document_id:
        findings.append(
            make_finding(
                rule_id=_RULE_DOCUMENT_MISMATCH,
                object_id=object_id,
                severity=ValidationSeverity.MEDIUM,
                category=ValidationCategory.PROVENANCE,
                status=ValidationStatus.INVALID,
                message="Provenance document_id is inconsistent with validation context.",
                provenance=provenance,
                stable_parts=(expected_document_id,),
            ),
        )

    if expected_source_id is not None and anchor.source_id not in (None, expected_source_id):
        findings.append(
            make_finding(
                rule_id=_RULE_DOCUMENT_MISMATCH,
                object_id=object_id,
                severity=ValidationSeverity.MEDIUM,
                category=ValidationCategory.PROVENANCE,
                status=ValidationStatus.INVALID,
                message="Provenance source_id is inconsistent with validation context.",
                provenance=provenance,
                stable_parts=(expected_source_id,),
            ),
        )

    return findings


def _validate_extraction_provenance(
    extraction_result: ExtractionResult,
    *,
    expected_document_id: str | None,
    expected_source_id: str | None,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for entity in extraction_result.entities:
        findings.extend(
            _validate_provenance_record(
                object_id=entity.extraction_id,
                provenance=entity.provenance,
                expected_document_id=expected_document_id or entity.document_id,
                expected_source_id=expected_source_id or extraction_result.source_id,
            ),
        )

    for quantity in extraction_result.quantities:
        findings.extend(
            _validate_provenance_record(
                object_id=quantity.extraction_id,
                provenance=quantity.provenance,
                expected_document_id=expected_document_id or quantity.document_id,
                expected_source_id=expected_source_id or extraction_result.source_id,
            ),
        )

    for claim in extraction_result.claims:
        findings.extend(
            _validate_provenance_record(
                object_id=claim.claim_id,
                provenance=claim.provenance,
                expected_document_id=expected_document_id or claim.document_id,
                expected_source_id=expected_source_id or extraction_result.source_id,
            ),
        )

    return findings


def _validate_canonicalization_provenance_chain(
    extraction_result: ExtractionResult,
    canonicalization_result: CanonicalizationResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    extraction_ids = {entity.extraction_id for entity in extraction_result.entities}

    for mapping in canonicalization_result.mappings:
        if mapping.extraction_id not in extraction_ids:
            findings.append(
                make_finding(
                    rule_id=_RULE_BROKEN_CHAIN,
                    object_id=mapping.mapping_id,
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.PROVENANCE,
                    status=ValidationStatus.INVALID,
                    message="Canonicalization mapping references a missing extraction candidate.",
                    provenance=mapping.provenance,
                    related_object_ids=(mapping.extraction_id,),
                ),
            )

    return findings
