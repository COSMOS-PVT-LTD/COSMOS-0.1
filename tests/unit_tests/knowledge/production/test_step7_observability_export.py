"""Step 7 observability export tests."""

from __future__ import annotations

from knowledge.production.observability import ObservabilityEvent, ObservabilityStage
from knowledge.production.observability_export import (
    ErrorClassification,
    ObservabilityExporter,
    StructuredObservabilitySession,
)


def test_structured_observability_session_records_correlation_id() -> None:
    session = StructuredObservabilitySession(correlation_id="corr-123")
    export_record = session.record_event(
        ObservabilityEvent(
            stage=ObservabilityStage.INGESTION,
            operation="ingest_document",
            duration_ms=12.5,
            success=True,
            metadata={"document_id": "DOC-A"},
        ),
    )

    assert export_record.correlation_id == "corr-123"
    assert export_record.metadata["document_id"] == "DOC-A"
    assert session.counters()["INGESTION.ingest_document"] == 1


def test_observability_exporter_writes_jsonl(tmp_path) -> None:
    session = StructuredObservabilitySession(correlation_id="corr-export")
    session.record_event(
        ObservabilityEvent(
            stage=ObservabilityStage.RETRIEVAL,
            operation="query",
            duration_ms=4.2,
            success=False,
            metadata={"request_id": "req-1"},
        ),
        error_classification=ErrorClassification.RETRIEVAL,
    )

    exporter = ObservabilityExporter(tmp_path)
    jsonl_path = exporter.export_session(session)
    summary_path = exporter.export_summary(session)

    assert jsonl_path.is_file()
    assert summary_path.is_file()
    assert "correlation_id" in jsonl_path.read_text(encoding="utf-8")
    assert "corr-export" in summary_path.read_text(encoding="utf-8")

    payload = jsonl_path.read_text(encoding="utf-8")
    assert "DOC-A" not in payload
    assert "chamber" not in payload.lower()
