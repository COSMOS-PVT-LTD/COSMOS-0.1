"""
Table parsing (NEW KG-015).
"""

from __future__ import annotations

import json

from knowledge.parsers.w3.exceptions import ParserTableError
from knowledge.parsers.w3.identity import deterministic_element_id
from knowledge.parsers.w3.models import (
    LocationAnchor,
    ParsedTable,
    ParsedTableCell,
    ParsedTableRow,
    ParseProvenance,
)

__all__ = (
    "extract_tables",
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


def _parse_markdown_table_block(
    lines: list[str],
    *,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
    table_index: int,
    start_line: int,
) -> ParsedTable:
    rows: list[ParsedTableRow] = []
    column_count = 0

    for row_index, line in enumerate(lines):
        cells_raw = [cell.strip() for cell in line.strip().strip("|").split("|")]

        if row_index == 1 and all(set(cell) <= {"-", ":"} for cell in cells_raw):
            continue

        cells: list[ParsedTableCell] = []

        for column_index, value in enumerate(cells_raw):
            cells.append(
                ParsedTableCell(
                    column_index=column_index,
                    row_index=len(rows),
                    value=value,
                    is_header=row_index == 0,
                ),
            )

        column_count = max(column_count, len(cells))
        rows.append(ParsedTableRow(row_index=len(rows), cells=tuple(cells)))

    table_id = deterministic_element_id(
        "tbl",
        document_id,
        str(table_index),
        str(start_line),
    )

    return ParsedTable(
        table_id=table_id,
        provenance=_base_provenance(
            source_id=source_id,
            artifact_id=artifact_id,
            content_hash=content_hash,
            document_id=document_id,
            parser_name=parser_name,
            parser_version=parser_version,
            location=LocationAnchor(line_number=start_line),
        ),
        rows=tuple(rows),
        column_count=column_count,
        ordering_index=table_index,
    )


def _extract_markdown_tables(
    content: str,
    *,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ParsedTable, ...]:
    lines = content.splitlines()
    tables: list[ParsedTable] = []
    table_index = 0
    index = 0

    while index < len(lines):
        line = lines[index].strip()

        if line.startswith("|") and "|" in line[1:]:
            start_line = index + 1
            block: list[str] = []

            while index < len(lines) and lines[index].strip().startswith("|"):
                block.append(lines[index].strip())
                index += 1

            if len(block) >= 2:
                table_index += 1
                tables.append(
                    _parse_markdown_table_block(
                        block,
                        document_id=document_id,
                        source_id=source_id,
                        artifact_id=artifact_id,
                        content_hash=content_hash,
                        parser_name=parser_name,
                        parser_version=parser_version,
                        table_index=table_index,
                        start_line=start_line,
                    ),
                )

            continue

        index += 1

    return tuple(tables)


def _extract_xlsx_envelope_tables(
    envelope: dict[str, object],
    *,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
) -> tuple[ParsedTable, ...]:
    cells_raw = envelope.get("cells")

    if not isinstance(cells_raw, list):
        raise ParserTableError("XLSX envelope must include a cells list.")

    rows_by_index: dict[int, list[ParsedTableCell]] = {}

    for item in cells_raw:
        if not isinstance(item, dict):
            raise ParserTableError("XLSX cell entries must be mappings.")

        reference = item.get("cell")
        value = item.get("value")

        if not isinstance(reference, str) or not isinstance(value, str):
            raise ParserTableError("XLSX cells require cell reference and value.")

        row_index = 0
        column_index = 0

        for char in reference:
            if char.isalpha():
                column_index = column_index * 26 + (ord(char.upper()) - ord("A") + 1)
            elif char.isdigit():
                row_index = row_index * 10 + int(char)

        row_index = max(row_index - 1, 0)
        column_index = max(column_index - 1, 0)
        rows_by_index.setdefault(row_index, []).append(
            ParsedTableCell(
                column_index=column_index,
                row_index=row_index,
                value=value,
                is_header=row_index == 0,
            ),
        )

    rows: list[ParsedTableRow] = []
    column_count = 0

    for row_index in sorted(rows_by_index):
        cells = tuple(
            sorted(rows_by_index[row_index], key=lambda cell: cell.column_index),
        )
        column_count = max(column_count, len(cells))
        rows.append(ParsedTableRow(row_index=row_index, cells=cells))

    table_id = deterministic_element_id("tbl", document_id, "xlsx", "sheet1")

    return (
        ParsedTable(
            table_id=table_id,
            provenance=_base_provenance(
                source_id=source_id,
                artifact_id=artifact_id,
                content_hash=content_hash,
                document_id=document_id,
                parser_name=parser_name,
                parser_version=parser_version,
                location=None,
            ),
            rows=tuple(rows),
            column_count=column_count,
            ordering_index=1,
        ),
    )


def extract_tables(
    *,
    content: str,
    document_id: str,
    source_id: str,
    artifact_id: str,
    content_hash: str,
    parser_name: str,
    parser_version: str,
    is_structured_envelope: bool,
) -> tuple[ParsedTable, ...]:
    """Extract tables from markdown or structured envelopes."""

    if not is_structured_envelope:
        return _extract_markdown_tables(
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
    except json.JSONDecodeError as exc:
        raise ParserTableError("Structured envelope must be valid JSON.") from exc

    if not isinstance(envelope, dict):
        raise ParserTableError("Structured envelope must be a JSON object.")

    if envelope.get("format") == "XLSX":
        return _extract_xlsx_envelope_tables(
            envelope,
            document_id=document_id,
            source_id=source_id,
            artifact_id=artifact_id,
            content_hash=content_hash,
            parser_name=parser_name,
            parser_version=parser_version,
        )

    return ()
