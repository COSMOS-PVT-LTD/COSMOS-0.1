"""Ingestion safety limits for untrusted PDFs. No path-based OCR inputs."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.pdf.models import ExtractionStatus

__all__ = (
    "MAX_IMAGE_BYTES",
    "MAX_PAGE_COUNT",
    "MAX_PDF_BYTES",
    "PdfSecurityFinding",
    "validate_pdf_bytes",
)

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_PAGE_COUNT = 50
MAX_IMAGE_BYTES = 20 * 1024 * 1024


@dataclass(frozen=True, slots=True, kw_only=True)
class PdfSecurityFinding:
    accepted: bool
    status: ExtractionStatus | None
    reason: str


def validate_pdf_bytes(content: bytes) -> PdfSecurityFinding:
    """Reject path-like, oversized, or non-PDF artifacts before OCR."""

    if not isinstance(content, bytes):
        return PdfSecurityFinding(
            accepted=False,
            status=ExtractionStatus.CORRUPT_SOURCE,
            reason="content must be bytes.",
        )
    if len(content) > MAX_PDF_BYTES:
        return PdfSecurityFinding(
            accepted=False,
            status=ExtractionStatus.CORRUPT_SOURCE,
            reason=f"PDF exceeds {MAX_PDF_BYTES} byte limit.",
        )
    if not content.startswith(b"%PDF-"):
        return PdfSecurityFinding(
            accepted=False,
            status=ExtractionStatus.CORRUPT_SOURCE,
            reason="Artifact is not a PDF.",
        )
    page_count = content.count(b"/Type /Page") - content.count(b"/Type /Pages")
    if page_count > MAX_PAGE_COUNT:
        return PdfSecurityFinding(
            accepted=False,
            status=ExtractionStatus.CORRUPT_SOURCE,
            reason=f"PDF exceeds {MAX_PAGE_COUNT} page limit.",
        )
    return PdfSecurityFinding(accepted=True, status=None, reason="ok")
