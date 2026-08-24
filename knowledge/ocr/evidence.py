"""OCR review evidence. OCR output is never treated as approved knowledge."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.ocr.models import OCRRegion, OCRResult
from knowledge.ocr.rasterize import RasterizeResult

__all__ = ("OCREvidence", "build_ocr_evidence")


@dataclass(frozen=True, slots=True, kw_only=True)
class OCREvidence:
    source_id: str
    document_id: str
    page_number: int
    image_hash: str
    rasterizer: str
    rasterizer_version: str
    raster_configuration_hash: str
    ocr_backend: str
    ocr_version: str
    ocr_text: str
    ocr_confidence: float
    regions: tuple[OCRRegion, ...]
    warnings: tuple[str, ...]
    page_image: bytes
    configuration: tuple[str, ...]


def build_ocr_evidence(
    raster: RasterizeResult,
    ocr: OCRResult,
    *,
    warnings: tuple[str, ...] = (),
) -> OCREvidence:
    return OCREvidence(
        source_id=ocr.source_id,
        document_id=ocr.document_id,
        page_number=ocr.page_number,
        image_hash=raster.image_hash or ocr.image_hash,
        rasterizer=raster.rasterizer,
        rasterizer_version=raster.rasterizer_version,
        raster_configuration_hash=raster.configuration_hash,
        ocr_backend=ocr.adapter_name,
        ocr_version=ocr.engine_version or ocr.adapter_version,
        ocr_text=ocr.text,
        ocr_confidence=ocr.confidence,
        regions=ocr.regions,
        warnings=warnings,
        page_image=raster.image,
        configuration=ocr.configuration,
    )
