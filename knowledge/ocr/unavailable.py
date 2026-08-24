"""Fail-closed OCR adapter — never invents text."""

from __future__ import annotations

from datetime import datetime, timezone

from knowledge.ocr.models import OCRFailure, OCRResult

__all__ = ("UnavailableOCRAdapter", "OCRUnavailableError")


class OCRUnavailableError(RuntimeError):
    """OCR was requested but no engine is provisioned."""


class UnavailableOCRAdapter:
    adapter_name = "cosmos-ocr-unavailable"
    adapter_version = "1.0.0"

    def supports(self, image: bytes) -> bool:
        return False

    def available(self) -> bool:
        return False

    def extract(
        self,
        image: bytes,
        *,
        source_id: str,
        document_id: str,
        page_number: int,
        image_id: str,
    ) -> OCRResult:
        if not image:
            failure = OCRFailure.NO_IMAGE
        else:
            failure = OCRFailure.OCR_UNAVAILABLE
        return OCRResult(
            document_id=document_id,
            source_id=source_id,
            page_number=page_number,
            image_id=image_id,
            text="",
            confidence=0.0,
            language="und",
            regions=(),
            processing_method="unavailable",
            adapter_name=self.adapter_name,
            adapter_version=self.adapter_version,
            timestamp=datetime.now(timezone.utc).isoformat(),
            failure=failure,
            configuration=("engine=none",),
        )
