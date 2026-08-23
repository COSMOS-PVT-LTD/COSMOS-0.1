"""Performance characterization helpers for production local RAG (Step 7)."""

from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

__all__ = (
    "PerformanceBenchmark",
    "PerformanceSample",
    "PerformanceSummary",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class PerformanceSample:
    """Single timed operation sample."""

    operation: str
    duration_ms: float


@dataclass(frozen=True, slots=True, kw_only=True)
class PerformanceSummary:
    """Aggregate performance summary."""

    operation: str
    sample_count: int
    p50_ms: float
    p95_ms: float
    max_ms: float

    def to_mapping(self) -> dict[str, object]:
        return {
            "max_ms": self.max_ms,
            "operation": self.operation,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "sample_count": self.sample_count,
        }


class PerformanceBenchmark:
    """Simple local performance benchmark harness."""

    def __init__(self) -> None:
        self._samples: dict[str, list[float]] = {}

    def time_operation(self, operation: str, callback) -> PerformanceSample:
        """Time a callable and record the sample."""

        start = time.perf_counter()
        callback()
        duration_ms = (time.perf_counter() - start) * 1000.0
        self._samples.setdefault(operation, []).append(duration_ms)

        return PerformanceSample(operation=operation, duration_ms=duration_ms)

    def summarize(self, operation: str) -> PerformanceSummary:
        """Summarize recorded samples for an operation."""

        values = sorted(self._samples.get(operation, []))

        if not values:
            return PerformanceSummary(
                operation=operation,
                sample_count=0,
                p50_ms=0.0,
                p95_ms=0.0,
                max_ms=0.0,
            )

        p50 = statistics.median(values)
        p95_index = max(0, int(len(values) * 0.95) - 1)

        return PerformanceSummary(
            operation=operation,
            sample_count=len(values),
            p50_ms=p50,
            p95_ms=values[p95_index],
            max_ms=values[-1],
        )
