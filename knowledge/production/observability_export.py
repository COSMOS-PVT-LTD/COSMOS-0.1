"""Structured observability export for production local RAG (Step 7 gate closure)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from knowledge.production.observability import ObservabilityEvent, ObservabilityRecorder

__all__ = (
    "ErrorClassification",
    "ObservabilityExportRecord",
    "ObservabilityExporter",
    "StructuredObservabilitySession",
)


class ErrorClassification(Enum):
    """Non-sensitive error classification for production observability."""

    NONE = "NONE"
    VALIDATION = "VALIDATION"
    PERSISTENCE = "PERSISTENCE"
    INDEX = "INDEX"
    RECOVERY = "RECOVERY"
    INGESTION = "INGESTION"
    RETRIEVAL = "RETRIEVAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True, kw_only=True)
class ObservabilityExportRecord:
    """Privacy-preserving structured observability record."""

    correlation_id: str
    timestamp_utc: str
    stage: str
    operation: str
    duration_ms: float
    success: bool
    error_classification: ErrorClassification
    metadata: dict[str, object] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, object]:
        return {
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "error_classification": self.error_classification.value,
            "metadata": self.metadata,
            "operation": self.operation,
            "stage": self.stage,
            "success": self.success,
            "timestamp_utc": self.timestamp_utc,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True)


class StructuredObservabilitySession:
    """Session-scoped observability with correlation identifiers."""

    def __init__(self, *, correlation_id: str | None = None) -> None:
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._recorder = ObservabilityRecorder()
        self._exports: list[ObservabilityExportRecord] = []
        self._counters: dict[str, int] = {}
        self._timers_ms: dict[str, list[float]] = {}

    @property
    def recorder(self) -> ObservabilityRecorder:
        return self._recorder

    @property
    def exports(self) -> tuple[ObservabilityExportRecord, ...]:
        return tuple(self._exports)

    def record_event(
        self,
        event: ObservabilityEvent,
        *,
        error_classification: ErrorClassification = ErrorClassification.NONE,
        extra_metadata: dict[str, object] | None = None,
    ) -> ObservabilityExportRecord:
        metadata = {
            "correlation_id": self.correlation_id,
            **event.metadata,
            **(extra_metadata or {}),
        }
        export_record = ObservabilityExportRecord(
            correlation_id=self.correlation_id,
            timestamp_utc=datetime.now(UTC).isoformat(),
            stage=event.stage.value,
            operation=event.operation,
            duration_ms=event.duration_ms,
            success=event.success,
            error_classification=error_classification,
            metadata=metadata,
        )
        self._exports.append(export_record)
        self._recorder.record(event)

        counter_key = f"{event.stage.value}.{event.operation}"
        self._counters[counter_key] = self._counters.get(counter_key, 0) + 1
        self._timers_ms.setdefault(counter_key, []).append(event.duration_ms)

        if not event.success:
            failure_key = f"failures.{event.stage.value}"
            self._counters[failure_key] = self._counters.get(failure_key, 0) + 1

        return export_record

    def counters(self) -> dict[str, int]:
        return dict(self._counters)

    def timer_summary(self) -> dict[str, object]:
        summary: dict[str, object] = {}

        for key, values in sorted(self._timers_ms.items()):
            if not values:
                continue

            sorted_values = sorted(values)
            summary[key] = {
                "count": len(sorted_values),
                "max_ms": sorted_values[-1],
                "p50_ms": sorted_values[len(sorted_values) // 2],
            }

        return summary


class ObservabilityExporter:
    """Export structured observability records to local JSONL files."""

    def __init__(self, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def export_session(self, session: StructuredObservabilitySession) -> Path:
        path = self._output_dir / f"observability-{session.correlation_id}.jsonl"
        lines = [record.to_json() for record in session.exports]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return path

    def export_summary(self, session: StructuredObservabilitySession) -> Path:
        path = self._output_dir / f"observability-summary-{session.correlation_id}.json"
        payload = {
            "correlation_id": session.correlation_id,
            "counters": session.counters(),
            "event_count": len(session.exports),
            "timers": session.timer_summary(),
        }
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path
