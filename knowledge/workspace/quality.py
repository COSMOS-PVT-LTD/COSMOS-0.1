"""Heuristics for judging whether a workspace source was under-extracted."""

from __future__ import annotations

from knowledge.workspace.models import IngestionJob, JobStatus, SourceRecord

__all__ = ("pdf_extraction_is_under_recovered", "source_extraction_summary")


def _estimated_pdf_pages(job: IngestionJob | None, source: SourceRecord) -> int:
    if job is not None and job.checkpoint.last_completed_page:
        return max(1, int(job.checkpoint.last_completed_page))
    size = source.size_bytes or 0
    if size > 2_000_000:
        return max(10, size // 50_000)
    if size > 500_000:
        return max(5, size // 80_000)
    return 1


def pdf_extraction_is_under_recovered(
    source: SourceRecord,
    job: IngestionJob | None = None,
    *,
    min_chars_per_page: int = 180,
) -> bool:
    """Return True when a PDF likely needs OCR/text extraction re-run."""

    if source.workspace_format != "PDF":
        return False
    text = (source.recovered_text or "").strip()
    if not text:
        return job is not None and job.status in {JobStatus.AVAILABLE, JobStatus.REVIEW_REQUIRED}
    pages = _estimated_pdf_pages(job, source)
    chars_per_page = len(text) / pages
    if chars_per_page < min_chars_per_page:
        return True
    if source.size_bytes >= 1_000_000 and len(text) < 20_000:
        return chars_per_page < 400
    return False


def source_extraction_summary(
    source: SourceRecord,
    job: IngestionJob | None = None,
) -> dict[str, object]:
    text = (source.recovered_text or "").strip()
    pages = _estimated_pdf_pages(job, source)
    under_recovered = pdf_extraction_is_under_recovered(source, job)
    return {
        "source_id": source.source_id,
        "text_chars": len(text),
        "estimated_pages": pages,
        "chars_per_page": round(len(text) / pages, 1) if pages else 0,
        "under_recovered": under_recovered,
        "job_status": job.status.value if job is not None else None,
    }
