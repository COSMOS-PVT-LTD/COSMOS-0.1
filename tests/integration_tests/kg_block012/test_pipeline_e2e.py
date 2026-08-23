"""End-to-end pipeline verification for KG-BLOCK-012."""

from __future__ import annotations

from knowledge.reasoning.w10 import EvidenceClassification

from tests.integration_tests.kg_block012.helpers.pipeline import PipelineArtifacts, run_full_pipeline


def test_full_pipeline_executes_without_error(pipeline_artifacts: PipelineArtifacts) -> None:
    """Golden fixture must traverse the complete authorized W1→W11 path."""

    assert pipeline_artifacts.validation_report.report_digest
    assert pipeline_artifacts.payload.payload_digest
    assert pipeline_artifacts.rag_result.package_digest


def test_full_pipeline_preserves_document_identity(pipeline_artifacts: PipelineArtifacts) -> None:
    """Document identity from extraction must survive to interface payload."""

    document_id = pipeline_artifacts.extraction.document_id

    assert pipeline_artifacts.canonical.document_id == document_id
    assert pipeline_artifacts.rag_result.request.query.text


def test_full_pipeline_golden_fixture_is_deterministic() -> None:
    """Repeated golden pipeline execution must produce identical digests."""

    first = run_full_pipeline(request_id="golden-run-1")
    second = run_full_pipeline(request_id="golden-run-1")

    assert first.payload.payload_digest == second.payload.payload_digest
    assert first.rag_result.context.context_digest == second.rag_result.context.context_digest


def test_full_pipeline_outcome_is_evidence_bounded(pipeline_artifacts: PipelineArtifacts) -> None:
    """Pipeline outcome must remain within evidence classification bounds."""

    assert pipeline_artifacts.payload.outcome.classification in {
        EvidenceClassification.SUPPORTED,
        EvidenceClassification.PARTIALLY_SUPPORTED,
        EvidenceClassification.NO_VERIFIED_RESULT,
        EvidenceClassification.UNSUPPORTED,
        EvidenceClassification.CONFLICTED,
    }


def test_full_pipeline_extracts_engineering_content() -> None:
    """Golden fixture must yield extractable engineering entities or quantities."""

    artifacts = run_full_pipeline()

    total_candidates = (
        len(artifacts.extraction.entities)
        + len(artifacts.extraction.quantities)
        + len(artifacts.extraction.claims)
    )
    assert total_candidates > 0
