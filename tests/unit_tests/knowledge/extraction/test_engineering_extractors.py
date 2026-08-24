"""Extractor tests — candidates are never auto-approved."""

from __future__ import annotations

from knowledge.extraction.correlation_extractor import extract_correlations
from knowledge.extraction.physical_law_extractor import extract_physical_laws
from knowledge.models.lifecycle import KnowledgeLifecycle


def test_extractors_emit_candidates_only() -> None:
    text = "Fourier's Law and the Bartz correlation apply. Assume coolant is single-phase."
    laws = extract_physical_laws(text, document_id="DOC-1", reference_id="REF-1")
    corrs = extract_correlations(text, document_id="DOC-1", reference_id="REF-1")
    assert laws
    assert corrs
    assert all(item.lifecycle is KnowledgeLifecycle.CANDIDATE for item in laws)
    assert all(item.lifecycle is KnowledgeLifecycle.CANDIDATE for item in corrs)
