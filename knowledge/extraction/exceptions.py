"""
COSMOS Knowledge Foundation

Module:
    knowledge.extraction.exceptions

Purpose:
    Extraction-layer exceptions.
"""

from __future__ import annotations

from knowledge.parsers.exceptions import ParserError, ParserValidationError

__all__ = (
    "ExtractionError",
    "ExtractionValidationError",
)


class ExtractionError(ParserError):
    """Base class for extraction-layer failures."""


class ExtractionValidationError(ParserValidationError):
    """Indicate that an extraction contract failed validation."""
