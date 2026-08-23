"""
KG-BLOCK-006 W3 parsing package.

New parsing capabilities (KG-014 → KG-018) without modifying frozen
knowledge.parsers contract modules.
"""

from __future__ import annotations

from knowledge.parsers.w3.content import ParseContext, ParseResult
from knowledge.parsers.w3.equations import extract_equations
from knowledge.parsers.w3.exceptions import (
    ParserContentError,
    ParserEquationError,
    ParserReferenceError,
    ParserStructureError,
    ParserTableError,
    UnsupportedStructureError,
)
from knowledge.parsers.w3.figures import extract_figures
from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import (
    CitationOccurrence,
    LocationAnchor,
    ParsedEquation,
    ParsedFigure,
    ParsedParagraph,
    ParsedTable,
    ParsedTableCell,
    ParsedTableRow,
    ParseProvenance,
    ReferenceRecord,
    StructuredParsedDocument,
)
from knowledge.parsers.w3.pipeline import (
    PARSER_NAME,
    PARSER_VERSION,
    W3DocumentParser,
    parse_document,
)
from knowledge.parsers.w3.registry import (
    ParserOrchestrator,
    ParserRegistry,
    StructuredDocumentParser,
    build_default_parser_registry,
)
from knowledge.parsers.w3.references import extract_citations, extract_references
from knowledge.parsers.w3.structure import parse_document_structure
from knowledge.parsers.w3.tables import extract_tables

__all__ = (
    "PARSER_NAME",
    "PARSER_VERSION",
    "CitationOccurrence",
    "LocationAnchor",
    "ParseContext",
    "ParseProvenance",
    "ParseResult",
    "ParsedEquation",
    "ParsedFigure",
    "ParsedParagraph",
    "ParsedTable",
    "ParsedTableCell",
    "ParsedTableRow",
    "ParserContentError",
    "ParserEquationError",
    "ParserOrchestrator",
    "ParserReferenceError",
    "ParserRegistry",
    "ParserStructureError",
    "ParserTableError",
    "ReferenceRecord",
    "StructuredDocumentParser",
    "StructuredParsedDocument",
    "UnsupportedStructureError",
    "W3DocumentParser",
    "build_default_parser_registry",
    "deterministic_element_id",
    "extract_citations",
    "extract_equations",
    "extract_figures",
    "extract_references",
    "extract_tables",
    "parse_document",
    "parse_document_structure",
)
