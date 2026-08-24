"""COSMOS-authored workspace golden fixtures. No third-party prose."""

from __future__ import annotations

import io
import json
import zipfile

__all__ = (
    "COOLING_NOTES_MARKDOWN",
    "CHAMBER_DATASET_CSV",
    "COMPONENT_JSON",
    "INTERNAL_NOTE_XML",
    "RIGHTS_BLOCKED_TEXT",
    "PNG_1X1",
    "chamber_csv_bytes",
    "component_json_bytes",
    "cooling_markdown_bytes",
    "internal_html_bytes",
    "internal_note_xml_bytes",
    "minimal_docx_bytes",
    "minimal_epub_bytes",
    "minimal_pptx_bytes",
    "minimal_xlsx_bytes",
    "png_1x1_bytes",
    "rights_blocked_bytes",
)

COOLING_NOTES_MARKDOWN = """# COSMOS Internal Cooling Notes

Regenerative cooling routes chamber coolant through wall channels.

The Bartz correlation is a candidate heat-transfer relation for throat-region convection.

Assumption: coolant remains single-phase in the channel for this note.

This document is COSMOS-authored qualification material. No third-party prose.
"""

CHAMBER_DATASET_CSV = """chamber_id,coolant,mass_flow (kg/s),pressure_mpa
CH-001,CH4,0.12,5.0
CH-002,CH4,0.18,6.5
"""

COMPONENT_JSON = json.dumps(
    [
        {"component": "injector", "orifice_count": "18"},
        {"component": "chamber", "orifice_count": "0"},
    ],
    indent=2,
)

INTERNAL_NOTE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<note>
  <title>COSMOS internal injector note</title>
  <body>Orifice count is recorded as source text only.</body>
</note>
"""

RIGHTS_BLOCKED_TEXT = "Restricted COSMOS-authored placeholder. Extraction must remain blocked.\n"

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)


def cooling_markdown_bytes() -> bytes:
    return COOLING_NOTES_MARKDOWN.encode("utf-8")


def chamber_csv_bytes() -> bytes:
    return CHAMBER_DATASET_CSV.encode("utf-8")


def component_json_bytes() -> bytes:
    return COMPONENT_JSON.encode("utf-8")


def internal_note_xml_bytes() -> bytes:
    return INTERNAL_NOTE_XML.encode("utf-8")


def rights_blocked_bytes() -> bytes:
    return RIGHTS_BLOCKED_TEXT.encode("utf-8")


def png_1x1_bytes() -> bytes:
    return PNG_1X1


def internal_html_bytes() -> bytes:
    return b"<html><body><h1>COSMOS internal HTML note</h1><p>Regenerative cooling note.</p></body></html>"


def minimal_docx_bytes(text: str = "COSMOS internal DOCX regenerative cooling note.") -> bytes:
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", document)
    return buffer.getvalue()


def minimal_pptx_bytes(text: str = "COSMOS internal PPTX cooling slide.") -> bytes:
    slide = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f"<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"
        "</p:spTree></p:cSld></p:sld>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide)
    return buffer.getvalue()


def minimal_xlsx_bytes() -> bytes:
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
        '<row r="1"><c r="A1" t="inlineStr"><is><t>component</t></is></c>'
        '<c r="B1" t="inlineStr"><is><t>value</t></is></c></row>'
        '<row r="2"><c r="A2" t="inlineStr"><is><t>chamber</t></is></c>'
        '<c r="B2" t="inlineStr"><is><t>5kN</t></is></c></row>'
        "</sheetData></worksheet>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("xl/worksheets/sheet1.xml", sheet)
    return buffer.getvalue()


def minimal_epub_bytes(text: str = "COSMOS internal EPUB regenerative cooling note.") -> bytes:
    html = f"<html><body><p>{text}</p></body></html>"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("OPS/content.xhtml", html)
    return buffer.getvalue()
