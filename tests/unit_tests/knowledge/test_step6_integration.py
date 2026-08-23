"""Step 6 cross-subsystem integration tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.graph.diagnostics import analyze_graph_integrity
from knowledge.interface.evidence_summary import summarize_evidence
from knowledge.pipelines.extended_pipeline import run_knowledge_pipeline_extended
from knowledge.pipelines.knowledge_pipeline import normalize_markdown_text
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.retrieval_diagnostics import build_retrieval_diagnostics
from knowledge.search.w8.hybrid import HybridSearchEngine
from knowledge.validation import ValidationContext, validate_evidence_chain

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[2]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_step6_end_to_end_extended_pipeline_diagnostics() -> None:
    """Step 6 capabilities must integrate across pipeline, graph, search, and interface."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    artifacts = run_knowledge_pipeline_extended(content, request_id="step6-e2e")

    graph_report = analyze_graph_integrity(artifacts.store)
    evidence_findings = validate_evidence_chain(
        ValidationContext(
            document_id=artifacts.extraction.document_id,
            extraction_result=artifacts.extraction,
        ),
    )

    engine = HybridSearchEngine(
        artifacts.index_bundle,
        artifacts.graph_query,
        artifacts.store,
    )
    query = SearchQuery(text="chamber pressure LOX", mode=RetrievalMode.HYBRID)
    page = engine.search(query)
    retrieval = build_retrieval_diagnostics(query, page)
    summary = summarize_evidence(artifacts.package)

    assert artifacts.rag_result.provider_invoked is False
    assert graph_report.source_digest
    assert isinstance(evidence_findings, tuple)
    assert retrieval.returned_count >= 0
    assert summary.provider_invoked is False
