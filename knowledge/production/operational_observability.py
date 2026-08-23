"""Operational observability hardening for Gate-6 readiness (Step 7)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from knowledge.production.observability import ObservabilityEvent
from knowledge.production.observability_export import (
    ErrorClassification,
    ObservabilityExportRecord,
    StructuredObservabilitySession,
)
from knowledge.storage.schema import PRODUCTION_SCHEMA_VERSION

__all__ = (
    "OBSERVABILITY_SCHEMA_VERSION",
    "OperationalEventTaxonomy",
    "OperationalObservabilityBridge",
    "redact_sensitive_metadata",
)

OBSERVABILITY_SCHEMA_VERSION = "1.0.0"

_FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "content",
        "document_text",
        "raw_text",
        "source_text",
        "embedding_vector",
        "credentials",
        "secret",
        "token",
        "api_key",
    },
)


@dataclass(frozen=True, slots=True)
class OperationalEventTaxonomy:
    """Canonical operational event names for Gate-6 observability."""

    INGESTION_STARTED: str = "ingestion.started"
    INGESTION_COMPLETED: str = "ingestion.completed"
    INGESTION_FAILED: str = "ingestion.failed"
    INDEXING_STARTED: str = "indexing.started"
    INDEXING_COMPLETED: str = "indexing.completed"
    PERSISTENCE_WRITE: str = "persistence.write"
    PERSISTENCE_LOAD: str = "persistence.load"
    PERSISTENCE_ERROR: str = "persistence.error"
    RETRIEVAL_STARTED: str = "retrieval.started"
    RETRIEVAL_COMPLETED: str = "retrieval.completed"
    RECOVERY_STARTED: str = "recovery.started"
    RECOVERY_COMPLETED: str = "recovery.completed"
    VALIDATION_FAILED: str = "validation.failed"
    EMBEDDING_FAILED: str = "embedding.failed"
    BENCHMARK_COMPLETED: str = "benchmark.completed"


def redact_sensitive_metadata(metadata: dict[str, object]) -> dict[str, object]:
    """Remove or digest values that must not appear in exported observability."""

    redacted: dict[str, object] = {}

    for key, value in metadata.items():
        lowered = key.lower()

        if lowered in _FORBIDDEN_METADATA_KEYS:
            continue

        if isinstance(value, str) and len(value) > 256:
            redacted[f"{key}_digest"] = hashlib.sha256(value.encode("utf-8")).hexdigest()
            continue

        redacted[key] = value

    return redacted


@dataclass
class OperationalObservabilityBridge:
    """Bridge pipeline events into operational observability with schema/version IDs."""

    session: StructuredObservabilitySession = field(
        default_factory=StructuredObservabilitySession,
    )
    taxonomy: OperationalEventTaxonomy = field(default_factory=OperationalEventTaxonomy)
    storage_schema_version: str = PRODUCTION_SCHEMA_VERSION
    observability_schema_version: str = OBSERVABILITY_SCHEMA_VERSION

    def record_pipeline_event(
        self,
        event: ObservabilityEvent,
        *,
        error_classification: ErrorClassification = ErrorClassification.NONE,
        metadata: dict[str, object] | None = None,
    ) -> ObservabilityExportRecord:
        payload = redact_sensitive_metadata(
            {
                "observability_schema_version": self.observability_schema_version,
                "storage_schema_version": self.storage_schema_version,
                **(metadata or {}),
            },
        )

        return self.session.record_event(
            event,
            error_classification=error_classification,
            extra_metadata=payload,
        )

    def export_bundle(self, output_dir: str) -> dict[str, object]:
        from knowledge.production.observability_export import ObservabilityExporter

        exporter = ObservabilityExporter(output_dir)
        jsonl_path = exporter.export_session(self.session)
        summary_path = exporter.export_summary(self.session)

        return {
            "event_count": len(self.session.exports),
            "jsonl_path": str(jsonl_path),
            "observability_schema_version": self.observability_schema_version,
            "storage_schema_version": self.storage_schema_version,
            "summary_path": str(summary_path),
        }

    def operational_summary(self) -> dict[str, object]:
        return {
            "counters": self.session.counters(),
            "event_count": len(self.session.exports),
            "observability_schema_version": self.observability_schema_version,
            "storage_schema_version": self.storage_schema_version,
            "timers": self.session.timer_summary(),
        }

    def to_json(self) -> str:
        return json.dumps(self.operational_summary(), indent=2, sort_keys=True)
