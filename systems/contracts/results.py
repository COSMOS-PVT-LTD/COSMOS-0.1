"""Calculation result contract for propulsion workflow stages."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from core.version import COSMOS_VERSION

from systems import SYSTEMS_SCHEMA_VERSION

__all__ = (
    "CalculationResult",
    "ProvenanceInfo",
    "ResultStatus",
    "ValidationInfo",
    "ValidityInfo",
    "ValidityState",
    "VerificationInfo",
    "is_current_displayable",
)


class ResultStatus(str, Enum):
    """
    Authoritative result / node status for workflow results.

    CURRENT is the only status that may be presented as the active engineering
    answer. STALE retains history but must not be treated as current.
    """

    NOT_CALCULATED = "NOT_CALCULATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CURRENT = "CURRENT"
    STALE = "STALE"
    FAILED = "FAILED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    OUT_OF_RANGE = "OUT_OF_RANGE"


class ValidityState(str, Enum):
    VALID = "VALID"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def is_current_displayable(status: ResultStatus | str) -> bool:
    """Return True only when a result may be shown as the current answer."""

    value = status.value if isinstance(status, ResultStatus) else str(status)
    return value == ResultStatus.CURRENT.value


@dataclass(frozen=True, slots=True)
class ValidityInfo:
    status: ValidityState = ValidityState.UNKNOWN
    checks: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()
    valid_range: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checks": list(self.checks),
            "violations": list(self.violations),
            "valid_range": self.valid_range,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> ValidityInfo:
        return cls(
            status=ValidityState(str(data.get("status", ValidityState.UNKNOWN.value))),
            checks=tuple(str(item) for item in (data.get("checks") or ())),
            violations=tuple(str(item) for item in (data.get("violations") or ())),
            valid_range=(
                None if data.get("valid_range") is None else str(data["valid_range"])
            ),
        )


@dataclass(frozen=True, slots=True)
class VerificationInfo:
    status: str = "UNKNOWN"
    reference: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {"status": self.status, "reference": self.reference}

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> VerificationInfo:
        return cls(
            status=str(data.get("status", "UNKNOWN")),
            reference=(
                None if data.get("reference") is None else str(data["reference"])
            ),
        )


@dataclass(frozen=True, slots=True)
class ValidationInfo:
    status: str = "NOT_CLAIMED"
    reference: str | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {"status": self.status, "reference": self.reference}

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> ValidationInfo:
        return cls(
            status=str(data.get("status", "NOT_CLAIMED")),
            reference=(
                None if data.get("reference") is None else str(data["reference"])
            ),
        )


@dataclass(frozen=True, slots=True)
class ProvenanceInfo:
    source: str | None = None
    reference: str | None = None
    model: str | None = None
    version: str | None = None
    software_version: str = COSMOS_VERSION
    implementation_revision: str | None = None
    calculation_revision: int | None = None

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "reference": self.reference,
            "model": self.model,
            "version": self.version,
            "software_version": self.software_version,
            "implementation_revision": self.implementation_revision,
            "calculation_revision": self.calculation_revision,
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> ProvenanceInfo:
        rev = data.get("calculation_revision")
        return cls(
            source=None if data.get("source") is None else str(data["source"]),
            reference=None if data.get("reference") is None else str(data["reference"]),
            model=None if data.get("model") is None else str(data["model"]),
            version=None if data.get("version") is None else str(data["version"]),
            software_version=str(data.get("software_version") or COSMOS_VERSION),
            implementation_revision=(
                None
                if data.get("implementation_revision") is None
                else str(data["implementation_revision"])
            ),
            calculation_revision=None if rev is None else int(rev),
        )


@dataclass(slots=True)
class CalculationResult:
    """Structured engineering result envelope (not a bare number)."""

    calculation_type: str
    status: ResultStatus = ResultStatus.NOT_CALCULATED
    result_id: str = field(default_factory=lambda: str(uuid4()))
    model_id: str | None = None
    model_version: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    assumptions: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[dict[str, str], ...] = ()
    validity: ValidityInfo = field(default_factory=ValidityInfo)
    verification: VerificationInfo = field(default_factory=VerificationInfo)
    validation: ValidationInfo = field(default_factory=ValidationInfo)
    provenance: ProvenanceInfo = field(default_factory=ProvenanceInfo)
    software_version: str = COSMOS_VERSION
    design_revision: int = 0
    stage_id: str | None = None
    schema_version: str = SYSTEMS_SCHEMA_VERSION

    def mark_stale(self) -> None:
        if self.status is ResultStatus.CURRENT:
            self.status = ResultStatus.STALE

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "assumptions": list(self.assumptions),
            "calculation_type": self.calculation_type,
            "design_revision": self.design_revision,
            "errors": [dict(item) for item in self.errors],
            "inputs": dict(self.inputs),
            "model_id": self.model_id,
            "model_version": self.model_version,
            "outputs": dict(self.outputs),
            "provenance": self.provenance.to_canonical_dict(),
            "result_id": self.result_id,
            "schema_version": self.schema_version,
            "software_version": self.software_version,
            "stage_id": self.stage_id,
            "status": self.status.value,
            "validation": self.validation.to_canonical_dict(),
            "validity": self.validity.to_canonical_dict(),
            "verification": self.verification.to_canonical_dict(),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_canonical_dict(cls, data: dict[str, object]) -> CalculationResult:
        return cls(
            result_id=str(data.get("result_id") or uuid4()),
            calculation_type=str(data["calculation_type"]),
            status=ResultStatus(str(data.get("status", ResultStatus.NOT_CALCULATED.value))),
            model_id=None if data.get("model_id") is None else str(data["model_id"]),
            model_version=(
                None if data.get("model_version") is None else str(data["model_version"])
            ),
            inputs=dict(data.get("inputs") or {}),
            outputs=dict(data.get("outputs") or {}),
            assumptions=tuple(str(item) for item in (data.get("assumptions") or ())),
            warnings=tuple(str(item) for item in (data.get("warnings") or ())),
            errors=tuple(
                {str(k): str(v) for k, v in dict(item).items()}
                for item in (data.get("errors") or ())
            ),
            validity=ValidityInfo.from_canonical_dict(dict(data.get("validity") or {})),
            verification=VerificationInfo.from_canonical_dict(
                dict(data.get("verification") or {})
            ),
            validation=ValidationInfo.from_canonical_dict(
                dict(data.get("validation") or {})
            ),
            provenance=ProvenanceInfo.from_canonical_dict(
                dict(data.get("provenance") or {})
            ),
            software_version=str(data.get("software_version") or COSMOS_VERSION),
            design_revision=int(data.get("design_revision") or 0),
            stage_id=None if data.get("stage_id") is None else str(data["stage_id"]),
            schema_version=str(data.get("schema_version") or SYSTEMS_SCHEMA_VERSION),
        )
