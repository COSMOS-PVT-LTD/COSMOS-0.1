"""RF-001..013 / RF-020..022 — source registry and native PDF extraction."""

from __future__ import annotations

from knowledge.pdf import (
    DuplicateKind,
    ExtractionStatus,
    PageClassification,
    SourceModifiedError,
    SourceRegistry,
    extract_document_structure,
    extract_pdf_pages,
    write_extractable_pdf,
)
from knowledge.pdf.corpus import (
    image_only_pdf_bytes,
    mixed_reynolds_pdf_bytes,
    reynolds_pdf_bytes,
)
from knowledge.source.integrity import sha256_bytes_digest


def test_rf001_source_registration_and_rf002_hash() -> None:
    content = reynolds_pdf_bytes()
    digest = sha256_bytes_digest(content)
    registry = SourceRegistry()
    record = registry.register(
        content,
        source_id="SRC-COSMOS-RE-001",
        document_id="DOC-COSMOS-RE-001",
        title="COSMOS Reynolds qualification original",
        filename="reynolds_identities.pdf",
        author="COSMOS",
    )
    assert record.file_hash == digest == record.content_hash
    assert record.media_type == "application/pdf"
    assert record.file_size == len(content)
    assert record.duplicate_kind is DuplicateKind.NONE
    assert sha256_bytes_digest(content + b"x") != digest


def test_rf003_duplicate_and_modified_source() -> None:
    content = reynolds_pdf_bytes()
    registry = SourceRegistry()
    registry.register(
        content,
        source_id="SRC-A",
        document_id="DOC-A",
        title="Same title",
        filename="a.pdf",
        edition="1",
    )
    exact = registry.register(
        content,
        source_id="SRC-B",
        document_id="DOC-B",
        title="Same title",
        filename="a.pdf",
    )
    renamed = registry.register(
        content,
        source_id="SRC-C",
        document_id="DOC-C",
        title="Same title",
        filename="b.pdf",
    )
    edition = registry.register(
        write_extractable_pdf((("edition two",),)),
        source_id="SRC-D",
        document_id="DOC-D",
        title="Same title",
        filename="d.pdf",
        edition="2",
    )
    assert exact.duplicate_kind is DuplicateKind.EXACT_DUPLICATE
    assert renamed.duplicate_kind is DuplicateKind.SAME_CONTENT_DIFFERENT_FILENAME
    assert edition.duplicate_kind is DuplicateKind.DIFFERENT_EDITION
    try:
        registry.register(
            write_extractable_pdf((("changed",),)),
            source_id="SRC-A",
            document_id="DOC-A2",
            title="Same title",
            filename="a2.pdf",
        )
        raise AssertionError("modified source must not replace silently")
    except SourceModifiedError:
        pass


def test_rf010_native_text_and_rf013_diagnostics() -> None:
    content = reynolds_pdf_bytes()
    result = extract_pdf_pages(content, source_id="SRC-RE", document_id="DOC-RE")
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.diagnostics.page_count == 1
    assert result.diagnostics.pages_with_text == 1
    assert result.diagnostics.pages_with_equation_candidates == 1
    assert "Re = rho * V * D / mu" in result.pages[0].text
    assert result.pages[0].classification in {
        PageClassification.NATIVE_TEXT,
        PageClassification.LOW_TEXT_DENSITY,
    }


def test_rf011_image_only_is_unavailable() -> None:
    result = extract_pdf_pages(image_only_pdf_bytes(), source_id="SRC-IMG", document_id="DOC-IMG")
    assert result.status is ExtractionStatus.EXTRACTION_UNAVAILABLE
    assert result.pages[0].text == ""
    assert result.diagnostics.pages_with_text == 0


def test_rf012_mixed_pdf_page_methods() -> None:
    result = extract_pdf_pages(mixed_reynolds_pdf_bytes(), source_id="SRC-MIX", document_id="DOC-MIX")
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.diagnostics.pages_with_text >= 1
    if result.method == "pypdf":
        assert result.diagnostics.page_count >= 1
    else:
        assert result.diagnostics.page_count == 2
    assert result.pages[0].text
    if len(result.pages) > 1:
        assert result.pages[1].text == ""


def test_rf020_021_022_structure_from_recovered_text() -> None:
    result = extract_pdf_pages(reynolds_pdf_bytes(), source_id="SRC-RE", document_id="DOC-RE")
    structure = extract_document_structure(
        result.pages,
        document_id="DOC-RE",
        reference_id="REF-COSMOS-RE",
    )
    assert any(node.title.startswith("Chapter") for node in structure.headings)
    assert any("1.1" in node.title for node in structure.headings)
    assert structure.paragraphs
    assert any("Figure" in node.text for node in structure.captions if node.text)
    assert any("Table" in node.text for node in structure.captions if node.text)
    assert structure.equation_labels


def test_hash_mismatch_status() -> None:
    content = reynolds_pdf_bytes()
    other = sha256_bytes_digest(b"%PDF-not-this")
    result = extract_pdf_pages(
        content,
        source_id="SRC-RE",
        document_id="DOC-RE",
        expected_hash=other,
    )
    assert result.status is ExtractionStatus.HASH_MISMATCH
    assert not result.pages[0].text
