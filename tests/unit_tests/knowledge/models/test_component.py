"""Component model tests."""

from __future__ import annotations

from knowledge.models.component import Component
from knowledge.models.lifecycle import ProvenanceTrace


def test_component_binds_materials_and_rules() -> None:
    component = Component(
        component_id="COMP-NOZZLE",
        name="Nozzle",
        classification="PROPULSION",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        material_ids=("MAT-GRCOP-42",),
        design_rule_ids=("RULE-TWALL-MAX",),
        failure_mode_ids=("FM-BURNTHROUGH",),
    )
    assert "MAT-GRCOP-42" in component.material_ids
