"""OCR adapter protocol — backends are interchangeable."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.ocr.models import OCRResult
from knowledge.ocr.tesseract import TesseractOCRAdapter, tesseract_is_provisioned
from knowledge.ocr.unavailable import UnavailableOCRAdapter

__all__ = ("OCRAdapter", "select_ocr_adapter")


@runtime_checkable
class OCRAdapter(Protocol):
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
        image_id: str,
    ) -> OCRResult: ...


def select_ocr_adapter() -> OCRAdapter:
    """Return a provisioned OCR backend, or the fail-closed unavailable adapter."""

    if tesseract_is_provisioned():
        return TesseractOCRAdapter()
    return UnavailableOCRAdapter()
