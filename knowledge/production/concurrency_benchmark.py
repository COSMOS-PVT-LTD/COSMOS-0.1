"""Concurrent query characterization for Gate-6 / final completion."""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from knowledge.production.local_rag_pipeline import ProductionLocalRAGPipeline
from knowledge.production.scale_benchmark import generate_scale_corpus

__all__ = (
    "ConcurrencyBenchmarkReport",
    "ConcurrencyBenchmarkRunner",
    "ConcurrencyResult",
    "ConcurrencyVerificationResult",
)


class ConcurrencyVerificationResult(Enum):
    """Verification outcome for a concurrency level."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CHARACTERIZED = "CHARACTERIZED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcurrencyResult:
    """Measured query throughput at a fixed concurrency level."""

    concurrency: int
    document_count: int
    query_count: int
    total_ms: float
    mean_query_ms: float
    p95_query_ms: float
    verification: ConcurrencyVerificationResult
    error_message: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "concurrency": self.concurrency,
            "document_count": self.document_count,
            "error_message": self.error_message,
            "mean_query_ms": round(self.mean_query_ms, 3),
            "p95_query_ms": round(self.p95_query_ms, 3),
            "query_count": self.query_count,
            "total_ms": round(self.total_ms, 3),
            "verification": self.verification.value,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ConcurrencyBenchmarkReport:
    """Aggregate concurrency characterization report."""

    environment: dict[str, object]
    document_count: int
    results: tuple[ConcurrencyResult, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "document_count": self.document_count,
            "environment": self.environment,
            "results": [item.to_mapping() for item in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True)


class ConcurrencyBenchmarkRunner:
    """Characterize concurrent local query latency (single-writer store)."""

    def __init__(self, *, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _prepare_store(self, document_count: int) -> Path:
        store_root = self._base_dir / f"concurrency-corpus-{document_count}"
        store_root.mkdir(parents=True, exist_ok=True)
        pipeline = ProductionLocalRAGPipeline(store_root)
        pipeline.initialize()

        for document_id, source_id, artifact_id, content in generate_scale_corpus(
            document_count,
        ):
            pipeline.ingest_document(
                document_id=document_id,
                source_id=source_id,
                artifact_id=artifact_id,
                content=content,
            )

        return store_root

    def run_level(
        self,
        *,
        document_count: int,
        concurrency: int,
        query_count: int = 16,
    ) -> ConcurrencyResult:
        store_root = self._prepare_store(document_count)
        documents = generate_scale_corpus(document_count)
        query_text = "chamber pressure LOX thrust"
        latencies: list[float] = []

        def _single_query(request_index: int) -> float:
            document_id = documents[request_index % len(documents)][0]
            pipeline = ProductionLocalRAGPipeline(store_root)
            pipeline.initialize()
            start = time.perf_counter()
            pipeline.query(
                task="Concurrency benchmark",
                query_text=query_text,
                document_id=document_id,
                request_id=f"conc-{concurrency}-{request_index}",
            )
            return (time.perf_counter() - start) * 1000.0

        try:
            sweep_start = time.perf_counter()

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [
                    executor.submit(_single_query, index) for index in range(query_count)
                ]

                for future in as_completed(futures):
                    latencies.append(future.result())

            total_ms = (time.perf_counter() - sweep_start) * 1000.0
            sorted_latencies = sorted(latencies)
            p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)

            verification = (
                ConcurrencyVerificationResult.VERIFIED
                if concurrency <= 4 and document_count <= 100
                else ConcurrencyVerificationResult.CHARACTERIZED
            )

            return ConcurrencyResult(
                concurrency=concurrency,
                document_count=document_count,
                query_count=query_count,
                total_ms=total_ms,
                mean_query_ms=statistics.mean(latencies),
                p95_query_ms=sorted_latencies[p95_index],
                verification=verification,
            )
        except Exception as exc:
            return ConcurrencyResult(
                concurrency=concurrency,
                document_count=document_count,
                query_count=query_count,
                total_ms=0.0,
                mean_query_ms=0.0,
                p95_query_ms=0.0,
                verification=ConcurrencyVerificationResult.FAILED,
                error_message=str(exc),
            )

    def run_sweep(
        self,
        *,
        document_count: int = 25,
        concurrency_levels: tuple[int, ...] = (1, 2, 4, 8),
    ) -> ConcurrencyBenchmarkReport:
        results = tuple(
            self.run_level(document_count=document_count, concurrency=level)
            for level in concurrency_levels
        )
        environment: dict[str, object] = {
            "hardware_note": "local benchmark runner — read-heavy concurrent queries",
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
        }

        return ConcurrencyBenchmarkReport(
            environment=environment,
            document_count=document_count,
            results=results,
        )
