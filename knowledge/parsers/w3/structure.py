"""
Document structure parsing (NEW KG-014).
"""

from __future__ import annotations

import json
import re

from knowledge.parsers.models import DocumentSection, PageAnchor
from knowledge.parsers.w3.exceptions import ParserStructureError, UnsupportedStructureError
from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import LocationAnchor, ParsedParagraph, ParseProvenance

__all__ = (
    "StructureParseOutput",
    "parse_document_structure",
)

_HEADING_PATTERN = re.compile(r"^(?P<level>#{1,6})\s+(?P<title>.+)$")
_PAGE_MARKER_PATTERN = re.compile(r"^<!--\s*page:\s*(\d+)\s*-->$")


class StructureParseOutput:
    """Intermediate structure parse result."""

    __slots__ = ("paragraphs", "sections")

    def __init__(
        self,
        sections: tuple[DocumentSection, ...],
        paragraphs: tuple[ParsedParagraph, ...],
    ) -> None:
        self.sections = sections
        self.paragraphs = paragraphs


def _base_provenance(
    *,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    document_id: str,
    parser_name: str,
    parser_version: str,
    location: LocationAnchor | None,
) -> ParseProvenance:
    return ParseProvenance(
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        document_id=document_id,
        location=location,
        parser_name=parser_name,
        parser_version=parser_version,
    )


def _parse_markdown_structure(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> StructureParseOutput:
    sections: list[DocumentSection] = []
    paragraphs: list[ParsedParagraph] = []
    section_stack: list[tuple[int, str]] = []
    current_page = 1
    current_section_id: str | None = None
    paragraph_index = 0

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()

        if not line:
            continue

        page_match = _PAGE_MARKER_PATTERN.match(line)

        if page_match is not None:
            current_page = int(page_match.group(1))

            if current_page <= 0:
                raise ParserStructureError("Page marker must be a positive integer.")

            continue

        heading_match = _HEADING_PATTERN.match(line)

        if heading_match is not None:
            level = len(heading_match.group("level"))
            title = heading_match.group("title").strip()

            if not title:
                raise ParserStructureError("Heading title must not be blank.")

            section_id = deterministic_element_id(
                "sec",
                document_id,
                str(line_number),
                title,
            )

            parent_section_id: str | None = None

            while section_stack and section_stack[-1][0] >= level:
                section_stack.pop()

            if section_stack:
                parent_section_id = section_stack[-1][1]

            section_stack.append((level, section_id))

            sections.append(
                DocumentSection(
                    section_id=section_id,
                    title=title,
                    level=level,
                    page_anchor=PageAnchor(
                        page_number=current_page,
                        section_id=section_id,
                    ),
                    parent_section_id=parent_section_id,
                ),
            )
            current_section_id = section_id
            continue

        if line.startswith("|") and "|" in line[1:]:
            continue

        paragraph_index += 1
        paragraph_id = deterministic_element_id(
            "para",
            document_id,
            str(line_number),
            str(paragraph_index),
        )
        location = LocationAnchor(
            line_number=line_number,
            page_number=current_page,
            section_id=current_section_id,
        )

        paragraphs.append(
            ParsedParagraph(
                paragraph_id=paragraph_id,
                text_length=len(line),
                provenance=_base_provenance(
                    source_id=source_id,
                    artifact_id=artifact_id,
                    content_hash=content_hash,
                    document_id=document_id,
                    parser_name=parser_name,
                    parser_version=parser_version,
                    location=location,
                ),
                section_id=current_section_id,
                ordering_index=paragraph_index,
            ),
        )

    return StructureParseOutput(
        sections=tuple(sections),
        paragraphs=tuple(paragraphs),
    )


def _parse_html_envelope_structure(
    *,
    envelope: dict[str, object],
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> StructureParseOutput:
    blocks = envelope.get("blocks")

    if not isinstance(blocks, list):
        raise ParserStructureError("HTML envelope must include a blocks list.")

    sections: list[DocumentSection] = []
    paragraphs: list[ParsedParagraph] = []
    section_stack: list[tuple[int, str]] = []
    paragraph_index = 0

    for block_index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ParserStructureError("HTML block entries must be mappings.")

        tag = block.get("tag")
        text = block.get("text")

        if not isinstance(tag, str) or not isinstance(text, str):
            raise ParserStructureError("HTML blocks require tag and text fields.")

        if tag in {"h1", "h2", "h3"}:
            level = int(tag[1])

            if not text.strip():
                raise ParserStructureError("Heading title must not be blank.")

            section_id = deterministic_element_id(
                "sec",
                document_id,
                str(block_index),
                tag,
                text,
            )
            parent_section_id: str | None = None

            while section_stack and section_stack[-1][0] >= level:
                section_stack.pop()

            if section_stack:
                parent_section_id = section_stack[-1][1]

            section_stack.append((level, section_id))
            sections.append(
                DocumentSection(
                    section_id=section_id,
                    title=text,
                    level=level,
                    parent_section_id=parent_section_id,
                ),
            )
            continue

        if tag in {"p", "li", "pre", "code"}:
            paragraph_index += 1
            paragraph_id = deterministic_element_id(
                "para",
                document_id,
                str(block_index),
                tag,
                text,
            )
            paragraphs.append(
                ParsedParagraph(
                    paragraph_id=paragraph_id,
                    text_length=len(text),
                    provenance=_base_provenance(
                        source_id=source_id,
                        artifact_id=artifact_id,
                        content_hash=content_hash,
                        document_id=document_id,
                        parser_name=parser_name,
                        parser_version=parser_version,
                        location=LocationAnchor(block_index=block_index),
                    ),
                    ordering_index=paragraph_index,
                ),
            )

    return StructureParseOutput(
        sections=tuple(sections),
        paragraphs=tuple(paragraphs),
    )


def _parse_docx_envelope_structure(
    *,
    envelope: dict[str, object],
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> StructureParseOutput:
    paragraphs_raw = envelope.get("paragraphs")

    if not isinstance(paragraphs_raw, list):
        raise ParserStructureError("DOCX envelope must include a paragraphs list.")

    sections: list[DocumentSection] = []
    paragraphs: list[ParsedParagraph] = []

    for index, text in enumerate(paragraphs_raw, start=1):
        if not isinstance(text, str):
            raise ParserStructureError("DOCX paragraph entries must be strings.")

        if not text.strip():
            continue

        paragraph_id = deterministic_element_id(
            "para",
            document_id,
            str(index),
            text,
        )
        paragraphs.append(
            ParsedParagraph(
                paragraph_id=paragraph_id,
                text_length=len(text),
                provenance=_base_provenance(
                    source_id=source_id,
                    artifact_id=artifact_id,
                    content_hash=content_hash,
                    document_id=document_id,
                    parser_name=parser_name,
                    parser_version=parser_version,
                    location=LocationAnchor(block_index=index - 1),
                ),
                ordering_index=index,
            ),
        )

    return StructureParseOutput(sections=tuple(sections), paragraphs=tuple(paragraphs))


def parse_document_structure(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
    is_structured_envelope: bool,
) -> StructureParseOutput:
    """Parse document structure from markdown or structured JSON envelopes."""

    if is_structured_envelope:
        try:
            envelope = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ParserStructureError(
                "Structured envelope must be valid JSON."
            ) from exc

        if not isinstance(envelope, dict):
            raise ParserStructureError("Structured envelope must be a JSON object.")

        if envelope.get("binary") is True:
            return StructureParseOutput(sections=(), paragraphs=())

        format_name = envelope.get("format")

        if format_name == "HTML":
            return _parse_html_envelope_structure(
                envelope=envelope,
                document_id=document_id,
                source_id=source_id,
                artifact_id=artifact_id,
                content_hash=content_hash,
                parser_name=parser_name,
                parser_version=parser_version,
            )

        if format_name == "DOCX":
            return _parse_docx_envelope_structure(
                envelope=envelope,
                document_id=document_id,
                source_id=source_id,
                artifact_id=artifact_id,
                content_hash=content_hash,
                parser_name=parser_name,
                parser_version=parser_version,
            )

        if format_name in {"PDF", "PPTX", "XLSX"}:
            return StructureParseOutput(sections=(), paragraphs=())

        raise UnsupportedStructureError(
            f"Unsupported structured envelope format '{format_name}'."
        )

    return _parse_markdown_structure(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=parser_name,
        parser_version=parser_version,
    )
