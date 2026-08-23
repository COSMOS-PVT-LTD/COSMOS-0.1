"""Step 6 evidence summary tests."""

from __future__ import annotations

from pathlib import Path

from knowledge.interface.evidence_summary import summarize_evidence
from knowledge.pipelines.extended_pipeline import run_knowledge_pipeline_extended
from knowledge.pipelines.knowledge_pipeline import normalize_markdown_text

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_summarize_evidence_reports_provider_invoked_false() -> None:
    """Evidence summary must preserve controlled local RAG trust boundary."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    artifacts = run_knowledge_pipeline_extended(content, request_id="step6-summary")
    summary = summarize_evidence(
        artifacts.package,
        constraint_labels=("evidence-only",),
    )

    assert summary.provider_invoked is False
    assert summary.evidence_count >= 0
    assert summary.package_id == artifacts.package.package_id


def test_summarize_evidence_is_deterministic() -> None:
    """Evidence summary must be deterministic."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    artifacts = run_knowledge_pipeline_extended(content, request_id="step6-summary-det")
    first = summarize_evidence(artifacts.package)
    second = summarize_evidence(artifacts.package)

    assert first.summary_digest == second.summary_digest
