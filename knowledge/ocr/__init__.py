"""OCR / image layer — evidence only, never authoritative knowledge."""

from __future__ import annotations

from knowledge.ocr.adapter import OCRAdapter, select_ocr_adapter
from knowledge.ocr.cache import OCRCache
from knowledge.ocr.embedded import EmbeddedImageRef, list_embedded_images
from knowledge.ocr.engine import run_ocr
from knowledge.ocr.images import hash_image, preprocess_record
from knowledge.ocr.models import (
    BoundingBox,
    EquationRegionCandidate,
    FigureCandidate,
    OCRFailure,
    OCRResult,
    RegionType,
    TableCandidate,
)
from knowledge.ocr.health import HealthState, OCRHealth, ocr_health
from knowledge.ocr.provisioning import ocr_is_provisioned, rasterizer_is_provisioned
from knowledge.ocr.service import OCRJob, OCRService
from knowledge.ocr.rasterize import (
    PdfRasterizer,
    RasterizeResult,
    UnavailableRasterizer,
    rasterize_page,
    select_pdf_rasterizer,
)
from knowledge.ocr.regions import detect_equation_regions, detect_figure_candidates, detect_table_candidates
from knowledge.ocr.unavailable import UnavailableOCRAdapter

__all__ = (
    "BoundingBox",
    "EmbeddedImageRef",
    "EquationRegionCandidate",
    "FigureCandidate",
    "HealthState",
    "OCRAdapter",
    "OCRCache",
    "OCRFailure",
    "OCRHealth",
    "OCRJob",
    "OCRResult",
    "OCRService",
    "PdfRasterizer",
    "RasterizeResult",
    "RegionType",
    "TableCandidate",
    "UnavailableOCRAdapter",
    "UnavailableRasterizer",
    "detect_equation_regions",
    "detect_figure_candidates",
    "detect_table_candidates",
    "hash_image",
    "list_embedded_images",
    "ocr_health",
    "ocr_is_provisioned",
    "preprocess_record",
    "rasterize_page",
    "rasterizer_is_provisioned",
    "run_ocr",
    "select_ocr_adapter",
    "select_pdf_rasterizer",
)
