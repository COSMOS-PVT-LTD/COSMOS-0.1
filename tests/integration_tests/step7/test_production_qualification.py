"""Step 7 production qualification integration tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.production import PerformanceBenchmark, ProductionLocalRAGPipeline

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[1]
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_production_qualification_end_to_end(tmp_path) -> None:
    """Production qualification path: ingest → persist → index → retrieve → RAG."""

    content = _GOLDEN_DOCUMENT.read_text(encoding="utf-8")
    pipeline = ProductionLocalRAGPipeline(tmp_path)
    pipeline.initialize()

    benchmark = PerformanceBenchmark()
    benchmark.time_operation(
        "ingest",
        lambda: pipeline.ingest_document(
            document_id="DOC-QUAL",
            source_id="SRC-QUAL",
            artifact_id="ART-QUAL",
            content=content,
        ),
    )

    result = pipeline.query(
        task="Step 7 qualification",
        query_text="chamber pressure LOX",
        document_id="DOC-QUAL",
        request_id="step7-qualification",
    )

    ingest_summary = benchmark.summarize("ingest")

    assert result.provider_invoked is False
    assert ingest_summary.sample_count == 1
    assert pipeline.observability.summary()["event_count"] >= 1
