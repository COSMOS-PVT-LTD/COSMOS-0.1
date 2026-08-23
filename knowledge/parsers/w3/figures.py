"""
Figure parsing (NEW KG-016).
"""

from __future__ import annotations

import json
import re

from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import LocationAnchor, ParsedFigure, ParseProvenance

__all__ = (
    "extract_figures",
)

_FIGURE_PATTERN = re.compile(
    r"!\[(?P<caption>[^\]]*)\]\((?P<reference>[^)]+)\)",
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


def _extract_markdown_figures(
    content: str,
    *,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ParsedFigure, ...]:
    figures: list[ParsedFigure] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        for match_index, match in enumerate(_FIGURE_PATTERN.finditer(line)):
            caption = match.group("caption").strip() or None
            reference = match.group("reference").strip()
            figure_id = deterministic_element_id(
                "fig",
                document_id,
                str(line_number),
                str(match_index),
                reference,
            )
            figures.append(
                ParsedFigure(
                    figure_id=figure_id,
                    provenance=_base_provenance(
                        source_id=source_id,
                        artifact_id=artifact_id,
                        content_hash=content_hash,
                        document_id=document_id,
                        parser_name=parser_name,
                        parser_version=parser_version,
                        location=LocationAnchor(line_number=line_number),
                    ),
                    caption=caption,
                    label=reference,
                    source_reference=reference,
                    ordering_index=len(figures) + 1,
                ),
            )

    return tuple(figures)


def _extract_html_envelope_figures(
    envelope: dict[str, object],
    *,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ParsedFigure, ...]:
    blocks = envelope.get("blocks")

    if not isinstance(blocks, list):
        return ()

    figures: list[ParsedFigure] = []

    for block_index, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue

        tag = block.get("tag")
        text = block.get("text")

        if tag != "figure" or not isinstance(text, str):
            continue

        figure_id = deterministic_element_id(
            "fig",
            document_id,
            str(block_index),
            text,
        )
        figures.append(
            ParsedFigure(
                figure_id=figure_id,
                provenance=_base_provenance(
                    source_id=source_id,
                    artifact_id=artifact_id,
                    content_hash=content_hash,
                    document_id=document_id,
                    parser_name=parser_name,
                    parser_version=parser_version,
                    location=LocationAnchor(block_index=block_index),
                ),
                caption=text,
                ordering_index=len(figures) + 1,
            ),
        )

    return tuple(figures)


def extract_figures(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
    is_structured_envelope: bool,
) -> tuple[ParsedFigure, ...]:
    """Extract figure metadata without semantic interpretation."""

    if not is_structured_envelope:
        return _extract_markdown_figures(
            content,
            document_id=document_id,
            source_id=source_id,
            artifact_id=artifact_id,
            content_hash=content_hash,
            parser_name=parser_name,
            parser_version=parser_version,
        )

    try:
        envelope = json.loads(content)
    except json.JSONDecodeError:
        return ()

    if not isinstance(envelope, dict) or envelope.get("format") != "HTML":
        return ()

    return _extract_html_envelope_figures(
        envelope,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=parser_name,
        parser_version=parser_version,
    )
