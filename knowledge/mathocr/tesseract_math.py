"""Equation-span math path over local Tesseract. Not a dedicated math-OCR engine."""

from __future__ import annotations

from datetime import datetime, timezone

from knowledge.equations.reconstruction import reconstruct_equation
from knowledge.mathocr.models import MathOCRFailure, MathOCRResult
from knowledge.ocr.images import hash_image
from knowledge.ocr.tesseract import TesseractOCRAdapter, tesseract_is_provisioned, tesseract_version

__all__ = ("TesseractMathOCRAdapter", "tesseract_math_is_provisioned")


def tesseract_math_is_provisioned() -> bool:
    return tesseract_is_provisioned()


class TesseractMathOCRAdapter:
    adapter_name = "cosmos-mathocr-tesseract-span"
    adapter_version = "1.0.0"

    def available(self) -> bool:
        return tesseract_math_is_provisioned()

    def supports(self, image: bytes) -> bool:
        return self.available() and bool(image)

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
        stamp = datetime.now(timezone.utc).isoformat()
        version = tesseract_version()
        image_digest = hash_image(image) if image else ""
        text = source_text.strip()
        if not text and image and self.available():
            ocr = TesseractOCRAdapter().extract(
                image,
                source_id=source_id,
                document_id=document_id,
                page_number=page_number,
                image_id=region_id,
            )
            text = ocr.text.strip()
        if not text:
            return MathOCRResult(
                source_id=source_id,
                document_id=document_id,
                page_number=page_number,
                region_id=region_id,
                image_hash=image_digest,
                source_representation="",
                latex=None,
                mathml=None,
                structured_expression=None,
                confidence=0.0,
                backend=self.adapter_name,
                backend_version=version or self.adapter_version,
                configuration=("engine=tesseract-equation-span", "latex=reconstructed-from-source-text"),
                reconstruction=None,
                failure=MathOCRFailure.NO_EQUATION_REGION
                if "=" not in source_text
                else MathOCRFailure.MATH_OCR_FAILED,
                timestamp=stamp,
            )
        reconstruction = reconstruct_equation(region_id, text)
        failure = None
        if reconstruction.tree is None:
            failure = MathOCRFailure.UNSUPPORTED_STRUCTURE
        return MathOCRResult(
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            region_id=region_id,
            image_hash=image_digest,
            source_representation=text,
            latex=reconstruction.latex,
            mathml=reconstruction.mathml,
            structured_expression=reconstruction.normalized_representation,
            confidence=0.55 if reconstruction.tree is not None else 0.2,
            backend=self.adapter_name,
            backend_version=version or self.adapter_version,
            configuration=("engine=tesseract-equation-span", "latex=reconstructed-from-source-text"),
            reconstruction=reconstruction,
            failure=failure,
            timestamp=stamp,
        )
