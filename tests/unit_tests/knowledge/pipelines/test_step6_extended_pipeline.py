"""Step 6 extended pipeline tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.pipelines.extended_pipeline import run_knowledge_pipeline_extended
from knowledge.pipelines.knowledge_pipeline import normalize_markdown_text, run_knowledge_pipeline

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_extended_pipeline_includes_phase_c_validation_findings() -> None:
    """Extended pipeline must wire parsed_document and Phase-C validation."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    base = run_knowledge_pipeline(content, request_id="step6-base")
    extended = run_knowledge_pipeline_extended(content, request_id="step6-extended")

    assert extended.rag_result.provider_invoked is False
    assert len(extended.validation_report.findings) >= len(
        base.validation_report.findings,
    )
    assert any(
        finding.rule_id.startswith("VAL-CIT")
        or finding.rule_id.startswith("VAL-AMB")
        for finding in extended.validation_report.findings
    )


def test_extended_pipeline_preserves_graph_and_index_digests() -> None:
    """Extended validation must not alter graph construction or index digests."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    base = run_knowledge_pipeline(content, request_id="step6-digest-parity")
    extended = run_knowledge_pipeline_extended(
        content,
        request_id="step6-digest-parity",
    )

    assert base.index_bundle.source_digest == extended.index_bundle.source_digest
    assert base.extraction.document_id == extended.extraction.document_id


def test_extended_pipeline_is_deterministic() -> None:
    """Repeated extended pipeline runs must be deterministic."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    first = run_knowledge_pipeline_extended(content, request_id="step6-determinism")
    second = run_knowledge_pipeline_extended(content, request_id="step6-determinism")

    assert first.validation_report.report_digest == second.validation_report.report_digest
    assert first.rag_result.package_digest == second.rag_result.package_digest
