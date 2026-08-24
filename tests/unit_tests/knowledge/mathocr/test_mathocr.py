"""Math-OCR adapter — fail closed, never auto-approves."""

from __future__ import annotations

from knowledge.mathocr import MathOCRFailure, UnavailableMathOCRAdapter, run_math_ocr, select_math_ocr_adapter
from knowledge.mathocr.tesseract_math import tesseract_math_is_provisioned


def test_unavailable_math_ocr_does_not_invent() -> None:
    result = UnavailableMathOCRAdapter().extract(
        b"not-an-image",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        region_id="r1",
        source_text="Re = rho * V * D / mu",
    )
    assert result.source_representation == ""
    assert result.latex is None
    assert result.failure is MathOCRFailure.MATH_OCR_UNAVAILABLE


def test_empty_image_is_corrupt_or_unavailable() -> None:
    result = UnavailableMathOCRAdapter().extract(
        b"",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        region_id="r1",
    )
    assert result.failure in {MathOCRFailure.CORRUPT_IMAGE, MathOCRFailure.MATH_OCR_UNAVAILABLE}
    assert result.latex is None


def test_tesseract_span_reconstructs_from_source_text_when_provisioned() -> None:
    if not tesseract_math_is_provisioned():
        result = run_math_ocr(
            b"",
            source_id="SRC",
            document_id="DOC",
            page_number=1,
            region_id="eq-1",
            source_text="Re = (rho * V * D) / mu",
        )
        assert result.failure is MathOCRFailure.MATH_OCR_UNAVAILABLE
        return
    result = run_math_ocr(
        b"",
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        region_id="eq-1",
        source_text="Re = (rho * V * D) / mu",
    )
    assert result.failure is None
    assert result.source_representation == "Re = (rho * V * D) / mu"
    assert result.latex is not None
    assert result.backend.startswith("cosmos-mathocr-tesseract")
    adapter = select_math_ocr_adapter()
    assert adapter.adapter_name != "cosmos-mathocr-unavailable"
