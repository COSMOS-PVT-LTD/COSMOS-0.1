"""Production benchmark suite for local RAG qualification (Step 7 gate closure)."""

from __future__ import annotations

import json
import resource
import tracemalloc
from dataclasses import dataclass
from pathlib import Path

from knowledge.production.local_rag_pipeline import ProductionLocalRAGPipeline
from knowledge.production.performance import PerformanceBenchmark

__all__ = (
    "BenchmarkEnvelope",
    "ProductionBenchmarkSuite",
    "ProductionBenchmarkReport",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class BenchmarkEnvelope:
    """Explicit benchmark scope — no fabricated production-scale claims."""

    single_document: bool
    multi_document: bool
    document_count: int
    corpus_size_label: str
    hardware_note: str = "local developer machine"
    verified_scale: str
    unverified_scale: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProductionBenchmarkReport:
    """Aggregate benchmark report with resource measurements."""

    envelope: BenchmarkEnvelope
    summaries: tuple[dict[str, object], ...]
    peak_memory_bytes: int
    storage_footprint_bytes: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "envelope": {
                "corpus_size_label": self.envelope.corpus_size_label,
                "document_count": self.envelope.document_count,
                "hardware_note": self.envelope.hardware_note,
                "multi_document": self.envelope.multi_document,
                "single_document": self.envelope.single_document,
                "unverified_scale": self.envelope.unverified_scale,
                "verified_scale": self.envelope.verified_scale,
            },
            "peak_memory_bytes": self.peak_memory_bytes,
            "storage_footprint_bytes": self.storage_footprint_bytes,
            "summaries": list(self.summaries),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_mapping(), indent=2, sort_keys=True)


def _directory_size(path: Path) -> int:
    total = 0

    if not path.exists():
        return 0

    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size

    return total


class ProductionBenchmarkSuite:
    """Measure local RAG operations at an explicitly declared scale."""

    def __init__(self, *, store_root: Path) -> None:
        self._store_root = store_root
        self._benchmark = PerformanceBenchmark()

    def run(
        self,
        *,
        documents: tuple[tuple[str, str, str, str], ...],
        query_text: str,
        warm_iterations: int = 2,
    ) -> ProductionBenchmarkReport:
        """Run cold/warm ingest, index, query, persistence, and recovery benchmarks."""

        tracemalloc.start()
        pipeline = ProductionLocalRAGPipeline(self._store_root)
        pipeline.initialize()

        for document_id, source_id, artifact_id, content in documents:
            self._benchmark.time_operation(
                "ingestion.end_to_end",
                lambda d=document_id, s=source_id, a=artifact_id, c=content: pipeline.ingest_document(
                    document_id=d,
                    source_id=s,
                    artifact_id=a,
                    content=c,
                    query_text=query_text,
                ),
            )

        first_doc_id = documents[0][0]

        self._benchmark.time_operation(
            "persistence.load_store",
            lambda: ProductionLocalRAGPipeline(self._store_root).initialize(),
        )

        restarted = ProductionLocalRAGPipeline(self._store_root)
        restarted.initialize()

        self._benchmark.time_operation(
            "recovery.recover",
            restarted.recover,
        )

        self._benchmark.time_operation(
            "query.cold_start",
            lambda: pipeline.query(
                task="Benchmark cold query",
                query_text=query_text,
                document_id=first_doc_id,
                request_id="benchmark-cold",
            ),
        )

        for index in range(warm_iterations):
            self._benchmark.time_operation(
                f"query.warm.{index}",
                lambda idx=index: pipeline.query(
                    task="Benchmark warm query",
                    query_text=query_text,
                    document_id=first_doc_id,
                    request_id=f"benchmark-warm-{idx}",
                ),
            )

        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        peak_memory = max(peak, rss * 1024 if rss else 0)
        storage_footprint = _directory_size(self._store_root)

        envelope = BenchmarkEnvelope(
            single_document=len(documents) == 1,
            multi_document=len(documents) > 1,
            document_count=len(documents),
            corpus_size_label=f"{len(documents)}-document fixture corpus",
            verified_scale="1-5 documents, short markdown fixtures",
            unverified_scale="100+ documents, large engineering corpora",
        )

        operations = (
            "ingestion.end_to_end",
            "persistence.load_store",
            "recovery.recover",
            "query.cold_start",
            *(f"query.warm.{index}" for index in range(warm_iterations)),
        )
        summaries = tuple(
            self._benchmark.summarize(operation).to_mapping()
            for operation in operations
        )

        return ProductionBenchmarkReport(
            envelope=envelope,
            summaries=summaries,
            peak_memory_bytes=peak_memory,
            storage_footprint_bytes=storage_footprint,
        )
