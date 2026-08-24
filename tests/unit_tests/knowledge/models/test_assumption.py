"""Assumption model tests."""

from __future__ import annotations

from knowledge.models.assumption import Assumption
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace


def test_approved_assumption_has_approver() -> None:
    assumption = Assumption(
        assumption_id="ASM-1",
        statement="Coolant is single-phase.",
        category="thermal",
        affected_entity_ids=("CORR-BARTZ",),
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        justification="application envelope",
        applicability="no bulk boiling",
        confidence=0.8,
        lifecycle=KnowledgeLifecycle.APPROVED,
        approved_by="reviewer",
    )
    assert assumption.approved_by == "reviewer"
