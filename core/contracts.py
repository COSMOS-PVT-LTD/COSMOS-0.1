"""
COSMOS Core — shared contracts and validation result types.

Domain-independent interfaces consumed by physics, numerics, and engineering
layers. Knowledge-layer metadata models remain separate; these contracts
define the computational kernel surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

__all__ = (
    "CanonicalSerializable",
    "DimensionProtocol",
    "HasMetadata",
    "PhysicalConstantProtocol",
    "QuantityProtocol",
    "UnitProtocol",
    "ValidationIssue",
    "ValidationResult",
    "ValidationSeverity",
)


class ValidationSeverity:
    """Validation issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """
    A single validation finding.

    Attributes
    ----------
    code:
        Stable machine-readable issue code.
    message:
        Human-readable explanation.
    field:
        Optional field or parameter name.
    severity:
        Issue severity (``error``, ``warning``, or ``info``).
    """

    code: str
    message: str
    field: str | None = None
    severity: str = ValidationSeverity.ERROR


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """
    Outcome of a validation operation.

    Validation is idempotent: re-validating an already valid object must
    produce an equivalent valid result.
    """

    is_valid: bool
    issues: tuple[ValidationIssue, ...] = ()

    @classmethod
    def valid(cls) -> ValidationResult:
        """Return a successful validation result."""

        return cls(is_valid=True)

    @classmethod
    def invalid(cls, *issues: ValidationIssue) -> ValidationResult:
        """Return a failed validation result with one or more issues."""

        if not issues:
            issues = (
                ValidationIssue(
                    code="validation_failed",
                    message="Validation failed.",
                ),
            )
        return cls(is_valid=False, issues=issues)

    @property
    def error_messages(self) -> tuple[str, ...]:
        """Return error-level issue messages in deterministic order."""

        return tuple(
            issue.message
            for issue in self.issues
            if issue.severity == ValidationSeverity.ERROR
        )


@runtime_checkable
class DimensionProtocol(Protocol):
    """Physical dimension contract based on SI base exponents."""

    @property
    def exponents(self) -> tuple[int, int, int, int, int, int, int]:
        """Return ``(L, M, T, I, Θ, N, J)`` exponent vector."""

    def is_dimensionless(self) -> bool:
        """Return ``True`` when all base exponents are zero."""

    def is_compatible_with(self, other: DimensionProtocol) -> bool:
        """Return ``True`` when dimensions are equal."""


@runtime_checkable
class UnitProtocol(Protocol):
    """Measurement unit contract."""

    @property
    def symbol(self) -> str:
        """Canonical unit symbol."""

    @property
    def dimension(self) -> DimensionProtocol:
        """Physical dimension of quantities expressed in this unit."""

    def factor_to_si(self) -> float:
        """Multiplicative factor converting one unit to SI."""

    def offset_to_si(self) -> float:
        """Additive offset applied after scaling to reach SI."""


@runtime_checkable
class QuantityProtocol(Protocol):
    """Engineering quantity contract."""

    @property
    def magnitude(self) -> float:
        """Numerical value in the attached unit."""

    @property
    def unit(self) -> UnitProtocol:
        """Unit of the magnitude."""

    def to_si(self) -> float:
        """Return magnitude expressed in SI base/derived units."""

    def dimension(self) -> DimensionProtocol:
        """Return the physical dimension."""


@runtime_checkable
class PhysicalConstantProtocol(Protocol):
    """Physical constant with units and provenance metadata."""

    @property
    def name(self) -> str:
        """Human-readable constant name."""

    @property
    def symbol(self) -> str:
        """Standard symbol."""

    @property
    def quantity(self) -> QuantityProtocol:
        """Constant value with unit."""


@runtime_checkable
class HasMetadata(Protocol):
    """Object exposing structured metadata."""

    def metadata_dict(self) -> dict[str, object]:
        """Return metadata as a deterministic mapping."""


@runtime_checkable
class CanonicalSerializable(Protocol):
    """Object supporting deterministic canonical serialization."""

    def to_canonical_dict(self) -> dict[str, object]:
        """Return a deterministic dictionary representation."""

    @classmethod
    def from_canonical_dict(
        cls,
        data: dict[str, object],
    ) -> CanonicalSerializable:
        """Reconstruct from a canonical dictionary."""
