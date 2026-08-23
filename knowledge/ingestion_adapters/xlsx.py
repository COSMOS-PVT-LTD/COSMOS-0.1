"""XLSX ingestion adapter (NEW KG-011)."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile

from knowledge.ingestion.models import (
    IngestionRequest,
    IngestionResult,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.base import VaultBackedAdapter
from knowledge.ingestion_adapters.exceptions import AdapterExecutionError
from knowledge.ingestion_adapters.normalize import build_structured_text_envelope
from knowledge.source.vault import SourceVault

__all__ = ("XlsxIngestionAdapter",)

_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _extract_xlsx_cells(content: bytes) -> tuple[dict[str, object], ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("XLSX artifact is not a valid ZIP archive.") from exc

    shared_strings: list[str] = []

    if "xl/sharedStrings.xml" in archive.namelist():
        shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(
                node.text or ""
                for node in item.iter(f"{_MAIN_NS}t")
            )
            for item in shared_root.iter(f"{_MAIN_NS}si")
        ]

    sheet_name = sorted(
        name
        for name in archive.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )[0]

    sheet_root = ET.fromstring(archive.read(sheet_name))
    cells: list[dict[str, object]] = []

    for cell in sheet_root.iter(f"{_MAIN_NS}c"):
        reference = cell.attrib.get("r")
        cell_type = cell.attrib.get("t")
        value_node = cell.find(f"{_MAIN_NS}v")

        if reference is None or value_node is None or value_node.text is None:
            continue

        value: str = value_node.text

        if cell_type == "s":
            value = shared_strings[int(value)]

        cells.append({"cell": reference, "value": value})

    return tuple(cells)


class XlsxIngestionAdapter(VaultBackedAdapter):
    """XLSX ingestion preserving worksheet cell values without formula execution."""

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-xlsx-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.XLSX}),
            parser_version="cosmos-xlsx-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.XLSX)

        cells = _extract_xlsx_cells(content)
        envelope = build_structured_text_envelope(
            {
                "cells": list(cells),
                "format": "XLSX",
            },
        )

        return self._build_result(
            request,
            envelope,
            normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
        )
