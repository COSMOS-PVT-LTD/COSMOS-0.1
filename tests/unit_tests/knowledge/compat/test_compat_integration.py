"""Integration tests — compatibility facades delegate to canonical implementations."""

from __future__ import annotations

from pathlib import Path

from knowledge.pipelines.knowledge_pipeline import normalize_markdown_text, run_knowledge_pipeline
from tests.integration_tests.kg_block012.helpers.pipeline import run_full_pipeline

_GOLDEN_DOCUMENT = (
    Path(__file__).resolve().parents[3]
    / "integration_tests"
    / "kg_block012"
    / "fixtures"
    / "documents"
    / "golden_propulsion_spec.md"
)


def test_compat_pipeline_matches_block012_integration_path() -> None:
    """COMPAT-006 orchestration must align with BLOCK-012 qualification pipeline."""

    content = normalize_markdown_text(_GOLDEN_DOCUMENT.read_text(encoding="utf-8"))
    compat = run_knowledge_pipeline(
        content,
        task="Qualify propulsion specification evidence",
        query_text="chamber pressure LOX",
        request_id="block012-e2e",
    )
    canonical = run_full_pipeline(
        content,
        task="Qualify propulsion specification evidence",
        query_text="chamber pressure LOX",
        request_id="block012-e2e",
    )

    assert len(compat.extraction.entities) == len(canonical.extraction.entities)
    assert compat.validation_report.is_valid == canonical.validation_report.is_valid
    assert compat.index_bundle.source_digest == canonical.index_bundle.source_digest
    assert compat.rag_result.package_digest == canonical.rag_result.package_digest
    assert compat.rag_result.provider_invoked is False
    assert compat.package.package_digest == canonical.package.package_digest
