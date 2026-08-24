"""Material ↔ property binding with temperature, pressure, and source."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.interface.engineering_query import MaterialCard
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.property import PropertyDefinition, PropertyValue
from knowledge.repositories.property_repository import PropertyRepository

__all__ = ("BoundMaterialProperty", "bind_property_value", "material_card")


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundMaterialProperty:
    material: MaterialCard
    definition: PropertyDefinition
    value: PropertyValue


def material_card(
    *,
    material_id: str,
    name: str,
    aliases: tuple[str, ...],
    classification: str,
    provenance: ProvenanceTrace,
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.APPROVED,
) -> MaterialCard:
    return MaterialCard(
        material_id=material_id,
        name=name,
        aliases=aliases,
        classification=classification,
        lifecycle=lifecycle,
        source_reference_id=provenance.source_reference_id,
    )


def bind_property_value(
    repository: PropertyRepository,
    definition: PropertyDefinition,
    value: PropertyValue,
    material: MaterialCard,
) -> BoundMaterialProperty:
    if value.property_id != definition.property_id:
        raise ValueError("property value does not match definition.")
    if value.material_id not in {None, material.material_id}:
        raise ValueError("property value is bound to a different material.")
    if value.lifecycle is KnowledgeLifecycle.APPROVED and value.validity_range is None:
        raise ValueError("approved property values require a validity range.")
    if value.lifecycle is KnowledgeLifecycle.APPROVED and value.provenance.source_reference_id.strip() == "":
        raise ValueError("approved property values require a source.")
    repository.definitions.create(definition) if _missing(repository.definitions, definition.property_id) else None
    repository.values.create(value)
    return BoundMaterialProperty(material=material, definition=definition, value=value)


def _missing(repository: object, entity_id: str) -> bool:
    try:
        repository.get(entity_id)  # type: ignore[attr-defined]
    except Exception:
        return True
    return False
