"""Ambiguity detection for KG-BLOCK-013 Phase C (KG-044 gap closure)."""

from __future__ import annotations

import re

from knowledge.extraction.w4.models import ExtractionResult
from knowledge.parsers.w3.models import StructuredParsedDocument
from knowledge.validation.models import (
    ConflictClassification,
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "detect_ambiguities",
)

_RULE_HEDGING_LANGUAGE = "VAL-AMB-001"
_RULE_CONFLICTING_SECTION = "VAL-AMB-002"
_RULE_ALTERNATE_VALUE_NOTE = "VAL-AMB-003"

_HEDGE_PATTERN = re.compile(
    r"\b(?:may|might|could|approximately|approx\.|unclear|uncertain|"
    r"alternate source|candidate note)\b",
    flags=re.IGNORECASE,
)
_ALTERNATE_VALUE_PATTERN = re.compile(
    r"\b(?:alternate|conflicting|candidate note)\b.*\b(?:may|might)\b",
    flags=re.IGNORECASE,
)


def detect_ambiguities(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Detect linguistic ambiguity and uncertain engineering statements."""

    findings: list[ValidationFinding] = []

    if context.parsed_document is not None and isinstance(
        context.parsed_document,
        StructuredParsedDocument,
    ):
        findings.extend(
            _detect_section_ambiguity(context.parsed_document),
        )

    if context.extraction_result is not None and isinstance(
        context.extraction_result,
        ExtractionResult,
    ):
        findings.extend(
            _detect_claim_ambiguity(context.extraction_result),
        )

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _detect_section_ambiguity(
    parsed_document: StructuredParsedDocument,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for section in parsed_document.sections:
        title = section.title.casefold()

        if "conflict" in title or "conflicting" in title:
            findings.append(
                make_finding(
                    rule_id=_RULE_CONFLICTING_SECTION,
                    object_id=section.section_id,
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.CONFLICT,
                    status=ValidationStatus.WARNING,
                    message=(
                        "Document contains a section explicitly marked as "
                        "conflicting or ambiguous."
                    ),
                    conflict_classification=ConflictClassification.POTENTIAL_CONFLICT,
                    stable_parts=(section.title,),
                ),
            )

    return findings


def _detect_claim_ambiguity(
    extraction_result: ExtractionResult,
) -> list[ValidationFinding]:
    findings: list[ValidationFinding] = []

    for claim in extraction_result.claims:
        if _ALTERNATE_VALUE_PATTERN.search(claim.claim_text):
            findings.append(
                make_finding(
                    rule_id=_RULE_ALTERNATE_VALUE_NOTE,
                    object_id=claim.claim_id,
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.CONFLICT,
                    status=ValidationStatus.WARNING,
                    message=(
                        "Extracted claim contains alternate-value language "
                        "that may indicate unresolved engineering ambiguity."
                    ),
                    provenance=claim.provenance,
                    conflict_classification=ConflictClassification.POTENTIAL_CONFLICT,
                    stable_parts=(claim.claim_id, "alternate"),
                ),
            )
        elif _HEDGE_PATTERN.search(claim.claim_text):
            findings.append(
                make_finding(
                    rule_id=_RULE_HEDGING_LANGUAGE,
                    object_id=claim.claim_id,
                    severity=ValidationSeverity.LOW,
                    category=ValidationCategory.CONFLICT,
                    status=ValidationStatus.WARNING,
                    message=(
                        "Extracted claim contains hedging language that "
                        "may indicate unresolved ambiguity."
                    ),
                    provenance=claim.provenance,
                    conflict_classification=ConflictClassification.INSUFFICIENT_EVIDENCE,
                    stable_parts=(claim.claim_id, "claim"),
                ),
            )

    return findings
