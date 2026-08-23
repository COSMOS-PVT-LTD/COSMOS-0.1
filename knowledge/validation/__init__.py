"""Public exports for knowledge.validation (W9)."""

from __future__ import annotations

from knowledge.validation.conflicts import detect_conflicts
from knowledge.validation.duplicates import detect_duplicates
from knowledge.validation.engine import ValidationEngine, validate_context
from knowledge.validation.exceptions import (
    ValidationError,
    ValidationRegistryError,
    ValidationRuleError,
)
from knowledge.validation.identity import deterministic_finding_id, validation_report_digest
from knowledge.validation.models import (
    ConflictClassification,
    DuplicateKind,
    ValidationCategory,
    ValidationContext,
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
    ValidationStatus,
)
from knowledge.validation.provenance import validate_provenance
from knowledge.validation.registry import ValidationRule, ValidationRuleRegistry
from knowledge.validation.schema import validate_schema
from knowledge.validation.units import KNOWN_ENGINEERING_UNIT_TOKENS, validate_units

__all__ = (
    "ConflictClassification",
    "DuplicateKind",
    "KNOWN_ENGINEERING_UNIT_TOKENS",
    "ValidationCategory",
    "ValidationContext",
    "ValidationEngine",
    "ValidationError",
    "ValidationFinding",
    "ValidationRegistryError",
    "ValidationReport",
    "ValidationRule",
    "ValidationRuleError",
    "ValidationRuleRegistry",
    "ValidationSeverity",
    "ValidationStatus",
    "detect_conflicts",
    "detect_duplicates",
    "deterministic_finding_id",
    "validate_context",
    "validate_provenance",
    "validate_schema",
    "validate_units",
    "validation_report_digest",
)
