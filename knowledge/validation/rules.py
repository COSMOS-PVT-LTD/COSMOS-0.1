"""Shared validation helpers for KG-BLOCK-009."""

from __future__ import annotations

from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.validation.identity import deterministic_finding_id
from knowledge.validation.models import (
    ConflictClassification,
    DuplicateKind,
    ValidationCategory,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)

__all__ = (
    "make_finding",
    "provenance_anchor_key",
    "section_key_from_provenance",
)


def make_finding(
    *,
    rule_id: str,
    object_id: str,
    severity: ValidationSeverity,
    category: ValidationCategory,
    status: ValidationStatus,
    message: str,
    provenance: SourceProvenanceRecord | None = None,
    related_object_ids: tuple[str, ...] = (),
    stable_parts: tuple[str, ...] = (),
    duplicate_kind: DuplicateKind | None = None,
    conflict_classification: ConflictClassification | None = None,
) -> ValidationFinding:
    """Construct a deterministic validation finding."""

    finding_id = deterministic_finding_id(
        rule_id,
        object_id,
        *stable_parts,
    )

    return ValidationFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        severity=severity,
        category=category,
        status=status,
        object_id=object_id,
        message=message,
        provenance=provenance,
        related_object_ids=related_object_ids,
        duplicate_kind=duplicate_kind,
        conflict_classification=conflict_classification,
    )


def section_key_from_provenance(
    provenance: SourceProvenanceRecord | None,
) -> str | None:
    """Return a section anchor key when available."""

    if provenance is None:
        return None

    return provenance.anchor.section


def provenance_anchor_key(provenance: SourceProvenanceRecord) -> str:
    """Return a stable provenance anchor key for duplicate grouping."""

    anchor = provenance.anchor

    return "|".join(
        part
        for part in (
            anchor.source_id,
            anchor.document_id,
            anchor.section,
            anchor.paragraph,
            anchor.table,
            anchor.equation,
        )
        if part is not None
    )
