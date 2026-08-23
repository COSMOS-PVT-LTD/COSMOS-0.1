"""Conflict detection for KG-044."""

from __future__ import annotations

from knowledge.extraction.claim import ClaimConflictVisibility
from knowledge.extraction.w4.models import ExtractionResult
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.validation.models import (
    ConflictClassification,
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding, section_key_from_provenance

__all__ = (
    "detect_conflicts",
)

_RULE_CLAIM_CONFLICT = "VAL-CNF-001"
_RULE_QUANTITY_CONFLICT = "VAL-CNF-002"

_RELATIVE_TOLERANCE = 0.01


def detect_conflicts(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Detect incompatible engineering knowledge without auto-resolution."""

    if context.extraction_result is None:
        return ()

    if not isinstance(context.extraction_result, ExtractionResult):
        return ()

    findings: list[ValidationFinding] = []
    findings.extend(_detect_claim_conflicts(context.extraction_result))
    findings.extend(_detect_quantity_conflicts(context.extraction_result))

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _detect_claim_conflicts(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for claim in extraction_result.claims:
        if claim.conflict_visibility is ClaimConflictVisibility.CONFIRMED_CONFLICT:
            findings.append(
                make_finding(
                    rule_id=_RULE_CLAIM_CONFLICT,
                    object_id=claim.claim_id,
                    severity=ValidationSeverity.HIGH,
                    category=ValidationCategory.CONFLICT,
                    status=ValidationStatus.INVALID,
                    message="Claim is marked with confirmed conflict visibility.",
                    provenance=claim.provenance,
                    conflict_classification=ConflictClassification.CONFLICT,
                ),
            )
        elif claim.conflict_visibility is ClaimConflictVisibility.POTENTIAL_CONFLICT:
            findings.append(
                make_finding(
                    rule_id=_RULE_CLAIM_CONFLICT,
                    object_id=claim.claim_id,
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.CONFLICT,
                    status=ValidationStatus.WARNING,
                    message="Claim is marked with potential conflict visibility.",
                    provenance=claim.provenance,
                    conflict_classification=ConflictClassification.POTENTIAL_CONFLICT,
                ),
            )

    return findings


def _detect_quantity_conflicts(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    groups: dict[
        tuple[str | None, str],
        list[tuple[str, float, SourceProvenanceRecord]],
    ] = {}

    for quantity in extraction_result.quantities:
        if quantity.numeric_value is None or quantity.unit_token is None:
            continue

        section = section_key_from_provenance(quantity.provenance)
        key = (section, quantity.unit_token)
        groups.setdefault(key, []).append(
            (
                quantity.extraction_id,
                quantity.numeric_value,
                quantity.provenance,
            ),
        )

    for key, members in sorted(groups.items(), key=lambda item: str(item[0])):
        if len(members) < 2:
            continue

        reference_value = members[0][1]
        conflicting_ids: list[str] = []

        for extraction_id, numeric_value, _provenance in members[1:]:
            if not _values_compatible(reference_value, numeric_value):
                conflicting_ids.append(extraction_id)

        if not conflicting_ids:
            continue

        findings.append(
            make_finding(
                rule_id=_RULE_QUANTITY_CONFLICT,
                object_id=members[0][0],
                severity=ValidationSeverity.HIGH,
                category=ValidationCategory.CONFLICT,
                status=ValidationStatus.INVALID,
                message="Incompatible quantity values detected for the same section and unit.",
                provenance=members[0][2],
                related_object_ids=tuple(conflicting_ids),
                conflict_classification=ConflictClassification.CONFLICT,
                stable_parts=(str(key),),
            ),
        )

    return findings


def _values_compatible(left: float, right: float) -> bool:
    """Return True when two numeric values are within relative tolerance."""

    if left == right:
        return True

    scale = max(abs(left), abs(right), 1.0)

    return abs(left - right) / scale <= _RELATIVE_TOLERANCE
