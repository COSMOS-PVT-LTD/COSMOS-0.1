"""
COSMOS Knowledge Foundation

Module:
    knowledge.reasoning.exceptions

Purpose:
    Reasoning and context-assembly layer exceptions.
"""

from __future__ import annotations

from knowledge.search.exceptions import SearchError

__all__ = (
    "ReasoningError",
    "ReasoningValidationError",
)


class ReasoningError(SearchError):
    """Base class for reasoning-layer failures."""


class ReasoningValidationError(ReasoningError):
    """Indicate that a reasoning contract failed validation."""
