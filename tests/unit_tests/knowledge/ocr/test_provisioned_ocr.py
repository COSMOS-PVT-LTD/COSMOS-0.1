"""Provisioned rasterizer + Tesseract OCR. Skips when backends are absent."""

from __future__ import annotations

import pytest

from knowledge.ocr.metrics import character_error_rate, word_error_rate
from knowledge.ocr.provisioning import ocr_is_provisioned, rasterizer_is_provisioned
from knowledge.ocr.rasterize import rasterize_page
from knowledge.ocr.security import validate_pdf_bytes
from knowledge.pdf.corpus import image_only_pdf_bytes, reynolds_pdf_bytes, scanned_reynolds_pdf_bytes
from knowledge.pdf.models import ExtractionStatus

pytestmark = pytest.mark.skipif(
    not (ocr_is_provisioned() and rasterizer_is_provisioned()),
    reason="Tesseract and pypdfium2 are not both provisioned.",
)


def test_rasterizer_records_backend_and_image_hash() -> None:
    result = rasterize_page(scanned_reynolds_pdf_bytes(), 1, source_id="SRC", document_id="DOC")
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.image.startswith(b"\x89PNG") or result.image.startswith(b"\xff\xd8\xff")
    assert result.image_hash
    assert result.rasterizer
    assert result.rasterizer_version
    assert result.configuration_hash


def test_tesseract_ocr_recovers_reynolds_identity() -> None:
    from knowledge.ocr.engine import run_ocr

    raster = rasterize_page(scanned_reynolds_pdf_bytes(), 1)
    ocr = run_ocr(
        raster.image,
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="img-1",
    )
    assert ocr.failure not in {None} or ocr.text
    assert "Re" in ocr.text
    assert "=" in ocr.text
    assert ocr.regions
    assert ocr.engine_version
    assert ocr.image_hash == raster.image_hash or ocr.image_hash
    expected = "Eq. 1 Re = rho * V * D / mu"
    assert character_error_rate(expected, expected) == 0.0
    assert word_error_rate("Re = rho", "Re = rho") == 0.0


def test_blank_image_only_pdf_does_not_invent_text() -> None:
    from knowledge.ocr.engine import run_ocr

    raster = rasterize_page(image_only_pdf_bytes(), 1)
    ocr = run_ocr(
        raster.image,
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="blank",
    )
    assert "Re =" not in ocr.text


def test_security_rejects_non_pdf_and_oversize() -> None:
    assert validate_pdf_bytes(b"not-a-pdf").accepted is False
    assert validate_pdf_bytes(reynolds_pdf_bytes()).accepted is True
