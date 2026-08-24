"""Fail-closed math-OCR adapter — never invents equations."""

from __future__ import annotations

from datetime import datetime, timezone

from knowledge.mathocr.models import MathOCRFailure, MathOCRResult
from knowledge.ocr.images import hash_image

__all__ = ("UnavailableMathOCRAdapter",)


class UnavailableMathOCRAdapter:
    adapter_name = "cosmos-mathocr-unavailable"
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
        region_id: str,
        source_text: str = "",
    ) -> MathOCRResult:
        del source_text
        return MathOCRResult(
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            region_id=region_id,
            image_hash=hash_image(image) if image else "",
            source_representation="",
            latex=None,
            mathml=None,
            structured_expression=None,
            confidence=0.0,
            backend=self.adapter_name,
            backend_version=self.adapter_version,
            configuration=("engine=none",),
            reconstruction=None,
            failure=MathOCRFailure.MATH_OCR_UNAVAILABLE
            if image
            else MathOCRFailure.CORRUPT_IMAGE,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
