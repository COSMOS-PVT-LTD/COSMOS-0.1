"""Unit and dimension validation for KG-042."""

from __future__ import annotations

from knowledge.extraction.w4.models import ExtractionResult
from knowledge.validation.models import (
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.rules import make_finding

__all__ = (
    "KNOWN_ENGINEERING_UNIT_TOKENS",
    "validate_units",
)

_RULE_UNKNOWN_UNIT = "VAL-UNT-001"
_RULE_MISSING_UNIT = "VAL-UNT-002"
_RULE_AMBIGUOUS_UNIT = "VAL-UNT-003"
_RULE_INCOMPATIBLE_DIMENSION_GROUP = "VAL-UNT-004"

KNOWN_ENGINEERING_UNIT_TOKENS = frozenset(
    {
        "Pa",
        "kPa",
        "MPa",
        "bar",
        "K",
        "kg",
        "g",
        "m",
        "mm",
        "s",
        "kN",
        "N",
        "kN/s",
        "kg/s",
        "m/s",
        "m/s2",
        "W",
        "kW",
        "MW",
        "%",
        "deg",
        "°",
    },
)

_UNIT_FAMILY: dict[str, str] = {
    "Pa": "pressure",
    "kPa": "pressure",
    "MPa": "pressure",
    "bar": "pressure",
    "K": "temperature",
    "kg": "mass",
    "g": "mass",
    "m": "length",
    "mm": "length",
    "s": "time",
    "kN": "force",
    "N": "force",
    "kg/s": "mass_flow",
    "m/s": "velocity",
    "m/s2": "acceleration",
    "W": "power",
    "kW": "power",
    "MW": "power",
}


def validate_units(context: ValidationContext) -> tuple[ValidationFinding, ...]:
    """Validate quantity/unit candidates without duplicating canonical Quantity models."""

    if context.extraction_result is None:
        return ()

    if not isinstance(context.extraction_result, ExtractionResult):
        return ()

    findings: list[ValidationFinding] = []
    family_by_section: dict[str, set[str]] = {}

    for quantity in context.extraction_result.quantities:
        findings.extend(_validate_quantity_candidate(quantity))

        section = quantity.provenance.anchor.section

        if section is None or quantity.unit_token is None:
            continue

        family = _UNIT_FAMILY.get(quantity.unit_token)

        if family is None:
            continue

        families = family_by_section.setdefault(section, set())

        if families and family not in families:
            findings.append(
                make_finding(
                    rule_id=_RULE_INCOMPATIBLE_DIMENSION_GROUP,
                    object_id=quantity.extraction_id,
                    severity=ValidationSeverity.MEDIUM,
                    category=ValidationCategory.UNIT_DIMENSION,
                    status=ValidationStatus.WARNING,
                    message="Section contains quantities from incompatible unit families.",
                    provenance=quantity.provenance,
                    stable_parts=(section, family),
                ),
            )

        families.add(family)

    return tuple(sorted(findings, key=lambda item: item.finding_id))


def _validate_quantity_candidate(quantity: object) -> list[ValidationFinding]:
    from knowledge.extraction.w4.models import CandidateQuantityExtraction

    if not isinstance(quantity, CandidateQuantityExtraction):
        return []

    findings: list[ValidationFinding] = []

    if quantity.ambiguous:
        findings.append(
            make_finding(
                rule_id=_RULE_AMBIGUOUS_UNIT,
                object_id=quantity.extraction_id,
                severity=ValidationSeverity.LOW,
                category=ValidationCategory.UNIT_DIMENSION,
                status=ValidationStatus.WARNING,
                message="Quantity unit token is marked ambiguous.",
                provenance=quantity.provenance,
            ),
        )

    if (
        not quantity.dimensionless
        and quantity.numeric_value is not None
        and quantity.unit_token is None
    ):
        findings.append(
            make_finding(
                rule_id=_RULE_MISSING_UNIT,
                object_id=quantity.extraction_id,
                severity=ValidationSeverity.MEDIUM,
                category=ValidationCategory.UNIT_DIMENSION,
                status=ValidationStatus.INVALID,
                message="Numeric quantity is missing a required unit token.",
                provenance=quantity.provenance,
            ),
        )

    if quantity.unit_token is not None and quantity.unit_token not in KNOWN_ENGINEERING_UNIT_TOKENS:
        findings.append(
            make_finding(
                rule_id=_RULE_UNKNOWN_UNIT,
                object_id=quantity.extraction_id,
                severity=ValidationSeverity.MEDIUM,
                category=ValidationCategory.UNIT_DIMENSION,
                status=ValidationStatus.WARNING,
                message="Quantity unit token is not in the known engineering unit registry.",
                provenance=quantity.provenance,
                stable_parts=(quantity.unit_token,),
            ),
        )

    return findings
