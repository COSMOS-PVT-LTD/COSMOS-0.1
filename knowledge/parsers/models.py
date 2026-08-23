"""
COSMOS Knowledge Foundation

Module:
    knowledge.parsers.models

Purpose:
    Normalized parsed-document structure contracts.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.graph.provenance import ExtractionProvenance
from knowledge.parsers.exceptions import ParserValidationError

__all__ = (
    "DocumentSection",
    "NormalizedParsedDocument",
    "PageAnchor",
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


def _validate_positive_int(field_name: str, value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ParserValidationError(f"{field_name} must be an integer.")

    if value <= 0:
        raise ParserValidationError(
            f"{field_name} must be a positive integer."
        )

    return value


@dataclass(frozen=True, slots=True, kw_only=True)
class PageAnchor:
    """Page-level anchor within a parsed document."""

    page_number: int
    section_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "page_number",
            _validate_positive_int("page_number", self.page_number),
        )
        object.__setattr__(
            self,
            "section_id",
            _validate_optional_non_empty_string(
                "section_id",
                self.section_id,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {"page_number": self.page_number}

        if self.section_id is not None:
            payload["section_id"] = self.section_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentSection:
    """Structured section within a normalized parsed document."""

    section_id: str
    title: str
    level: int = 1
    page_anchor: PageAnchor | None = None
    parent_section_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "section_id",
            _validate_non_empty_string("section_id", self.section_id),
        )
        object.__setattr__(
            self,
            "title",
            _validate_non_empty_string("title", self.title),
        )
        object.__setattr__(
            self,
            "level",
            _validate_positive_int("level", self.level),
        )

        if self.page_anchor is not None and not isinstance(
            self.page_anchor,
            PageAnchor,
        ):
            raise ParserValidationError(
                "page_anchor must be a PageAnchor instance."
            )

        object.__setattr__(
            self,
            "parent_section_id",
            _validate_optional_non_empty_string(
                "parent_section_id",
                self.parent_section_id,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
        }

        if self.page_anchor is not None:
            payload["page_anchor"] = self.page_anchor.to_mapping()
        if self.parent_section_id is not None:
            payload["parent_section_id"] = self.parent_section_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedParsedDocument:
    """
    Normalized parsed document structure for downstream extraction.

    Does not embed full copyrighted source text; stores structure and anchors.
    """

    document_id: str
    source_id: str
    artifact_id: str
    parser_version: str
    sections: tuple[DocumentSection, ...] = ()
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
            "parser_version",
            _validate_non_empty_string(
                "parser_version",
                self.parser_version,
            ),
        )

        if not isinstance(self.sections, tuple):
            raise ParserValidationError("sections must be a tuple.")

        section_ids = {section.section_id for section in self.sections}

        if len(section_ids) != len(self.sections):
            raise ParserValidationError("Section identifiers must be unique.")

        if self.extraction is not None and not isinstance(
            self.extraction,
            ExtractionProvenance,
        ):
            raise ParserValidationError(
                "extraction must be an ExtractionProvenance instance."
            )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "document_id": self.document_id,
            "source_id": self.source_id,
            "artifact_id": self.artifact_id,
            "parser_version": self.parser_version,
            "sections": [section.to_mapping() for section in self.sections],
        }

        if self.extraction is not None:
            payload["extraction"] = self.extraction.to_mapping()

        return payload
