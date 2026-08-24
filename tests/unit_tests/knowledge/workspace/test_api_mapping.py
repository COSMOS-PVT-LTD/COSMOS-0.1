"""API mapping tests."""

from __future__ import annotations

from knowledge.workspace.api_mapping import source_detail_mapping, source_list_mapping
from knowledge.workspace.models import IngestionJob, JobCheckpoint, JobStatus, SourceRecord


def _source(**overrides: object) -> SourceRecord:
    base = {
        "source_id": "SRC-test",
        "artifact_id": "ART-test",
        "filename": "paper.pdf",
        "media_type": "application/pdf",
        "extension": ".pdf",
        "size_bytes": 1000,
        "sha256": "a" * 64,
        "created_at": "2026-01-01T00:00:00+00:00",
        "ingested_at": "2026-01-01T00:00:00+00:00",
        "source_origin": "test",
        "rights_status": "INTERNAL",
        "license": None,
        "classification": "PDF",
        "version": 1,
        "parent_source_id": None,
        "storage_uri": "secret/path",
        "integrity_status": "VERIFIED",
        "workspace_format": "PDF",
        "project_id": "GLOBAL",
        "pipeline_version": "workspace-1.0.0",
        "configuration_hash": "cfg",
        "title": "paper.pdf",
        "processing_fingerprint": "fp",
        "recovered_text": "hello " * 200,
    }
    base.update(overrides)
    return SourceRecord(**base)  # type: ignore[arg-type]


def test_source_list_mapping_omits_full_text() -> None:
    payload = source_list_mapping(_source())
    assert "recovered_text" not in payload
    assert payload["text_preview"]
    assert payload["extraction"]["text_chars"] > 0


def test_source_detail_mapping_includes_content() -> None:
    job = IngestionJob(
        job_id="JOB-1",
        source_id="SRC-test",
        source_hash="a" * 64,
        status=JobStatus.AVAILABLE,
        attempt=1,
        pipeline_version="workspace-1.0.0",
        configuration_hash="cfg",
        created_at="2026-01-01T00:00:00+00:00",
        started_at="2026-01-01T00:00:00+00:00",
        completed_at=None,
        worker="local-sync",
        checkpoint=JobCheckpoint(last_completed_page=3),
        error_code=None,
        error_message=None,
    )
    payload = source_detail_mapping(_source(), job)
    assert "text_content" in payload
    assert payload["job"]["status"] == "AVAILABLE"
