"""
W3 parsing exceptions for KG-BLOCK-006.

Extends frozen parser exceptions without modifying knowledge.parsers.exceptions.
"""

from __future__ import annotations

from knowledge.parsers.exceptions import ParserError, ParserValidationError

__all__ = (
    "ParserContentError",
    "ParserEquationError",
    "ParserReferenceError",
    "ParserStructureError",
    "ParserTableError",
    "UnsupportedStructureError",
)


class ParserStructureError(ParserError):
    """Indicate that document structure parsing failed."""


class ParserTableError(ParserError):
    """Indicate that table parsing failed."""


class ParserEquationError(ParserError):
    """Indicate that equation parsing failed."""


class ParserReferenceError(ParserError):
    """Indicate that reference/citation parsing failed."""


class ParserContentError(ParserValidationError):
    """Indicate that parse input content failed validation."""


class UnsupportedStructureError(ParserStructureError):
    """Indicate that the input structure is not supported by the parser."""
