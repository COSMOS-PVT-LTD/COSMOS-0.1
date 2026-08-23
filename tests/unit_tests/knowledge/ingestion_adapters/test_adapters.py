"""Unit tests for knowledge.ingestion_adapters (KG-BLOCK-005 W2)."""

from __future__ import annotations

import io
import zipfile

import pytest

from knowledge.ingestion.models import IngestionArtifactRef, IngestionRequest, SourceFormat
from knowledge.ingestion_adapters import (
    DocxIngestionAdapter,
    HtmlIngestionAdapter,
    IngestionOrchestrator,
    MarkdownIngestionAdapter,
    PdfIngestionAdapter,
    PptxIngestionAdapter,
    RepositoryBoundaryError,
    RepositoryIngestionAdapter,
    RepositoryIngestionConfig,
    XlsxIngestionAdapter,
    build_default_registry,
)
from knowledge.source import InMemorySourceVault, VaultArtifact, sha256_bytes_digest


def _store(
    vault: InMemorySourceVault,
    *,
    source_id: str,
    artifact_id: str,
    content: bytes,
    source_format: SourceFormat,
) -> IngestionArtifactRef:
    digest = sha256_bytes_digest(content)
    vault.store(
        VaultArtifact(
            source_id=source_id,
            artifact_id=artifact_id,
            content=content,
            content_hash=digest,
            metadata=__import__(
                "knowledge.source.vault",
                fromlist=["VaultArtifactMetadata"],
            ).VaultArtifactMetadata(source_format=source_format.value),
        ),
    )

    return IngestionArtifactRef(
        source_id=source_id,
        artifact_id=artifact_id,
        source_format=source_format,
        content_hash=digest,
    )


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


def _minimal_pptx_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    slide_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f'<p:sp><a:t>{text}</a:t></p:sp></p:sld>'
    )

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("ppt/slides/slide1.xml", slide_xml)

    return buffer.getvalue()


def _minimal_xlsx_bytes(cell_value: str) -> bytes:
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData><row r="1"><c r="A1"><v>'
                f"{cell_value}"
                "</v></c></row></sheetData></worksheet>"
            ),
        )

    return buffer.getvalue()


def test_pdf_adapter_marks_binary_pdf_without_fake_text() -> None:
    """Binary PDF ingestion must not fabricate extracted text."""

    vault = InMemorySourceVault()
    content = b"%PDF-1.4\n%cosmos\n"
    artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-PDF",
        content=content,
        source_format=SourceFormat.PDF,
    )
    adapter = PdfIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )

    result = adapter.ingest(request)

    assert result.normalized_format.value == "STRUCTURED_TEXT"
    assert len(result.normalized_content_hash) == 64


def test_markdown_adapter_normalizes_text() -> None:
    """Markdown ingestion must normalize line endings deterministically."""

    vault = InMemorySourceVault()
    content = b"# Title\r\n\r\nBody\r\n"
    artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-MD",
        content=content,
        source_format=SourceFormat.MARKDOWN,
    )
    adapter = MarkdownIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )

    first = adapter.ingest(request)
    second = adapter.ingest(request)

    assert first.normalized_content_hash == second.normalized_content_hash


def test_docx_adapter_extracts_paragraphs() -> None:
    """DOCX ingestion must preserve paragraph text."""

    vault = InMemorySourceVault()
    content = _minimal_docx_bytes("Chamber Pressure")
    artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-DOCX",
        content=content,
        source_format=SourceFormat.DOCX,
    )
    adapter = DocxIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )

    result = adapter.ingest(request)

    assert result.stage.value == "NORMALIZED"


def test_html_adapter_preserves_blocks() -> None:
    """HTML ingestion must preserve structural blocks."""

    vault = InMemorySourceVault()
    content = b"<html><body><h1>Title</h1><p>Body</p></body></html>"
    artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-HTML",
        content=content,
        source_format=SourceFormat.HTML,
    )
    adapter = HtmlIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )

    result = adapter.ingest(request)

    assert result.normalized_format.value == "STRUCTURED_TEXT"


def test_orchestrator_auto_dispatch_is_deterministic() -> None:
    """Auto dispatch must select the same adapter for repeated calls."""

    vault = InMemorySourceVault()
    content = b"# Deterministic\n"
    artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-MD",
        content=content,
        source_format=SourceFormat.MARKDOWN,
    )
    orchestrator = IngestionOrchestrator(build_default_registry(vault))

    first = orchestrator.ingest_auto(artifact)
    second = orchestrator.ingest_auto(artifact)

    assert first.normalized_content_hash == second.normalized_content_hash


def test_repository_ingestion_is_bounded(tmp_path) -> None:
    """Repository ingestion must respect include/exclude rules and bounds."""

    (tmp_path / "notes.md").write_text("# Note", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=1", encoding="utf-8")

    vault = InMemorySourceVault()
    adapter = RepositoryIngestionAdapter(
        vault,
        RepositoryIngestionConfig(
            root_path=str(tmp_path),
            source_id="SRC-REPO",
            include_globs=("*.md",),
        ),
    )

    result = adapter.ingest_repository()

    assert result.file_count == 1
    assert result.artifact_ids == ("notes.md",)
    assert vault.exists("SRC-REPO", "notes.md")
    assert not vault.exists("SRC-REPO", ".env")


def test_repository_ingestion_enforces_max_files(tmp_path) -> None:
    """Repository ingestion must fail when max_files is exceeded."""

    for index in range(3):
        (tmp_path / f"file{index}.md").write_text("x", encoding="utf-8")

    vault = InMemorySourceVault()
    adapter = RepositoryIngestionAdapter(
        vault,
        RepositoryIngestionConfig(
            root_path=str(tmp_path),
            source_id="SRC-REPO",
            include_globs=("*.md",),
            max_files=2,
        ),
    )

    with pytest.raises(RepositoryBoundaryError):
        adapter.ingest_repository()


def test_pptx_and_xlsx_adapters_normalize_structure() -> None:
    """PPTX and XLSX adapters must produce normalized structured output."""

    vault = InMemorySourceVault()

    pptx_artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-PPTX",
        content=_minimal_pptx_bytes("Slide Title"),
        source_format=SourceFormat.PPTX,
    )
    xlsx_artifact = _store(
        vault,
        source_id="SRC-001",
        artifact_id="ART-XLSX",
        content=_minimal_xlsx_bytes("100"),
        source_format=SourceFormat.XLSX,
    )

    pptx_result = PptxIngestionAdapter(vault).ingest(
        IngestionRequest(
            artifact=pptx_artifact,
            adapter_name="cosmos-pptx-ingestion",
            adapter_version="0.1.0",
        ),
    )
    xlsx_result = XlsxIngestionAdapter(vault).ingest(
        IngestionRequest(
            artifact=xlsx_artifact,
            adapter_name="cosmos-xlsx-ingestion",
            adapter_version="0.1.0",
        ),
    )

    assert pptx_result.normalized_format.value == "STRUCTURED_TEXT"
    assert xlsx_result.normalized_format.value == "STRUCTURED_TEXT"
