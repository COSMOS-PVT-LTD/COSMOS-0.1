"""Validation result models for KG-BLOCK-009."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.validation.exceptions import ValidationError

if TYPE_CHECKING:
    from knowledge.extraction.w4.models import ExtractionResult
    from knowledge.graph.contracts import ImmutableGraphRecord
    from knowledge.ontology.models import CanonicalizationResult
    from knowledge.parsers.w3.models import StructuredParsedDocument

__all__ = (
    "ConflictClassification",
    "DuplicateKind",
    "ValidationCategory",
    "ValidationContext",
    "ValidationFinding",
    "ValidationReport",
    "ValidationSeverity",
    "ValidationStatus",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ValidationError(f"{field_name} must not be blank.")

    return cleaned


class ValidationSeverity(Enum):
    """Severity taxonomy for validation findings."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ValidationStatus(Enum):
    """Outcome status for a validation finding."""

    VALID = "VALID"
    INVALID = "INVALID"
    WARNING = "WARNING"
    UNSUPPORTED = "UNSUPPORTED"


class ValidationCategory(Enum):
    """Validation batch category (KG-040 → KG-044)."""

    SCHEMA = "SCHEMA"
    PROVENANCE = "PROVENANCE"
    UNIT_DIMENSION = "UNIT_DIMENSION"
    DUPLICATE = "DUPLICATE"
    CONFLICT = "CONFLICT"


class DuplicateKind(Enum):
    """Duplicate classification taxonomy."""

    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    DOMAIN_DUPLICATE = "DOMAIN_DUPLICATE"
    SAME_LABEL_DIFFERENT_ENTITY = "SAME_LABEL_DIFFERENT_ENTITY"
    SAME_VALUE_DIFFERENT_PROVENANCE = "SAME_VALUE_DIFFERENT_PROVENANCE"


class ConflictClassification(Enum):
    """Conflict classification taxonomy."""

    CONFLICT = "CONFLICT"
    POTENTIAL_CONFLICT = "POTENTIAL_CONFLICT"
    NO_CONFLICT = "NO_CONFLICT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationFinding:
    """Single deterministic validation finding."""

    finding_id: str
    rule_id: str
    severity: ValidationSeverity
    category: ValidationCategory
    status: ValidationStatus
    object_id: str
    message: str
    provenance: SourceProvenanceRecord | None = None
    related_object_ids: tuple[str, ...] = ()
    duplicate_kind: DuplicateKind | None = None
    conflict_classification: ConflictClassification | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "finding_id",
            _validate_non_empty_string("finding_id", self.finding_id),
        )
        object.__setattr__(
            self,
            "rule_id",
            _validate_non_empty_string("rule_id", self.rule_id),
        )
        object.__setattr__(
            self,
            "object_id",
            _validate_non_empty_string("object_id", self.object_id),
        )
        object.__setattr__(
            self,
            "message",
            _validate_non_empty_string("message", self.message),
        )

        if not isinstance(self.severity, ValidationSeverity):
            raise ValidationError("severity must be a ValidationSeverity value.")
        if not isinstance(self.category, ValidationCategory):
            raise ValidationError("category must be a ValidationCategory value.")
        if not isinstance(self.status, ValidationStatus):
            raise ValidationError("status must be a ValidationStatus value.")
        if not isinstance(self.related_object_ids, tuple):
            raise ValidationError("related_object_ids must be a tuple.")
        if self.provenance is not None and not isinstance(
            self.provenance,
            SourceProvenanceRecord,
        ):
            raise ValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "category": self.category.value,
            "finding_id": self.finding_id,
            "message": self.message,
            "object_id": self.object_id,
            "related_object_ids": list(self.related_object_ids),
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "status": self.status.value,
        }

        if self.provenance is not None:
            payload["provenance"] = self.provenance.to_mapping()
        if self.duplicate_kind is not None:
            payload["duplicate_kind"] = self.duplicate_kind.value
        if self.conflict_classification is not None:
            payload["conflict_classification"] = self.conflict_classification.value

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationReport:
    """Aggregated validation report with deterministic ordering."""

    findings: tuple[ValidationFinding, ...] = ()
    report_digest: str = ""

    @property
    def is_valid(self) -> bool:
        """Return True when no high-severity invalid findings exist."""

        for finding in self.findings:
            if finding.status is ValidationStatus.INVALID and finding.severity in (
                ValidationSeverity.HIGH,
                ValidationSeverity.CRITICAL,
            ):
                return False

        return True

    def summary_counts(self) -> dict[str, int]:
        """Return severity counts for all findings."""

        counts = {severity.value: 0 for severity in ValidationSeverity}

        for finding in self.findings:
            counts[finding.severity.value] += 1

        return counts

    def to_mapping(self) -> dict[str, object]:
        return {
            "findings": [finding.to_mapping() for finding in self.findings],
            "is_valid": self.is_valid,
            "report_digest": self.report_digest,
            "summary_counts": self.summary_counts(),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationContext:
    """Bounded validation input spanning W4/W5/W6 artifacts."""

    document_id: str | None = None
    source_id: str | None = None
    extraction_result: ExtractionResult | None = None
    canonicalization_result: CanonicalizationResult | None = None
    graph_record: ImmutableGraphRecord | None = None
    parsed_document: StructuredParsedDocument | None = None
