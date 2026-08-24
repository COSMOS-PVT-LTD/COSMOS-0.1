"""OCR / image layer — fail closed, hash evidence, no fabricated text."""

from __future__ import annotations

from knowledge.ocr import (
    OCRFailure,
    UnavailableOCRAdapter,
    UnavailableRasterizer,
    hash_image,
    preprocess_record,
    run_ocr,
)
from knowledge.ocr.config import RasterConfiguration
from knowledge.pdf.corpus import image_only_pdf_bytes, reynolds_pdf_bytes
from knowledge.ocr.security import validate_pdf_bytes
from knowledge.pdf.models import ExtractionStatus


def test_unavailable_adapter_never_invents_text() -> None:
    adapter = UnavailableOCRAdapter()
    result = adapter.extract(
        b"not-an-image",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="img-1",
    )
    assert result.text == ""
    assert result.confidence == 0.0
    assert result.failure is OCRFailure.OCR_UNAVAILABLE


def test_empty_image_is_no_image() -> None:
    result = run_ocr(
        b"",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="img-empty",
    )
    assert result.text == ""
    assert result.failure in {OCRFailure.NO_IMAGE, OCRFailure.OCR_UNAVAILABLE}


def test_invalid_bytes_are_not_treated_as_ocr_text() -> None:
    result = run_ocr(b"abc", source_id="SRC", document_id="DOC", page_number=1, image_id="img-2")
    assert result.text == ""
    assert result.failure is not None


def test_unavailable_rasterizer_never_invents_image() -> None:
    result = UnavailableRasterizer().rasterize_page(
        image_only_pdf_bytes(),
        1,
        RasterConfiguration(),
    )
    assert result.status is ExtractionStatus.EXTRACTION_UNAVAILABLE
    assert result.image == b""
    assert result.warning


def test_image_hash_is_deterministic() -> None:
    try:
        from PIL import Image
    except Exception:
        payload = b"\x89PNG\r\n\x1a\ncosmos-original"
        assert hash_image(payload) == hash_image(payload)
        return
    import io

    buffer = io.BytesIO()
    Image.new("L", (8, 8), color=128).save(buffer, format="PNG")
    payload = buffer.getvalue()
    assert hash_image(payload) == hash_image(payload)
    record = preprocess_record(payload, operations=("binarize",))
    assert record.original_hash == hash_image(payload)
    assert record.processed_hash == record.original_hash


def test_security_rejects_non_pdf() -> None:
    finding = validate_pdf_bytes(b"not-a-pdf")
    assert finding.accepted is False
    assert finding.status is ExtractionStatus.CORRUPT_SOURCE
    assert validate_pdf_bytes(reynolds_pdf_bytes()).accepted is True


def test_native_pdf_pipeline_does_not_replace_text_with_ocr() -> None:
    from knowledge.foundation import KnowledgeFoundationService

    service = KnowledgeFoundationService()
    result = service.ingest_real_pdf(
        reynolds_pdf_bytes(),
        source_id="SRC-NATIVE-OCR",
        document_id="DOC-NATIVE-OCR",
        title="native",
        filename="native.pdf",
        reference_id="REF-NATIVE-OCR",
    )
    assert "Re = rho * V * D / mu" in result.recovered_text
    assert result.extraction is not None
    assert "ocr" not in result.extraction.method or "+ocr" in result.extraction.method
    assert result.ocr_results == ()
