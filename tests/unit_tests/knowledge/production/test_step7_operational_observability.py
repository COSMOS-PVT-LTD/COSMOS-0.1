"""Gate-6 operational observability tests."""

from __future__ import annotations

from knowledge.production.observability import ObservabilityEvent, ObservabilityStage
from knowledge.production.observability_export import ErrorClassification
from knowledge.production.operational_observability import (
    OperationalObservabilityBridge,
    redact_sensitive_metadata,
)


def test_redact_sensitive_metadata_removes_content() -> None:
    redacted = redact_sensitive_metadata(
        {
            "document_id": "DOC-1",
            "content": "proprietary chamber pressure data",
            "api_key": "secret",
        },
    )

    assert redacted["document_id"] == "DOC-1"
    assert "content" not in redacted
    assert "api_key" not in redacted


def test_operational_bridge_records_schema_versions(tmp_path) -> None:
    bridge = OperationalObservabilityBridge()
    bridge.record_pipeline_event(
        ObservabilityEvent(
            stage=ObservabilityStage.INGESTION,
            operation="ingest_document",
            duration_ms=3.5,
            success=True,
            metadata={"document_id": "DOC-1"},
        ),
        error_classification=ErrorClassification.NONE,
    )

    export_info = bridge.export_bundle(tmp_path)
    summary = bridge.operational_summary()

    assert summary["observability_schema_version"] == "1.0.0"
    assert summary["storage_schema_version"] == "1.0.0"
    assert export_info["event_count"] == 1
