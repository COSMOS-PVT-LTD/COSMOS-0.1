"""Structured dataset extraction. Units are never invented."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import json
import re
from xml.etree import ElementTree

__all__ = (
    "DatasetCandidate",
    "DatasetColumn",
    "extract_csv_dataset",
    "extract_json_dataset",
    "extract_xml_text",
)

_UNIT_HEADER = re.compile(r"^(?P<name>.+?)\s*\((?P<unit>[^)]+)\)\s*$")


@dataclass(frozen=True, slots=True, kw_only=True)
class DatasetColumn:
    name: str
    unit: str | None
    declared: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class DatasetCandidate:
    dataset_id: str
    schema: tuple[DatasetColumn, ...]
    rows: tuple[tuple[str, ...], ...]
    provenance_source_id: str
    warnings: tuple[str, ...] = ()

    @property
    def row_count(self) -> int:
        return len(self.rows)


def extract_csv_dataset(content: bytes, *, source_id: str, dataset_id: str) -> DatasetCandidate:
    text = _decode_text(content)
    reader = csv.reader(io.StringIO(text))
    rows = tuple(tuple(cell.strip() for cell in row) for row in reader if any(cell.strip() for cell in row))
    if not rows:
        raise ValueError("CSV artifact has no rows.")
    headers = rows[0]
    data_rows = rows[1:]
    schema = tuple(_column_from_header(header) for header in headers)
    normalized: list[tuple[str, ...]] = []
    warnings: list[str] = []
    width = len(headers)
    for index, row in enumerate(data_rows, start=2):
        if len(row) != width:
            warnings.append(f"Row {index} column count {len(row)} does not match header width {width}.")
            continue
        normalized.append(row)
    return DatasetCandidate(
        dataset_id=dataset_id,
        schema=schema,
        rows=tuple(normalized),
        provenance_source_id=source_id,
        warnings=tuple(warnings),
    )


def extract_json_dataset(content: bytes, *, source_id: str, dataset_id: str) -> DatasetCandidate | None:
    try:
        payload = json.loads(_decode_text(content))
    except json.JSONDecodeError as exc:
        raise ValueError("JSON artifact is not valid JSON.") from exc
    if not isinstance(payload, list) or not payload or not all(isinstance(item, dict) for item in payload):
        return None
    keys: list[str] = []
    seen: set[str] = set()
    for item in payload:
        for key in item:
            if key not in seen:
                seen.add(key)
                keys.append(str(key))
    schema = tuple(_column_from_header(key) for key in keys)
    rows = tuple(tuple(_stringify(item.get(key)) for key in keys) for item in payload)
    return DatasetCandidate(
        dataset_id=dataset_id,
        schema=schema,
        rows=rows,
        provenance_source_id=source_id,
    )


def extract_xml_text(content: bytes) -> str:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError("XML artifact is not well-formed.") from exc
    texts = [text.strip() for text in root.itertext() if text and text.strip()]
    return "\n".join(texts)


def _column_from_header(header: str) -> DatasetColumn:
    cleaned = header.strip()
    match = _UNIT_HEADER.match(cleaned)
    if match:
        return DatasetColumn(name=match.group("name").strip(), unit=match.group("unit").strip(), declared=True)
    return DatasetColumn(name=cleaned, unit=None, declared=False)


def _decode_text(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Text artifact must be UTF-8.") from exc


def _stringify(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
