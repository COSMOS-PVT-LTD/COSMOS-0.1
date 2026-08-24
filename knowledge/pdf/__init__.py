"""Native PDF source registration and page-text extraction — fail closed."""

from __future__ import annotations

from knowledge.pdf.extractor import extract_pdf_pages
from knowledge.pdf.models import (
    ExtractionStatus,
    PageClassification,
    PageExtraction,
    PdfDiagnostics,
    PdfExtractionResult,
)
from knowledge.pdf.registry import DuplicateKind, RegisteredSource, SourceModifiedError, SourceRegistry
from knowledge.pdf.structure import ExtractedDocumentStructure, extract_document_structure
from knowledge.pdf.image_pdf import write_image_pdf, write_scanned_pdf
from knowledge.pdf.writer import write_extractable_pdf, write_image_only_pdf, write_mixed_pdf

__all__ = (
    "DuplicateKind",
    "ExtractedDocumentStructure",
    "ExtractionStatus",
    "PageClassification",
    "PageExtraction",
    "PdfDiagnostics",
    "PdfExtractionResult",
    "RegisteredSource",
    "SourceModifiedError",
    "SourceRegistry",
    "extract_document_structure",
    "extract_pdf_pages",
    "write_extractable_pdf",
    "write_image_only_pdf",
    "write_image_pdf",
    "write_mixed_pdf",
    "write_scanned_pdf",
)
