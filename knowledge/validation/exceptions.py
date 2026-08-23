"""W9 validation-layer exceptions for KG-BLOCK-009."""

from __future__ import annotations

from knowledge.graph.exceptions import GraphError

__all__ = (
    "ValidationError",
    "ValidationRegistryError",
    "ValidationRuleError",
)


class ValidationError(GraphError):
    """Base class for W9 validation-layer failures."""


class ValidationRuleError(ValidationError):
    """Indicate invalid or duplicate validation rule registration."""


class ValidationRegistryError(ValidationError):
    """Indicate validation registry operation failure."""
