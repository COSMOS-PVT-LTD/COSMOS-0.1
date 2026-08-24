"""FailureMode model tests."""

from __future__ import annotations

from knowledge.models.failure_mode import FailureMode
from knowledge.models.lifecycle import ProvenanceTrace


def test_failure_mode_links_design_rules() -> None:
    mode = FailureMode(
        failure_mode_id="FM-BURN",
        name="burn-through",
        mechanism="wall temperature exceeds capability",
        cause="insufficient cooling",
        effect="wall rupture",
        severity="CATASTROPHIC",
        likelihood="MEDIUM",
        mitigation="wall-temperature rule",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        design_rule_ids=("RULE-TWALL-MAX",),
    )
    assert mode.design_rule_ids == ("RULE-TWALL-MAX",)
