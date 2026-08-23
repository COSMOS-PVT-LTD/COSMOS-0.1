"""
Reference and citation parsing (NEW KG-018).
"""

from __future__ import annotations

import re

from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import (
    CitationOccurrence,
    LocationAnchor,
    ParseProvenance,
    ReferenceRecord,
)

__all__ = (
    "extract_citations",
    "extract_references",
)

_CITATION_PATTERN = re.compile(r"\[(?P<key>[^\]]+)\]")
_REFERENCE_LINE_PATTERN = re.compile(
    r"^(?P<index>\d+)\.\s+(?P<body>.+)$",
)


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


def extract_citations(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
    reference_ids_by_key: dict[str, str] | None = None,
) -> tuple[CitationOccurrence, ...]:
    """Extract in-document citation occurrences."""

    citations: list[CitationOccurrence] = []
    reference_ids_by_key = reference_ids_by_key or {}

    for line_number, line in enumerate(content.splitlines(), start=1):
        for match_index, match in enumerate(_CITATION_PATTERN.finditer(line)):
            end = match.end()

            if end < len(line) and line[end] == "(":
                continue

            key = match.group("key").strip()
            citation_id = deterministic_element_id(
                "cite",
                document_id,
                str(line_number),
                str(match_index),
                key,
            )
            reference_id = reference_ids_by_key.get(key)

            citations.append(
                CitationOccurrence(
                    citation_id=citation_id,
                    provenance=_base_provenance(
                        source_id=source_id,
                        artifact_id=artifact_id,
                        content_hash=content_hash,
                        document_id=document_id,
                        parser_name=parser_name,
                        parser_version=parser_version,
                        location=LocationAnchor(line_number=line_number),
                    ),
                    reference_id=reference_id,
                    citation_key=key if reference_id is None else None,
                    ordering_index=len(citations) + 1,
                ),
            )

    return tuple(citations)


def extract_references(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ReferenceRecord, ...]:
    """Extract bibliography reference records from a references section."""

    references: list[ReferenceRecord] = []
    in_references = False

    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()

        if line.lower() in {"# references", "## references"}:
            in_references = True
            continue

        if not in_references or not line:
            continue

        match = _REFERENCE_LINE_PATTERN.match(line)

        if match is None:
            continue

        index = match.group("index")
        body = match.group("body").strip()
        reference_id = deterministic_element_id(
            "ref",
            document_id,
            index,
            body,
        )
        title = body
        authors: str | None = None
        year: str | None = None

        if "(" in body and body.endswith(")"):
            title_part, _, remainder = body.rpartition("(")
            title = title_part.strip().rstrip(",")
            year = remainder.removesuffix(")").strip() or None

        references.append(
            ReferenceRecord(
                reference_id=reference_id,
                provenance=_base_provenance(
                    source_id=source_id,
                    artifact_id=artifact_id,
                    content_hash=content_hash,
                    document_id=document_id,
                    parser_name=parser_name,
                    parser_version=parser_version,
                    location=LocationAnchor(line_number=line_number),
                ),
                ordering_index=len(references) + 1,
                title=title or None,
                authors=authors,
                year=year,
                raw_metadata=body,
            ),
        )

    return tuple(references)
