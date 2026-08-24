"""Public API mappings for knowledge workspace sources (no huge payloads in lists)."""

from __future__ import annotations

from knowledge.workspace.models import IngestionJob, SourceRecord
from knowledge.workspace.quality import source_extraction_summary

__all__ = ("source_detail_mapping", "source_list_mapping")

_PREVIEW_LEN = 320
_DETAIL_LEN = 16_000


def source_list_mapping(record: SourceRecord, job: IngestionJob | None = None) -> dict[str, object]:
    text = (record.recovered_text or "").strip()
    summary = source_extraction_summary(record, job)
    return {
        "source_id": record.source_id,
        "filename": record.filename,
        "title": record.title,
        "workspace_format": record.workspace_format,
        "rights_status": record.rights_status,
        "size_bytes": record.size_bytes,
        "project_id": record.project_id,
        "ingested_at": record.ingested_at,
        "integrity_status": record.integrity_status,
        "text_preview": _preview(text),
        "extraction": summary,
        "job_status": job.status.value if job is not None else None,
        "needs_approval": job.status.value == "REVIEW_REQUIRED" if job is not None else False,
        "can_reextract": record.workspace_format == "PDF",
    }


def source_detail_mapping(record: SourceRecord, job: IngestionJob | None = None) -> dict[str, object]:
    text = record.recovered_text or ""
    payload = source_list_mapping(record, job)
    payload.update(
        {
            "sha256": record.sha256,
            "created_at": record.created_at,
            "adapter_version": record.adapter_version,
            "pipeline_version": record.pipeline_version,
            "text_chars": len(text.strip()),
            "text_content": text[:_DETAIL_LEN] + ("…" if len(text) > _DETAIL_LEN else ""),
            "text_truncated": len(text) > _DETAIL_LEN,
        },
    )
    if job is not None:
        payload["job"] = job.to_mapping()
    return payload


def _preview(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return ""
    if len(cleaned) <= _PREVIEW_LEN:
        return cleaned
    return cleaned[:_PREVIEW_LEN] + "…"
