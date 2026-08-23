"""Evidence-chain completeness validation for engineering knowledge (Step 6)."""

from __future__ import annotations

from knowledge.extraction.claim import CandidateClaimExtraction
from knowledge.extraction.entity import CandidateEntityExtraction
from knowledge.extraction.w4.models import CandidateQuantityExtraction
from knowledge.validation.models import (
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "validate_evidence_chain",
)

_RULE_MISSING_ENTITY_PROVENANCE = "VAL-EVC-001"
_RULE_MISSING_CLAIM_PROVENANCE = "VAL-EVC-002"
_RULE_MISSING_QUANTITY_PROVENANCE = "VAL-EVC-003"
_RULE_MISSING_DOCUMENT_ANCHOR = "VAL-EVC-004"


def _check_provenance_anchor(
    *,
    rule_id: str,
    object_id: str,
    provenance,
    label: str,
) -> ValidationFinding | None:
    if provenance is None:
        return make_finding(
            rule_id=rule_id,
            object_id=object_id,
            severity=ValidationSeverity.HIGH,
            category=ValidationCategory.PROVENANCE,
            status=ValidationStatus.INVALID,
            message=f"{label} is missing provenance.",
        )

    anchor = provenance.anchor
    if not anchor.document_id or not str(anchor.document_id).strip():
        return make_finding(
            rule_id=_RULE_MISSING_DOCUMENT_ANCHOR,
            object_id=object_id,
            severity=ValidationSeverity.HIGH,
            category=ValidationCategory.PROVENANCE,
            status=ValidationStatus.INVALID,
            message=f"{label} provenance is missing a document anchor.",
            provenance=provenance,
        )

    return None


def validate_evidence_chain(
    context: ValidationContext,
) -> tuple[ValidationFinding, ...]:
    """Validate that extracted artifacts maintain provenance chain integrity."""

    extraction = context.extraction_result
    if extraction is None:
        return ()

    findings: list[ValidationFinding] = []

    for entity in extraction.entities:
        if not isinstance(entity, CandidateEntityExtraction):
            continue
        finding = _check_provenance_anchor(
            rule_id=_RULE_MISSING_ENTITY_PROVENANCE,
            object_id=entity.extraction_id,
            provenance=entity.provenance,
            label="Extracted entity",
        )
        if finding is not None:
            findings.append(finding)

    for claim in extraction.claims:
        if not isinstance(claim, CandidateClaimExtraction):
            continue
        finding = _check_provenance_anchor(
            rule_id=_RULE_MISSING_CLAIM_PROVENANCE,
            object_id=claim.claim_id,
            provenance=claim.provenance,
            label="Extracted claim",
        )
        if finding is not None:
            findings.append(finding)

    for quantity in extraction.quantities:
        if not isinstance(quantity, CandidateQuantityExtraction):
            continue
        finding = _check_provenance_anchor(
            rule_id=_RULE_MISSING_QUANTITY_PROVENANCE,
            object_id=quantity.extraction_id,
            provenance=quantity.provenance,
            label="Extracted quantity",
        )
        if finding is not None:
            findings.append(finding)

    return tuple(sorted(findings, key=lambda item: item.finding_id))
