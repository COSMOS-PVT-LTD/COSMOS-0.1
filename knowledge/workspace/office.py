"""Office and markup extraction used by the workspace pipeline.

Frozen ingestion adapters remain the registration contract. This module recovers
source-faithful text/cells for candidate generation without rewriting those adapters.
"""

from __future__ import annotations

from html.parser import HTMLParser
import io
import zipfile
from xml.etree import ElementTree

from knowledge.ingestion_adapters.exceptions import AdapterExecutionError

__all__ = (
    "extract_docx_text",
    "extract_epub_text",
    "extract_html_text",
    "extract_pptx_text",
    "extract_xlsx_cells",
)

_W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
_MAIN_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


class _HTMLTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.chunks.append(text)


def extract_docx_text(content: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("DOCX artifact is not a valid ZIP archive.") from exc
    try:
        document_xml = archive.read("word/document.xml")
    except KeyError as exc:
        raise AdapterExecutionError("DOCX artifact is missing word/document.xml.") from exc
    root = ElementTree.fromstring(document_xml)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{_W_NS}p"):
        texts = [node.text for node in paragraph.iter(f"{_W_NS}t") if node.text]
        if texts:
            paragraphs.append("".join(texts))
    return "\n".join(paragraphs)


def extract_pptx_text(content: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("PPTX artifact is not a valid ZIP archive.") from exc
    slide_names = sorted(
        name
        for name in archive.namelist()
        if name.startswith("ppt/slides/slide") and name.endswith(".xml")
    )
    blocks: list[str] = []
    for index, slide_name in enumerate(slide_names, start=1):
        root = ElementTree.fromstring(archive.read(slide_name))
        texts = [node.text.strip() for node in root.iter(f"{_A_NS}t") if node.text and node.text.strip()]
        if texts:
            blocks.append(f"Slide {index}")
            blocks.extend(texts)
    return "\n".join(blocks)


def extract_xlsx_cells(content: bytes) -> tuple[dict[str, str], ...]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("XLSX artifact is not a valid ZIP archive.") from exc
    shared_strings: list[str] = []
    if "xl/sharedStrings.xml" in archive.namelist():
        shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        shared_strings = [
            "".join(node.text or "" for node in item.iter(f"{_MAIN_NS}t"))
            for item in shared_root.iter(f"{_MAIN_NS}si")
        ]
    sheets = sorted(
        name
        for name in archive.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )
    if not sheets:
        raise AdapterExecutionError("XLSX artifact has no worksheets.")
    sheet_root = ElementTree.fromstring(archive.read(sheets[0]))
    cells: list[dict[str, str]] = []
    for cell in sheet_root.iter(f"{_MAIN_NS}c"):
        reference = cell.attrib.get("r")
        if reference is None:
            continue
        inline = cell.find(f"{_MAIN_NS}is")
        value_node = cell.find(f"{_MAIN_NS}v")
        value: str | None = None
        if inline is not None:
            value = "".join(node.text or "" for node in inline.iter(f"{_MAIN_NS}t"))
        elif value_node is not None and value_node.text is not None:
            value = value_node.text
            if cell.attrib.get("t") == "s":
                value = shared_strings[int(value)]
        if value is None:
            continue
        cells.append({"cell": reference, "value": value})
    return tuple(cells)


def extract_html_text(content: bytes) -> str:
    try:
        html = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdapterExecutionError("HTML artifact must be UTF-8 encoded.") from exc
    parser = _HTMLTextParser()
    parser.feed(html)
    parser.close()
    return "\n".join(parser.chunks)


def extract_epub_text(content: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile as exc:
        raise AdapterExecutionError("EPUB artifact is not a valid ZIP archive.") from exc
    names = [name for name in archive.namelist() if name.endswith((".xhtml", ".html", ".htm"))]
    if not names:
        raise AdapterExecutionError("EPUB archive contains no HTML documents.")
    return extract_html_text(archive.read(names[0]))
