"""COMPAT-001 — frozen ingestion loader facade tests."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from knowledge.ingestion.docx_loader import load_docx
from knowledge.ingestion.html_loader import load_html
from knowledge.ingestion.markdown_loader import load_markdown
from knowledge.ingestion.models import IngestionStage
from knowledge.ingestion.pdf_loader import load_pdf


def _minimal_docx_bytes(paragraph: str) -> bytes:
    buffer = io.BytesIO()
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body><w:p><w:r><w:t>"
        f"{paragraph}"
        "</w:t></w:r></w:p></w:body></w:document>"
    )

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", document_xml)

    return buffer.getvalue()


def test_load_markdown_delegates_to_canonical_adapter(tmp_path: Path) -> None:
    """load_markdown must ingest via MarkdownIngestionAdapter."""

    path = tmp_path / "sample.md"
    path.write_text("# Title\n\nBody line\n", encoding="utf-8")

    result = load_markdown(path, source_id="SRC-COMPAT", artifact_id="ART-COMPAT")

    assert result.stage is IngestionStage.NORMALIZED
    assert result.request.artifact.source_id == "SRC-COMPAT"
    assert result.request.artifact.artifact_id == "ART-COMPAT"
    assert len(result.normalized_content_hash) == 64


def test_load_pdf_delegates_without_fabricated_text(tmp_path: Path) -> None:
    """load_pdf must delegate to PdfIngestionAdapter without fake extraction."""

    path = tmp_path / "sample.pdf"
    path.write_bytes(b"%PDF-1.4\n%cosmos\n")

    result = load_pdf(path)

    assert result.stage is IngestionStage.NORMALIZED
    assert result.normalized_format.value == "STRUCTURED_TEXT"


def test_load_html_delegates_to_canonical_adapter(tmp_path: Path) -> None:
    """load_html must ingest via HtmlIngestionAdapter."""

    path = tmp_path / "sample.html"
    path.write_text("<html><body><p>Chamber Pressure</p></body></html>", encoding="utf-8")

    result = load_html(path)

    assert result.stage is IngestionStage.NORMALIZED
    assert len(result.normalized_content_hash) == 64


def test_load_docx_delegates_to_canonical_adapter(tmp_path: Path) -> None:
    """load_docx must ingest via DocxIngestionAdapter."""

    path = tmp_path / "sample.docx"
    path.write_bytes(_minimal_docx_bytes("Operating pressure"))

    result = load_docx(path)

    assert result.stage is IngestionStage.NORMALIZED
    assert len(result.normalized_content_hash) == 64


def test_load_markdown_missing_file_raises() -> None:
    """Compatibility loaders must surface missing-file errors."""

    with pytest.raises(FileNotFoundError):
        load_markdown("/nonexistent/path/sample.md")
