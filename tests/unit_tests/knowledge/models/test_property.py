"""Property definition and value tests."""

from __future__ import annotations

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.property import PropertyDefinition, PropertyValue


def test_approved_property_value_has_source_and_range() -> None:
    value = PropertyValue(
        value_id="PV-1",
        property_id="PROP-DENSITY",
        material_id="MAT-WATER",
        numeric_value=997.0,
        unit="kg/m^3",
        provenance=ProvenanceTrace(source_reference_id="REF-1", document_id="DOC-1"),
        temperature_k=298.15,
        validity_range="273-373 K",
        lifecycle=KnowledgeLifecycle.APPROVED,
    )
    assert value.temperature_k == 298.15
    definition = PropertyDefinition(
        property_id="PROP-DENSITY",
        name="density",
        symbol="rho",
        dimension="M L^-3",
        unit="kg/m^3",
        description="mass density",
    )
    assert definition.symbol == "rho"
