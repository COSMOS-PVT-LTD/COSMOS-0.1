"""
W3 structured parsing models for KG-BLOCK-006 (KG-014 → KG-018).

New models only — frozen knowledge.parsers.models remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.provenance import ExtractionProvenance
from knowledge.parsers.exceptions import ParserValidationError
from knowledge.parsers.models import DocumentSection

__all__ = (
    "CitationOccurrence",
    "LocationAnchor",
    "ParsedEquation",
    "ParsedFigure",
    "ParsedParagraph",
    "ParsedTable",
    "ParsedTableCell",
    "ParsedTableRow",
    "ParseProvenance",
    "ReferenceRecord",
    "StructuredParsedDocument",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise ParserValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise ParserValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


def _validate_non_negative_int(field_name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ParserValidationError(f"{field_name} must be an integer.")

    if value < 0:
        raise ParserValidationError(f"{field_name} must be non-negative.")

    return value


def _validate_unique_ids(field_name: str, items: tuple[object, ...], attr: str) -> None:
    ids = {getattr(item, attr) for item in items}

    if len(ids) != len(items):
        raise ParserValidationError(f"{field_name} identifiers must be unique.")


@dataclass(frozen=True, slots=True, kw_only=True)
class LocationAnchor:
    """Location anchor within a parsed document."""

    line_number: int | None = None
    page_number: int | None = None
    section_id: str | None = None
    block_index: int | None = None

    def __post_init__(self) -> None:
        if self.line_number is not None and self.line_number <= 0:
            raise ParserValidationError("line_number must be positive when set.")

        if self.page_number is not None:
            if self.page_number <= 0:
                raise ParserValidationError("page_number must be positive when set.")

        object.__setattr__(
            self,
            "section_id",
            _validate_optional_non_empty_string("section_id", self.section_id),
        )

        if self.block_index is not None:
            object.__setattr__(
                self,
                "block_index",
                _validate_non_negative_int("block_index", self.block_index),
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {}

        if self.line_number is not None:
            payload["line_number"] = self.line_number
        if self.page_number is not None:
            payload["page_number"] = self.page_number
        if self.section_id is not None:
            payload["section_id"] = self.section_id
        if self.block_index is not None:
            payload["block_index"] = self.block_index

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ParseProvenance:
    """Provenance linking a parsed element to its source artifact."""

    source_id: str
    artifact_id: str
    content_hash: str
    document_id: str
    location: LocationAnchor | None = None
    parser_name: str | None = None
    parser_version: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )
        object.__setattr__(
            self,
            "content_hash",
            _validate_non_empty_string("content_hash", self.content_hash),
        )
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "parser_name",
            _validate_optional_non_empty_string("parser_name", self.parser_name),
        )
        object.__setattr__(
            self,
            "parser_version",
            _validate_optional_non_empty_string(
                "parser_version",
                self.parser_version,
            ),
        )

        if self.location is not None and not isinstance(self.location, LocationAnchor):
            raise ParserValidationError("location must be a LocationAnchor instance.")

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "artifact_id": self.artifact_id,
            "content_hash": self.content_hash,
            "document_id": self.document_id,
            "source_id": self.source_id,
        }

        if self.location is not None:
            payload["location"] = self.location.to_mapping()
        if self.parser_name is not None:
            payload["parser_name"] = self.parser_name
        if self.parser_version is not None:
            payload["parser_version"] = self.parser_version

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedParagraph:
    """Parsed paragraph with provenance (KG-014)."""

    paragraph_id: str
    text_length: int
    provenance: ParseProvenance
    section_id: str | None = None
    ordering_index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "paragraph_id",
            _validate_non_empty_string("paragraph_id", self.paragraph_id),
        )
        object.__setattr__(
            self,
            "text_length",
            _validate_non_negative_int("text_length", self.text_length),
        )
        object.__setattr__(
            self,
            "section_id",
            _validate_optional_non_empty_string("section_id", self.section_id),
        )
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ordering_index": self.ordering_index,
            "paragraph_id": self.paragraph_id,
            "provenance": self.provenance.to_mapping(),
            "text_length": self.text_length,
        }

        if self.section_id is not None:
            payload["section_id"] = self.section_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedTableCell:
    """Single table cell (KG-015)."""

    column_index: int
    value: str
    row_index: int
    is_header: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "column_index",
            _validate_non_negative_int("column_index", self.column_index),
        )
        object.__setattr__(
            self,
            "row_index",
            _validate_non_negative_int("row_index", self.row_index),
        )

        if not isinstance(self.value, str):
            raise ParserValidationError("value must be a string.")

        if not isinstance(self.is_header, bool):
            raise ParserValidationError("is_header must be a boolean.")

    def to_mapping(self) -> dict[str, object]:
        return {
            "column_index": self.column_index,
            "is_header": self.is_header,
            "row_index": self.row_index,
            "value": self.value,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedTableRow:
    """Table row with ordered cells (KG-015)."""

    row_index: int
    cells: tuple[ParsedTableCell, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "row_index",
            _validate_non_negative_int("row_index", self.row_index),
        )

        if not isinstance(self.cells, tuple):
            raise ParserValidationError("cells must be a tuple.")

        for cell in self.cells:
            if not isinstance(cell, ParsedTableCell):
                raise ParserValidationError(
                    "cells must contain ParsedTableCell instances."
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "cells": [cell.to_mapping() for cell in self.cells],
            "row_index": self.row_index,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedTable:
    """Parsed table structure (KG-015)."""

    table_id: str
    provenance: ParseProvenance
    rows: tuple[ParsedTableRow, ...]
    column_count: int
    ordering_index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "table_id",
            _validate_non_empty_string("table_id", self.table_id),
        )
        object.__setattr__(
            self,
            "column_count",
            _validate_non_negative_int("column_count", self.column_count),
        )
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if not isinstance(self.rows, tuple):
            raise ParserValidationError("rows must be a tuple.")

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "column_count": self.column_count,
            "ordering_index": self.ordering_index,
            "provenance": self.provenance.to_mapping(),
            "rows": [row.to_mapping() for row in self.rows],
            "table_id": self.table_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedFigure:
    """Figure metadata without semantic interpretation (KG-016)."""

    figure_id: str
    provenance: ParseProvenance
    caption: str | None = None
    label: str | None = None
    ordering_index: int = 0
    source_reference: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "figure_id",
            _validate_non_empty_string("figure_id", self.figure_id),
        )
        object.__setattr__(
            self,
            "caption",
            _validate_optional_non_empty_string("caption", self.caption),
        )
        object.__setattr__(
            self,
            "label",
            _validate_optional_non_empty_string("label", self.label),
        )
        object.__setattr__(
            self,
            "source_reference",
            _validate_optional_non_empty_string(
                "source_reference",
                self.source_reference,
            ),
        )
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "figure_id": self.figure_id,
            "ordering_index": self.ordering_index,
            "provenance": self.provenance.to_mapping(),
        }

        if self.caption is not None:
            payload["caption"] = self.caption
        if self.label is not None:
            payload["label"] = self.label
        if self.source_reference is not None:
            payload["source_reference"] = self.source_reference

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ParsedEquation:
    """Parsed equation representation without engineering semantics (KG-017)."""

    equation_id: str
    normalized_text: str
    provenance: ParseProvenance
    ordering_index: int = 0
    variable_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "equation_id",
            _validate_non_empty_string("equation_id", self.equation_id),
        )

        if not isinstance(self.normalized_text, str):
            raise ParserValidationError("normalized_text must be a string.")

        normalized = " ".join(self.normalized_text.split())

        if not normalized:
            raise ParserValidationError("normalized_text must not be blank.")

        object.__setattr__(self, "normalized_text", normalized)
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if not isinstance(self.variable_references, tuple):
            raise ParserValidationError("variable_references must be a tuple.")

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "equation_id": self.equation_id,
            "normalized_text": self.normalized_text,
            "ordering_index": self.ordering_index,
            "provenance": self.provenance.to_mapping(),
            "variable_references": list(self.variable_references),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ReferenceRecord:
    """Bibliographic reference record (KG-018)."""

    reference_id: str
    provenance: ParseProvenance
    ordering_index: int = 0
    title: str | None = None
    authors: str | None = None
    year: str | None = None
    source_link: str | None = None
    raw_metadata: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reference_id",
            _validate_non_empty_string("reference_id", self.reference_id),
        )
        object.__setattr__(
            self,
            "title",
            _validate_optional_non_empty_string("title", self.title),
        )
        object.__setattr__(
            self,
            "authors",
            _validate_optional_non_empty_string("authors", self.authors),
        )
        object.__setattr__(
            self,
            "year",
            _validate_optional_non_empty_string("year", self.year),
        )
        object.__setattr__(
            self,
            "source_link",
            _validate_optional_non_empty_string("source_link", self.source_link),
        )
        object.__setattr__(
            self,
            "raw_metadata",
            _validate_optional_non_empty_string("raw_metadata", self.raw_metadata),
        )
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "ordering_index": self.ordering_index,
            "provenance": self.provenance.to_mapping(),
            "reference_id": self.reference_id,
        }

        for key in ("authors", "raw_metadata", "source_link", "title", "year"):
            value = getattr(self, key)

            if value is not None:
                payload[key] = value

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class CitationOccurrence:
    """In-document citation occurrence linked to a reference (KG-018)."""

    citation_id: str
    provenance: ParseProvenance
    reference_id: str | None = None
    citation_key: str | None = None
    ordering_index: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "citation_id",
            _validate_non_empty_string("citation_id", self.citation_id),
        )
        object.__setattr__(
            self,
            "reference_id",
            _validate_optional_non_empty_string("reference_id", self.reference_id),
        )
        object.__setattr__(
            self,
            "citation_key",
            _validate_optional_non_empty_string("citation_key", self.citation_key),
        )
        object.__setattr__(
            self,
            "ordering_index",
            _validate_non_negative_int("ordering_index", self.ordering_index),
        )

        if self.reference_id is None and self.citation_key is None:
            raise ParserValidationError(
                "citation must include reference_id or citation_key."
            )

        if not isinstance(self.provenance, ParseProvenance):
            raise ParserValidationError(
                "provenance must be a ParseProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "citation_id": self.citation_id,
            "ordering_index": self.ordering_index,
            "provenance": self.provenance.to_mapping(),
        }

        if self.reference_id is not None:
            payload["reference_id"] = self.reference_id
        if self.citation_key is not None:
            payload["citation_key"] = self.citation_key

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class StructuredParsedDocument:
    """
    Complete W3 parsed document (KG-014 → KG-018).

    Composes frozen DocumentSection models with new W3 element types.
    Does not embed full source text.
    """

    document_id: str
    source_id: str
    artifact_id: str
    parser_name: str
    parser_version: str
    normalized_content_hash: str
    sections: tuple[DocumentSection, ...] = ()
    paragraphs: tuple[ParsedParagraph, ...] = ()
    tables: tuple[ParsedTable, ...] = ()
    figures: tuple[ParsedFigure, ...] = ()
    equations: tuple[ParsedEquation, ...] = ()
    citations: tuple[CitationOccurrence, ...] = ()
    references: tuple[ReferenceRecord, ...] = ()
    extraction: ExtractionProvenance | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )
        object.__setattr__(
            self,
            "parser_name",
            _validate_non_empty_string("parser_name", self.parser_name),
        )
        object.__setattr__(
            self,
            "parser_version",
            _validate_non_empty_string("parser_version", self.parser_version),
        )
        object.__setattr__(
            self,
            "normalized_content_hash",
            _validate_non_empty_string(
                "normalized_content_hash",
                self.normalized_content_hash,
            ),
        )

        for field_name, items, attr in (
            ("sections", self.sections, "section_id"),
            ("paragraphs", self.paragraphs, "paragraph_id"),
            ("tables", self.tables, "table_id"),
            ("figures", self.figures, "figure_id"),
            ("equations", self.equations, "equation_id"),
            ("citations", self.citations, "citation_id"),
            ("references", self.references, "reference_id"),
        ):
            if not isinstance(items, tuple):
                raise ParserValidationError(f"{field_name} must be a tuple.")

            _validate_unique_ids(field_name, items, attr)

        if self.extraction is not None and not isinstance(
            self.extraction,
            ExtractionProvenance,
        ):
            raise ParserValidationError(
                "extraction must be an ExtractionProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "artifact_id": self.artifact_id,
            "citations": [item.to_mapping() for item in self.citations],
            "document_id": self.document_id,
            "equations": [item.to_mapping() for item in self.equations],
            "figures": [item.to_mapping() for item in self.figures],
            "normalized_content_hash": self.normalized_content_hash,
            "paragraphs": [item.to_mapping() for item in self.paragraphs],
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "references": [item.to_mapping() for item in self.references],
            "sections": [section.to_mapping() for section in self.sections],
            "source_id": self.source_id,
            "tables": [item.to_mapping() for item in self.tables],
        }

        if self.extraction is not None:
            payload["extraction"] = self.extraction.to_mapping()

        return payload
