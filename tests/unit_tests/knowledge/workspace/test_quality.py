"""Extraction quality heuristics."""

from __future__ import annotations

from knowledge.workspace.models import IngestionJob, JobCheckpoint, JobStatus, SourceRecord
from knowledge.workspace.quality import pdf_extraction_is_under_recovered, source_extraction_summary


def _source(**overrides: object) -> SourceRecord:
    base = {
        "source_id": "SRC-test",
        "artifact_id": "ART-test",
        "filename": "paper.pdf",
        "media_type": "application/pdf",
        "extension": ".pdf",
        "size_bytes": 4_000_000,
        "sha256": "a" * 64,
        "created_at": "2026-01-01T00:00:00+00:00",
        "ingested_at": "2026-01-01T00:00:00+00:00",
        "source_origin": "test",
        "rights_status": "INTERNAL",
        "license": None,
        "classification": "PDF",
        "version": 1,
        "parent_source_id": None,
        "storage_uri": "",
        "integrity_status": "VERIFIED",
        "workspace_format": "PDF",
        "project_id": "GLOBAL",
        "pipeline_version": "workspace-1.0.0",
        "configuration_hash": "cfg",
        "title": "paper.pdf",
        "processing_fingerprint": "fp",
        "recovered_text": "short",
    }
    base.update(overrides)
    return SourceRecord(**base)  # type: ignore[arg-type]


def _job(**overrides: object) -> IngestionJob:
    base = {
        "job_id": "JOB-test",
        "source_id": "SRC-test",
        "source_hash": "a" * 64,
        "status": JobStatus.REVIEW_REQUIRED,
        "attempt": 1,
        "pipeline_version": "workspace-1.0.0",
        "configuration_hash": "cfg",
        "created_at": "2026-01-01T00:00:00+00:00",
        "started_at": "2026-01-01T00:00:00+00:00",
        "completed_at": None,
        "worker": "local-sync",
        "checkpoint": JobCheckpoint(last_completed_page=102, last_completed_stage="pdf"),
        "error_code": None,
        "error_message": None,
    }
    base.update(overrides)
    return IngestionJob(**base)  # type: ignore[arg-type]


def test_pdf_under_recovered_when_text_is_tiny_for_large_pdf() -> None:
    source = _source(recovered_text="x" * 3000)
    job = _job()
    assert pdf_extraction_is_under_recovered(source, job) is True


def test_pdf_not_under_recovered_when_text_is_rich() -> None:
    source = _source(recovered_text="word " * 30_000)
    job = _job()
    assert pdf_extraction_is_under_recovered(source, job) is False


def test_source_extraction_summary_flags_under_recovered() -> None:
    summary = source_extraction_summary(_source(recovered_text="tiny"), _job())
    assert summary["under_recovered"] is True
    assert summary["estimated_pages"] == 102
