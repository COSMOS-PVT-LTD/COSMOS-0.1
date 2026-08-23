"""Duplicate detection for KG-043."""

from __future__ import annotations

from knowledge.extraction.w4.models import ExtractionResult
from knowledge.validation.models import (
    DuplicateKind,
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding, provenance_anchor_key

__all__ = (
    "detect_duplicates",
)

_RULE_EXACT_DUPLICATE = "VAL-DUP-001"
_RULE_SAME_LABEL = "VAL-DUP-002"
_RULE_SAME_VALUE = "VAL-DUP-003"


def detect_duplicates(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Detect deterministic duplicate groups using domain identity keys."""

    if context.extraction_result is None:
        return ()

    if not isinstance(context.extraction_result, ExtractionResult):
        return ()

    findings: list[ValidationFinding] = []
    findings.extend(_detect_exact_duplicate_ids(context.extraction_result))
    findings.extend(_detect_same_label_different_entity(context.extraction_result))
    findings.extend(_detect_same_value_different_provenance(context.extraction_result))

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _detect_exact_duplicate_ids(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    seen: dict[str, str] = {}

    for entity in extraction_result.entities:
        if entity.extraction_id in seen:
            findings.append(
                make_finding(
                    rule_id=_RULE_EXACT_DUPLICATE,
                    object_id=entity.extraction_id,
                    severity=ValidationSeverity.CRITICAL,
                    category=ValidationCategory.DUPLICATE,
                    status=ValidationStatus.INVALID,
                    message="Duplicate extraction_id detected in entity batch.",
                    provenance=entity.provenance,
                    duplicate_kind=DuplicateKind.EXACT_DUPLICATE,
                ),
            )
        seen[entity.extraction_id] = entity.extraction_id

    return findings


def _detect_same_label_different_entity(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    groups: dict[tuple[str, str], list[str]] = {}

    for entity in extraction_result.entities:
        key = (entity.extracted_label.casefold(), entity.entity_kind.value)
        groups.setdefault(key, []).append(entity.extraction_id)

    for (label, kind), extraction_ids in sorted(groups.items()):
        unique_ids = sorted(set(extraction_ids))

        if len(unique_ids) < 2:
            continue

        findings.append(
            make_finding(
                rule_id=_RULE_SAME_LABEL,
                object_id=unique_ids[0],
                severity=ValidationSeverity.INFO,
                category=ValidationCategory.DUPLICATE,
                status=ValidationStatus.WARNING,
                message=(
                    "Multiple entity candidates share the same label and kind "
                    "but distinct extraction identities."
                ),
                related_object_ids=tuple(unique_ids[1:]),
                duplicate_kind=DuplicateKind.SAME_LABEL_DIFFERENT_ENTITY,
                stable_parts=(label, kind),
            ),
        )

    return findings


def _detect_same_value_different_provenance(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []
    groups: dict[tuple[str, str | None, float | None], list[tuple[str, str]]] = {}

    for quantity in extraction_result.quantities:
        value_key = (
            quantity.raw_text,
            quantity.unit_token,
            quantity.numeric_value,
        )
        groups.setdefault(value_key, []).append(
            (
                quantity.extraction_id,
                provenance_anchor_key(quantity.provenance),
            ),
        )

    for value_key, members in sorted(groups.items(), key=lambda item: str(item[0])):
        extraction_ids = sorted({member[0] for member in members})
        provenance_keys = {member[1] for member in members}

        if len(extraction_ids) < 2:
            continue

        if len(provenance_keys) <= 1:
            continue

        findings.append(
            make_finding(
                rule_id=_RULE_SAME_VALUE,
                object_id=extraction_ids[0],
                severity=ValidationSeverity.LOW,
                category=ValidationCategory.DUPLICATE,
                status=ValidationStatus.WARNING,
                message=(
                    "Identical quantity values appear with different provenance anchors."
                ),
                related_object_ids=tuple(extraction_ids[1:]),
                duplicate_kind=DuplicateKind.SAME_VALUE_DIFFERENT_PROVENANCE,
                stable_parts=(str(value_key),),
            ),
        )

    return findings
