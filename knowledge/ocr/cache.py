"""Hash-addressed OCR cache. Empty or failed results are not reused as text."""

from __future__ import annotations

from knowledge.ocr.images import hash_image
from knowledge.ocr.models import OCRFailure, OCRResult

__all__ = ("OCRCache",)


class OCRCache:
    def __init__(self) -> None:
        self._store: dict[str, OCRResult] = {}

    def get(self, image: bytes) -> OCRResult | None:
        if not image:
            return None
        return self._store.get(hash_image(image))

    def put(self, image: bytes, result: OCRResult) -> None:
        if not image or result.failure is OCRFailure.OCR_UNAVAILABLE:
            return
        self._store[hash_image(image)] = result
