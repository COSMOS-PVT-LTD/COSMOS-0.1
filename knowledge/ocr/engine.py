"""OCR orchestration — fail closed, never invents text."""

from __future__ import annotations

from knowledge.ocr.adapter import OCRAdapter, select_ocr_adapter
from knowledge.ocr.cache import OCRCache
from knowledge.ocr.models import OCRFailure, OCRResult

__all__ = ("TERMINAL_OCR_FAILURES", "run_ocr")

TERMINAL_OCR_FAILURES = frozenset(
    {
        OCRFailure.NO_IMAGE,
        OCRFailure.IMAGE_UNREADABLE,
        OCRFailure.OCR_UNAVAILABLE,
        OCRFailure.OCR_FAILED,
        OCRFailure.UNSUPPORTED_FORMAT,
        OCRFailure.CORRUPT_SOURCE,
    },
)


def run_ocr(
    image: bytes,
    *,
    source_id: str,
    document_id: str,
    page_number: int,
    image_id: str,
    adapter: OCRAdapter | None = None,
    cache: OCRCache | None = None,
) -> OCRResult:
    if cache is not None:
        cached = cache.get(image)
        if cached is not None:
            return cached
    selected = adapter or select_ocr_adapter()
    result = selected.extract(
        image,
        source_id=source_id,
        document_id=document_id,
        page_number=page_number,
        image_id=image_id,
    )
    if result.failure is None and not result.text.strip():
        result = OCRResult(
            document_id=result.document_id,
            source_id=result.source_id,
            page_number=result.page_number,
            image_id=result.image_id,
            text="",
            confidence=0.0,
            language=result.language,
            regions=(),
            processing_method=result.processing_method,
            adapter_name=result.adapter_name,
            adapter_version=result.adapter_version,
            timestamp=result.timestamp,
            failure=OCRFailure.OCR_FAILED,
            configuration=result.configuration,
            image_hash=result.image_hash,
            engine_version=result.engine_version,
            token_confidences=result.token_confidences,
        )
    if cache is not None:
        cache.put(image, result)
    return result
