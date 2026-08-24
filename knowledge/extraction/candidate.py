"""Shared candidate-extraction contract — extractors never approve."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("candidate_provenance",)


def candidate_provenance(document_id: str, reference_id: str) -> ProvenanceTrace:
    return ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        extraction_method="pattern-candidate",
    )


def assert_candidate(lifecycle: KnowledgeLifecycle) -> None:
    if lifecycle is KnowledgeLifecycle.APPROVED:
        raise ValueError("Extractors must not emit APPROVED entities.")
