"""Math-OCR orchestration — fail closed."""

from __future__ import annotations

from knowledge.mathocr.adapter import MathOCRAdapter, select_math_ocr_adapter
from knowledge.mathocr.models import MathOCRResult

__all__ = ("run_math_ocr",)


def run_math_ocr(
    image: bytes,
    *,
    source_id: str,
    document_id: str,
    page_number: int,
    region_id: str,
    source_text: str = "",
    adapter: MathOCRAdapter | None = None,
) -> MathOCRResult:
    selected = adapter or select_math_ocr_adapter()
    return selected.extract(
        image,
        source_id=source_id,
        document_id=document_id,
        page_number=page_number,
        region_id=region_id,
        source_text=source_text,
    )
