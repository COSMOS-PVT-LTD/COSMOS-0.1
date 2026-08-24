"""DesignRule model tests."""

from __future__ import annotations

from knowledge.models.design_rule import DesignRule
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace


def test_approved_design_rule_requires_approval() -> None:
    rule = DesignRule(
        rule_id="RULE-1",
        statement="Maximum wall temperature shall not exceed the material limit.",
        formula="T_wall <= T_limit",
        parameters=("T_wall", "T_limit"),
        applicability="regenerative chambers",
        authority="seed",
        severity="CRITICAL",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        lifecycle=KnowledgeLifecycle.APPROVED,
        approval="reviewer",
    )
    assert rule.approval == "reviewer"
