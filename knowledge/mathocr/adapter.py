"""Replaceable math-OCR adapter protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.mathocr.models import MathOCRResult
from knowledge.mathocr.tesseract_math import TesseractMathOCRAdapter, tesseract_math_is_provisioned
from knowledge.mathocr.unavailable import UnavailableMathOCRAdapter

__all__ = ("MathOCRAdapter", "select_math_ocr_adapter")


@runtime_checkable
class MathOCRAdapter(Protocol):
    adapter_name: str
    adapter_version: str

    def supports(self, image: bytes) -> bool: ...

    def extract(
        self,
        image: bytes,
        *,
        source_id: str,
        document_id: str,
        page_number: int,
        region_id: str,
        source_text: str = "",
    ) -> MathOCRResult: ...


def select_math_ocr_adapter() -> MathOCRAdapter:
    if tesseract_math_is_provisioned():
        return TesseractMathOCRAdapter()
    return UnavailableMathOCRAdapter()
