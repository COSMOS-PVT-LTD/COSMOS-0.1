"""Extract native PDF page text. Never invent missing text."""

from __future__ import annotations

import re
import time

from knowledge.pdf.models import (
    ExtractionStatus,
    PageClassification,
    PageExtraction,
    PdfDiagnostics,
    PdfExtractionResult,
)
from knowledge.source.exceptions import IntegrityMismatchError
from knowledge.source.integrity import sha256_bytes_digest, verify_digest

__all__ = ("extract_pdf_pages", "ExtractionUnavailableError")

_PAGE_OBJECT = re.compile(rb"/Type\s*/Page(?!s)")
_TJ = re.compile(rb"\((?:\\.|[^\\)])*\)\s*Tj")
_IMAGE = re.compile(rb"/Subtype\s*/Image")


class ExtractionUnavailableError(RuntimeError):
    """Raised when page text cannot be recovered and OCR is not used here."""


def extract_pdf_pages(
    content: bytes,
    *,
    source_id: str,
    document_id: str,
    expected_hash: str | None = None,
) -> PdfExtractionResult:
    started = time.perf_counter()
    digest = sha256_bytes_digest(content)
    if expected_hash is not None:
        try:
            verify_digest(content, expected_hash)
        except IntegrityMismatchError:
            return _failed(
                source_id,
                document_id,
                digest,
                ExtractionStatus.HASH_MISMATCH,
                "HASH_MISMATCH: artifact digest does not match the registered source.",
                started,
            )
    if not content.startswith(b"%PDF-"):
        return _failed(
            source_id,
            document_id,
            digest,
            ExtractionStatus.CORRUPT_SOURCE,
            "Artifact is not a PDF.",
            started,
        )

    pages_text = _extract_via_optional_pypdf(content)
    method = "pypdf" if pages_text is not None else "tj-operator"
    if pages_text is None:
        pages_text = _extract_tj_pages(content)

    if not pages_text:
        pages_text = ("",)

    pages: list[PageExtraction] = []
    has_images = bool(_IMAGE.search(content))
    for index, text in enumerate(pages_text, start=1):
        cleaned = text.strip("\n")
        classification = _classify(cleaned, has_images)
        pages.append(
            PageExtraction(
                page_number=index,
                text=cleaned,
                classification=classification,
                has_images=has_images and not cleaned.strip(),
                char_count=len(cleaned.strip()),
                warning=None if cleaned.strip() else "No native text recovered on this page.",
            ),
        )

    with_text = sum(1 for page in pages if page.char_count > 0)
    diagnostics = PdfDiagnostics(
        page_count=len(pages),
        pages_with_text=with_text,
        pages_without_text=len(pages) - with_text,
        pages_with_images=sum(1 for page in pages if page.has_images),
        pages_with_tables=sum(1 for page in pages if "table" in page.text.lower()),
        pages_with_equation_candidates=sum(1 for page in pages if "=" in page.text),
        ocr_pages=0,
        failed_pages=sum(1 for page in pages if page.classification is PageClassification.EXTRACTION_FAILED),
        warnings=tuple(page.warning for page in pages if page.warning),
    )
    status = (
        ExtractionStatus.TEXT_AVAILABLE
        if with_text
        else ExtractionStatus.EXTRACTION_UNAVAILABLE
    )
    return PdfExtractionResult(
        source_id=source_id,
        document_id=document_id,
        content_hash=digest,
        status=status,
        pages=tuple(pages),
        diagnostics=diagnostics,
        method=method,
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )


def _classify(text: str, has_images: bool) -> PageClassification:
    if text.strip() and has_images:
        return PageClassification.MIXED
    if text.strip():
        return PageClassification.NATIVE_TEXT if len(text.strip()) >= 24 else PageClassification.LOW_TEXT_DENSITY
    if has_images:
        return PageClassification.OCR_REQUIRED
    return PageClassification.IMAGE_ONLY if not text.strip() else PageClassification.EXTRACTION_FAILED


def _extract_via_optional_pypdf(content: bytes) -> tuple[str, ...] | None:
    try:
        from pypdf import PdfReader  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        reader = PdfReader(__import__("io").BytesIO(content))
        pages = tuple((page.extract_text() or "") for page in reader.pages)
    except Exception:
        return None
    return pages or None


def _extract_tj_pages(content: bytes) -> tuple[str, ...]:
    page_count = max(1, len(_PAGE_OBJECT.findall(content)))
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", content, flags=re.DOTALL)
    if not streams:
        return tuple("" for _ in range(page_count))
    extracted: list[str] = []
    for stream in streams:
        texts = [_unescape(match.group(0)) for match in _TJ.finditer(stream)]
        if texts:
            extracted.append("\n".join(texts))
    if not extracted:
        return tuple("" for _ in range(page_count))
    while len(extracted) < page_count:
        extracted.append("")
    return tuple(extracted[:page_count])


def _unescape(operator: bytes) -> str:
    inner = operator.strip()
    if inner.startswith(b"("):
        inner = inner[1 : inner.rfind(b")")]
    return (
        inner.replace(b"\\(", b"(")
        .replace(b"\\)", b")")
        .replace(b"\\\\", b"\\")
        .decode("latin-1", errors="replace")
    )


def _failed(
    source_id: str,
    document_id: str,
    digest: str,
    status: ExtractionStatus,
    warning: str,
    started: float,
) -> PdfExtractionResult:
    page = PageExtraction(
        page_number=1,
        text="",
        classification=PageClassification.EXTRACTION_FAILED,
        has_images=False,
        char_count=0,
        warning=warning,
    )
    return PdfExtractionResult(
        source_id=source_id,
        document_id=document_id,
        content_hash=digest,
        status=status,
        pages=(page,),
        diagnostics=PdfDiagnostics(
            page_count=1,
            pages_with_text=0,
            pages_without_text=1,
            pages_with_images=0,
            pages_with_tables=0,
            pages_with_equation_candidates=0,
            ocr_pages=0,
            failed_pages=1,
            warnings=(warning,),
        ),
        method="none",
        elapsed_ms=(time.perf_counter() - started) * 1000.0,
    )
