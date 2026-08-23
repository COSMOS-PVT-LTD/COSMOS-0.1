"""W4 extraction exceptions for KG-BLOCK-007."""

from __future__ import annotations

from knowledge.extraction.exceptions import ExtractionError, ExtractionValidationError

__all__ = (
    "ExtractionContentError",
    "ExtractionInputError",
    "ExtractionQuantityError",
    "ExtractionRelationshipError",
    "UnsupportedExtractionError",
)


class ExtractionInputError(ExtractionValidationError):
    """Indicate that extraction input failed validation."""


class ExtractionContentError(ExtractionInputError):
    """Indicate that required source content is missing or invalid."""


class ExtractionQuantityError(ExtractionError):
    """Indicate that quantity extraction failed."""


class ExtractionRelationshipError(ExtractionError):
    """Indicate that relationship extraction failed."""


class UnsupportedExtractionError(ExtractionError):
    """Indicate that the requested extraction type is unsupported."""
