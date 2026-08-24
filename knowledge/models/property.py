"""Property definition vs measured/tabulated property value."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, UncertaintyRecord

__all__ = ("PropertyDefinition", "PropertyValue")


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyDefinition:
    """Definition of an engineering property (density, viscosity, ...)."""

    property_id: str
    name: str
    symbol: str
    dimension: str
    unit: str
    description: str
    domain: str = "MATERIALS"

    def __post_init__(self) -> None:
        if not self.property_id.strip() or not self.name.strip():
            raise ValueError("property_id and name are required.")
        if not self.symbol.strip() or not self.unit.strip():
            raise ValueError("symbol and unit are required.")


@dataclass(frozen=True, slots=True, kw_only=True)
class PropertyValue:
    """A sourced property value with validity range — never a bare number."""

    value_id: str
    property_id: str
    material_id: str | None
    numeric_value: float
    unit: str
    provenance: ProvenanceTrace
    temperature_k: float | None = None
    pressure_pa: float | None = None
    composition: str | None = None
    environment: str | None = None
    manufacturing_condition: str | None = None
    uncertainty: UncertaintyRecord | None = None
    validity_range: str | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE

    def __post_init__(self) -> None:
        if not self.value_id.strip() or not self.property_id.strip():
            raise ValueError("value_id and property_id are required.")
        if not isinstance(self.numeric_value, (int, float)):
            raise ValueError("numeric_value must be numeric.")
        if self.lifecycle is KnowledgeLifecycle.APPROVED and self.validity_range is None:
            raise ValueError("APPROVED property values require a validity range.")
