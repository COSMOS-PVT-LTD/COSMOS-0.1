"""Citation integrity validation for KG-BLOCK-013 Phase C (KG-041 gap closure)."""

from __future__ import annotations

from knowledge.parsers.w3.models import StructuredParsedDocument
from knowledge.validation.models import (
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "validate_citations",
)

_RULE_UNRESOLVED_KEY = "VAL-CIT-001"
_RULE_BROKEN_REFERENCE = "VAL-CIT-002"
_RULE_ORPHAN_REFERENCE = "VAL-CIT-003"


def validate_citations(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Validate W3 citation/reference integrity without mutating inputs."""

    parsed_document = context.parsed_document

    if parsed_document is None:
        return ()

    if not isinstance(parsed_document, StructuredParsedDocument):
        return ()

    findings: list[ValidationFinding] = []
    reference_ids = {reference.reference_id for reference in parsed_document.references}
    cited_reference_ids: set[str] = set()

    for citation in parsed_document.citations:
        if citation.reference_id is not None:
            cited_reference_ids.add(citation.reference_id)

            if citation.reference_id not in reference_ids:
                findings.append(
                    make_finding(
                        rule_id=_RULE_BROKEN_REFERENCE,
                        object_id=citation.citation_id,
                        severity=ValidationSeverity.HIGH,
                        category=ValidationCategory.PROVENANCE,
                        status=ValidationStatus.INVALID,
                        message=(
                            "Citation references a bibliography record that "
                            "does not exist in the parsed document."
                        ),
                        related_object_ids=(citation.reference_id,),
                        stable_parts=(citation.reference_id,),
                    ),
                )
            continue

        if citation.citation_key is not None:
            findings.append(
                make_finding(
                    rule_id=_RULE_UNRESOLVED_KEY,
                    object_id=citation.citation_id,
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.PROVENANCE,
                    status=ValidationStatus.WARNING,
                    message=(
                        "Citation key is present but was not resolved to a "
                        "bibliography reference during parsing."
                    ),
                    stable_parts=(citation.citation_key,),
                ),
            )

    for reference in parsed_document.references:
        if reference.reference_id not in cited_reference_ids:
            findings.append(
                make_finding(
                    rule_id=_RULE_ORPHAN_REFERENCE,
                    object_id=reference.reference_id,
                    severity=ValidationSeverity.LOW,
                    category=ValidationCategory.PROVENANCE,
                    status=ValidationStatus.WARNING,
                    message=(
                        "Bibliography reference is not cited anywhere in the "
                        "parsed document."
                    ),
                    stable_parts=(reference.reference_id,),
                ),
            )

    return tuple(sorted(findings, key=lambda item: item.finding_id))
