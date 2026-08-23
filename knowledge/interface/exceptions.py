"""W11 interface-layer exceptions for KG-BLOCK-011."""

from __future__ import annotations

from knowledge.reasoning.exceptions import ReasoningError

__all__ = (
    "InterfaceError",
    "InterfaceValidationError",
    "RAGControlError",
)


class InterfaceError(ReasoningError):
    """Base class for W11 interface-layer failures."""


class InterfaceValidationError(InterfaceError):
    """Indicate that an interface contract failed validation."""


class RAGControlError(InterfaceError):
    """Indicate controlled RAG orchestration failure."""
