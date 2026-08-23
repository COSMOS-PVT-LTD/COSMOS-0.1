"""COMPAT-006 — knowledge pipeline facade tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.pipelines.knowledge_pipeline import (
    KnowledgePipelineArtifacts,
    normalize_markdown_text,
    run_knowledge_pipeline,
)

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_normalize_markdown_text_matches_integration_helper() -> None:
    """normalize_markdown_text must apply deterministic line normalization."""

    raw = "# Title\r\n\r\nBody\r\n"
    normalized = normalize_markdown_text(raw)

    assert normalized == "# Title\n\nBody\n"


def test_run_knowledge_pipeline_produces_full_artifact_chain() -> None:
    """run_knowledge_pipeline must execute W1→W11 and return artifacts."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    artifacts = run_knowledge_pipeline(
        content,
        task="COMPAT-006 qualification",
        query_text="chamber pressure LOX",
        request_id="compat-pipeline-001",
    )

    assert isinstance(artifacts, KnowledgePipelineArtifacts)
    assert artifacts.extraction.document_id
    assert artifacts.validation_report.is_valid
    assert artifacts.store is not None
    assert artifacts.index_bundle.source_digest
    assert artifacts.rag_result.provider_invoked is False
    assert artifacts.package.package_digest
    assert artifacts.payload.payload_digest


def test_run_knowledge_pipeline_is_deterministic() -> None:
    """Repeated pipeline runs must produce identical RAG digests."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    first = run_knowledge_pipeline(content, request_id="compat-determinism")
    second = run_knowledge_pipeline(content, request_id="compat-determinism")

    assert first.index_bundle.source_digest == second.index_bundle.source_digest
    assert first.rag_result.package_digest == second.rag_result.package_digest
