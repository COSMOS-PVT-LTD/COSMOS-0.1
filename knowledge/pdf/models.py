"""PDF page-extraction contracts. Missing text is never invented."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = (
    "ExtractionStatus",
    "PageClassification",
    "PageExtraction",
    "PdfExtractionResult",
    "PdfDiagnostics",
)


class PageClassification(Enum):
    NATIVE_TEXT = "NATIVE_TEXT"
    IMAGE_ONLY = "IMAGE_ONLY"
    MIXED = "MIXED"
    LOW_TEXT_DENSITY = "LOW_TEXT_DENSITY"
    OCR_REQUIRED = "OCR_REQUIRED"
    OCR_OPTIONAL = "OCR_OPTIONAL"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class ExtractionStatus(Enum):
    TEXT_AVAILABLE = "TEXT_AVAILABLE"
    EXTRACTION_UNAVAILABLE = "EXTRACTION_UNAVAILABLE"
    HASH_MISMATCH = "HASH_MISMATCH"
    CORRUPT_SOURCE = "CORRUPT_SOURCE"
    RIGHTS_BLOCKED = "RIGHTS_BLOCKED"


@dataclass(frozen=True, slots=True, kw_only=True)
class PageExtraction:
    page_number: int
    text: str
    classification: PageClassification
    has_images: bool
    char_count: int
    warning: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PdfDiagnostics:
    page_count: int
    pages_with_text: int
    pages_without_text: int
    pages_with_images: int
    pages_with_tables: int
    pages_with_equation_candidates: int
    ocr_pages: int
    failed_pages: int
    warnings: tuple[str, ...]


@dataclass(frozen=True, slots=True, kw_only=True)
class PdfExtractionResult:
    source_id: str
    document_id: str
    content_hash: str
    status: ExtractionStatus
    pages: tuple[PageExtraction, ...]
    diagnostics: PdfDiagnostics
    method: str
    elapsed_ms: float
