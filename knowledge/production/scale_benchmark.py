"""Representative-scale performance benchmarking for Gate-6 readiness (Step 7)."""

from __future__ import annotations

import json
import platform
import resource
import statistics
import sys
import time
import tracemalloc
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from knowledge.production.local_rag_pipeline import ProductionLocalRAGPipeline

__all__ = (
    "CorpusBenchmarkResult",
    "ScaleBenchmarkReport",
    "ScaleBenchmarkRunner",
    "ScaleVerificationResult",
    "generate_scale_corpus",
)


class ScaleVerificationResult(Enum):
    """Verification outcome for a corpus scale point."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    CHARACTERIZED = "CHARACTERIZED"
    NOT_VERIFIED = "NOT_VERIFIED"
    FAILED = "FAILED"


def generate_scale_corpus(document_count: int) -> tuple[tuple[str, str, str, str], ...]:
    """Build deterministic synthetic markdown documents for scale testing."""

    if document_count <= 0:
        raise ValueError("document_count must be positive.")

    documents: list[tuple[str, str, str, str]] = []

    for index in range(document_count):
        document_id = f"DOC-SCALE-{index:04d}"
        source_id = f"SRC-SCALE-{index:04d}"
        artifact_id = f"ART-SCALE-{index:04d}"
        content = (
            f"# Engineering Spec {index}\n\n"
            f"## Section A\n\n"
            f"Chamber pressure nominal at {1500 + index} kPa for subsystem {index}.\n\n"
            f"## Section B\n\n"
            f"Thrust vector control margin {index % 7} degrees.\n"
            f"LOX flow rate {10 + (index % 5)} kg/s.\n"
        )
        documents.append((document_id, source_id, artifact_id, content))

    return tuple(documents)


@dataclass(frozen=True, slots=True, kw_only=True)
class CorpusBenchmarkResult:
    """Measured benchmark result for a single corpus scale."""

    document_count: int
    verification: ScaleVerificationResult
    ingestion_total_ms: float
    ingestion_per_doc_ms: float
    persistence_reload_ms: float
    recovery_ms: float
    query_cold_ms: float
    query_warm_ms: float
    query_deterministic_repeat_ms: float
    storage_bytes: int
    peak_memory_bytes: int
    graph_node_count: int
    registered_document_count: int
    error_message: str | None = None

    def to_mapping(self) -> dict[str, object]:
        return {
            "document_count": self.document_count,
            "error_message": self.error_message,
            "graph_node_count": self.graph_node_count,
            "ingestion_per_doc_ms": round(self.ingestion_per_doc_ms, 3),
            "ingestion_total_ms": round(self.ingestion_total_ms, 3),
            "peak_memory_bytes": self.peak_memory_bytes,
            "persistence_reload_ms": round(self.persistence_reload_ms, 3),
            "query_cold_ms": round(self.query_cold_ms, 3),
            "query_deterministic_repeat_ms": round(self.query_deterministic_repeat_ms, 3),
            "query_warm_ms": round(self.query_warm_ms, 3),
            "recovery_ms": round(self.recovery_ms, 3),
            "registered_document_count": self.registered_document_count,
            "storage_bytes": self.storage_bytes,
            "verification": self.verification.value,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ScaleBenchmarkReport:
    """Aggregate scale sweep report with environment metadata."""

    environment: dict[str, object]
    corpus_results: tuple[CorpusBenchmarkResult, ...]
    scale_points: tuple[int, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "corpus_results": [item.to_mapping() for item in self.corpus_results],
            "environment": self.environment,
            "scale_points": list(self.scale_points),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True)


def _peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":
        return rss
    return rss * 1024


def _directory_size(path: Path) -> int:
    total = 0

    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size

    return total


def _timed(callback) -> float:
    start = time.perf_counter()
    callback()
    return (time.perf_counter() - start) * 1000.0


class ScaleBenchmarkRunner:
    """Execute representative-scale benchmarks without fabricating results."""

    def __init__(self, *, base_dir: Path) -> None:
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def run_corpus(self, document_count: int) -> CorpusBenchmarkResult:
        """Benchmark a single corpus size in an isolated store directory."""

        store_root = self._base_dir / f"corpus-{document_count}"
        if store_root.exists():
            for child in sorted(store_root.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                elif child.is_dir():
                    child.rmdir()
        store_root.mkdir(parents=True, exist_ok=True)

        documents = generate_scale_corpus(document_count)
        query_text = "chamber pressure LOX thrust"
        per_doc_times: list[float] = []

        tracemalloc.start()

        try:
            pipeline = ProductionLocalRAGPipeline(store_root)
            pipeline.initialize()

            ingest_start = time.perf_counter()
            for document_id, source_id, artifact_id, content in documents:
                per_doc_times.append(
                    _timed(
                        lambda d=document_id,
                        s=source_id,
                        a=artifact_id,
                        c=content: pipeline.ingest_document(
                            document_id=d,
                            source_id=s,
                            artifact_id=a,
                            content=c,
                            query_text=query_text,
                        ),
                    ),
                )
            ingestion_total_ms = (time.perf_counter() - ingest_start) * 1000.0

            persistence_reload_ms = _timed(
                lambda: ProductionLocalRAGPipeline(store_root).initialize(),
            )

            restarted = ProductionLocalRAGPipeline(store_root)
            restarted.initialize()
            recovery_ms = _timed(restarted.recover)

            first_doc_id = documents[0][0]
            query_cold_ms = _timed(
                lambda: restarted.query(
                    task="Scale benchmark cold",
                    query_text=query_text,
                    document_id=first_doc_id,
                    request_id="scale-cold",
                ),
            )
            query_warm_ms = _timed(
                lambda: restarted.query(
                    task="Scale benchmark warm",
                    query_text=query_text,
                    document_id=first_doc_id,
                    request_id="scale-warm",
                ),
            )
            query_deterministic_repeat_ms = _timed(
                lambda: restarted.query(
                    task="Scale benchmark warm",
                    query_text=query_text,
                    document_id=first_doc_id,
                    request_id="scale-warm-repeat",
                ),
            )

            graph_nodes = len(restarted.store.graph_store.list_nodes())
            registered = len(restarted.store.documents)

            _, peak = tracemalloc.get_traced_memory()
            peak_memory = max(peak, _peak_rss_bytes())
            storage_bytes = _directory_size(store_root)

            verification = self._classify_verification(
                document_count=document_count,
                registered=registered,
                graph_nodes=graph_nodes,
            )

            return CorpusBenchmarkResult(
                document_count=document_count,
                verification=verification,
                ingestion_total_ms=ingestion_total_ms,
                ingestion_per_doc_ms=statistics.mean(per_doc_times) if per_doc_times else 0.0,
                persistence_reload_ms=persistence_reload_ms,
                recovery_ms=recovery_ms,
                query_cold_ms=query_cold_ms,
                query_warm_ms=query_warm_ms,
                query_deterministic_repeat_ms=query_deterministic_repeat_ms,
                storage_bytes=storage_bytes,
                peak_memory_bytes=peak_memory,
                graph_node_count=graph_nodes,
                registered_document_count=registered,
            )
        except Exception as exc:
            _, peak = tracemalloc.get_traced_memory()
            return CorpusBenchmarkResult(
                document_count=document_count,
                verification=ScaleVerificationResult.FAILED,
                ingestion_total_ms=0.0,
                ingestion_per_doc_ms=0.0,
                persistence_reload_ms=0.0,
                recovery_ms=0.0,
                query_cold_ms=0.0,
                query_warm_ms=0.0,
                query_deterministic_repeat_ms=0.0,
                storage_bytes=_directory_size(store_root),
                peak_memory_bytes=peak,
                graph_node_count=0,
                registered_document_count=0,
                error_message=str(exc),
            )
        finally:
            tracemalloc.stop()

    def run_scale_sweep(
        self,
        *,
        scale_points: tuple[int, ...] = (5, 25, 50, 100, 250, 500),
    ) -> ScaleBenchmarkReport:
        """Run benchmarks across multiple corpus sizes."""

        results = tuple(self.run_corpus(count) for count in scale_points)
        environment: dict[str, object] = {
            "hardware_note": "local benchmark runner",
            "platform": platform.platform(),
            "python_version": sys.version.split()[0],
        }

        return ScaleBenchmarkReport(
            environment=environment,
            corpus_results=results,
            scale_points=scale_points,
        )

    @staticmethod
    def _classify_verification(
        *,
        document_count: int,
        registered: int,
        graph_nodes: int,
    ) -> ScaleVerificationResult:
        if registered != document_count or graph_nodes < document_count:
            return ScaleVerificationResult.PARTIALLY_VERIFIED

        if document_count <= 25:
            return ScaleVerificationResult.VERIFIED

        if document_count <= 100:
            return ScaleVerificationResult.PARTIALLY_VERIFIED

        return ScaleVerificationResult.CHARACTERIZED
