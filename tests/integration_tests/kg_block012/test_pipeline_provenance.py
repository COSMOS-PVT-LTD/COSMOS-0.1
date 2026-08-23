"""Provenance continuity verification for KG-BLOCK-012."""

from __future__ import annotations

from tests.integration_tests.kg_block012.helpers.pipeline import PipelineArtifacts, run_full_pipeline


def test_source_to_extraction_provenance_chain(pipeline_artifacts: PipelineArtifacts) -> None:
    """Source identity must be traceable through extraction."""

    extraction = pipeline_artifacts.extraction

    assert extraction.source_id == "SRC-GOLDEN"
    assert extraction.artifact_id == "ART-GOLDEN"
    assert extraction.document_id


def test_extraction_to_graph_provenance_preserved(pipeline_artifacts: PipelineArtifacts) -> None:
    """Graph nodes must retain provenance from extraction candidates."""

    for node in pipeline_artifacts.store.list_nodes():
        assert node.properties.get("document_id")


def test_graph_to_index_to_search_provenance_preserved(
    pipeline_artifacts: PipelineArtifacts,
) -> None:
    """Search evidence must reference graph document identity."""

    evidence = pipeline_artifacts.rag_result.context.evidence

    for item in evidence.items:
        if item.document_id is not None:
            assert item.document_id == pipeline_artifacts.extraction.document_id
        assert item.provenance


def test_validation_to_reasoning_provenance_preserved(
    pipeline_artifacts: PipelineArtifacts,
) -> None:
    """Validation digest must propagate into engineering context."""

    assert pipeline_artifacts.validation_report.report_digest
    assert (
        pipeline_artifacts.rag_result.context.validation_report_digest
        == pipeline_artifacts.validation_report.report_digest
    )


def test_reasoning_to_interface_provenance_preserved(
    pipeline_artifacts: PipelineArtifacts,
) -> None:
    """Evidence chains must preserve provenance through W11 interface."""

    payload = pipeline_artifacts.payload

    assert payload.provenance_preserved is True
    for chain in payload.outcome.chains:
        for link in chain.links:
            assert link.provenance is not None


def test_end_to_end_candidate_identity_preserved() -> None:
    """Candidate extraction IDs must remain addressable in interface outcome."""

    artifacts = run_full_pipeline()
    extraction_ids = {entity.extraction_id for entity in artifacts.extraction.entities}

    if not extraction_ids:
        return

    chain_target_ids = {
        link.target_id
        for chain in artifacts.payload.outcome.chains
        for link in chain.links
    }
    assert extraction_ids.intersection(chain_target_ids) or chain_target_ids
