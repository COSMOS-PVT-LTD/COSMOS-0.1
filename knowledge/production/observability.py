"""Structured observability for production local RAG (Step 7)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum

__all__ = (
    "ObservabilityEvent",
    "ObservabilityRecorder",
    "ObservabilityStage",
)


class ObservabilityStage(Enum):
    """Production pipeline observability stages."""

    INGESTION = "INGESTION"
    INDEXING = "INDEXING"
    RETRIEVAL = "RETRIEVAL"
    VALIDATION = "VALIDATION"
    RAG = "RAG"
    RECOVERY = "RECOVERY"


@dataclass(frozen=True, slots=True, kw_only=True)
class ObservabilityEvent:
    """Structured observability event without sensitive document content."""

    stage: ObservabilityStage
    operation: str
    duration_ms: float
    success: bool
    metadata: dict[str, object] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, object]:
        return {
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
            "operation": self.operation,
            "stage": self.stage.value,
            "success": self.success,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), sort_keys=True)


class ObservabilityRecorder:
    """In-memory structured observability recorder."""

    def __init__(self) -> None:
        self._events: list[ObservabilityEvent] = []

    @property
    def events(self) -> tuple[ObservabilityEvent, ...]:
        return tuple(self._events)

    def record(self, event: ObservabilityEvent) -> None:
        self._events.append(event)

    def timed(
        self,
        *,
        stage: ObservabilityStage,
        operation: str,
        metadata: dict[str, object] | None = None,
    ):
        """Context manager for timed observability events."""

        return _TimedObservation(
            recorder=self,
            stage=stage,
            operation=operation,
            metadata=metadata or {},
        )

    def summary(self) -> dict[str, object]:
        by_stage: dict[str, int] = {}
        failures = 0

        for event in self._events:
            by_stage[event.stage.value] = by_stage.get(event.stage.value, 0) + 1

            if not event.success:
                failures += 1

        return {
            "event_count": len(self._events),
            "failures": failures,
            "stages": by_stage,
        }


class _TimedObservation:
    def __init__(
        self,
        *,
        recorder: ObservabilityRecorder,
        stage: ObservabilityStage,
        operation: str,
        metadata: dict[str, object],
    ) -> None:
        self._recorder = recorder
        self._stage = stage
        self._operation = operation
        self._metadata = metadata
        self._start = 0.0
        self._success = True

    def __enter__(self) -> _TimedObservation:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self._success = False

        duration_ms = (time.perf_counter() - self._start) * 1000.0
        self._recorder.record(
            ObservabilityEvent(
                stage=self._stage,
                operation=self._operation,
                duration_ms=duration_ms,
                success=self._success,
                metadata=self._metadata,
            ),
        )
