"""
COSMOS Knowledge Foundation

Module:
    knowledge.parsers.exceptions

Purpose:
    Parser-layer exceptions.
"""

from __future__ import annotations

from knowledge.ingestion.exceptions import IngestionError, IngestionValidationError

__all__ = (
    "ParserError",
    "ParserValidationError",
)


class ParserError(IngestionError):
    """Base class for parser-layer failures."""


class ParserValidationError(IngestionValidationError):
    """Indicate that a parser contract failed validation."""
