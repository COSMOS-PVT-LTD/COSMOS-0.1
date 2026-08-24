"""Populate the engineering domain taxonomy and aliases (additive)."""

from __future__ import annotations

from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology.exceptions import OntologyTermNotFoundError
from knowledge.ontology.models import OntologyAlias, OntologyTerm, TaxonomyEdge
from knowledge.ontology.registry import OntologyRegistry

__all__ = (
    "ENGINEERING_TAXONOMY",
    "ENGINEERING_ALIASES",
    "populate_engineering_taxonomy",
    "resolve_engineering_alias",
)

ENGINEERING_TAXONOMY: tuple[tuple[str, str, str | None], ...] = (
    ("ONT-ENGINEERING", "Engineering", None),
    ("ONT-AEROSPACE", "Aerospace", "ONT-ENGINEERING"),
    ("ONT-ROCKET-PROPULSION", "Rocket Propulsion", "ONT-AEROSPACE"),
    ("ONT-LIQUID-ROCKET", "Liquid Rocket", "ONT-ROCKET-PROPULSION"),
    ("ONT-SOLID-ROCKET", "Solid Rocket", "ONT-ROCKET-PROPULSION"),
    ("ONT-HYBRID-ROCKET", "Hybrid Rocket", "ONT-ROCKET-PROPULSION"),
    ("ONT-FLUID-MECHANICS", "Fluid Mechanics", "ONT-ENGINEERING"),
    ("ONT-INCOMPRESSIBLE", "Incompressible Flow", "ONT-FLUID-MECHANICS"),
    ("ONT-COMPRESSIBLE", "Compressible Flow", "ONT-FLUID-MECHANICS"),
    ("ONT-THERMODYNAMICS", "Thermodynamics", "ONT-ENGINEERING"),
    ("ONT-THERMOCHEMISTRY", "Thermochemistry", "ONT-ENGINEERING"),
    ("ONT-COMBUSTION", "Combustion", "ONT-ENGINEERING"),
    ("ONT-HEAT-TRANSFER", "Heat Transfer", "ONT-ENGINEERING"),
    ("ONT-CRYOGENICS", "Cryogenics", "ONT-ENGINEERING"),
    ("ONT-MATERIALS", "Materials", "ONT-ENGINEERING"),
    ("ONT-STRUCTURES", "Structures", "ONT-ENGINEERING"),
    ("ONT-MANUFACTURING", "Manufacturing", "ONT-ENGINEERING"),
    ("ONT-TURBOMACHINERY", "Turbomachinery", "ONT-ENGINEERING"),
    ("ONT-CONTROLS", "Controls", "ONT-ENGINEERING"),
    ("ONT-RELIABILITY", "Reliability", "ONT-ENGINEERING"),
    ("ONT-OPTIMIZATION", "Optimization", "ONT-ENGINEERING"),
    ("ONT-LOX", "Liquid Oxygen", "ONT-CRYOGENICS"),
    ("ONT-METHANE", "Methane", "ONT-CRYOGENICS"),
    ("ONT-REYNOLDS", "Reynolds Number", "ONT-FLUID-MECHANICS"),
    ("ONT-BARTZ", "Bartz Correlation", "ONT-HEAT-TRANSFER"),
)

ENGINEERING_ALIASES: tuple[tuple[str, str], ...] = (
    ("LOX", "ONT-LOX"),
    ("Liquid Oxygen", "ONT-LOX"),
    ("O2(l)", "ONT-LOX"),
    ("oxygen - liquid", "ONT-LOX"),
    ("Methane", "ONT-METHANE"),
    ("CH4", "ONT-METHANE"),
    ("LNG methane", "ONT-METHANE"),
    ("Re", "ONT-REYNOLDS"),
    ("Reynolds number", "ONT-REYNOLDS"),
    ("Bartz", "ONT-BARTZ"),
)


def populate_engineering_taxonomy(registry: OntologyRegistry) -> None:
    existing = {term.term_id for term in registry.list_terms()}
    for term_id, name, _parent in ENGINEERING_TAXONOMY:
        if term_id in existing:
            continue
        entity_type = CanonicalEntityType.MATERIAL if term_id in {"ONT-LOX", "ONT-METHANE"} else CanonicalEntityType.ENGINEERING_DOMAIN
        registry.register_term(
            OntologyTerm(
                term_id=term_id,
                canonical_name=name,
                entity_type=entity_type,
            ),
        )
    for term_id, _name, parent in ENGINEERING_TAXONOMY:
        if parent is None:
            continue
        existing_children = {child.term_id for child in registry.children_of(parent)}
        if term_id in existing_children:
            continue
        registry.register_taxonomy_edge(
            TaxonomyEdge(parent_term_id=parent, child_term_id=term_id),
        )
    for alias, term_id in ENGINEERING_ALIASES:
        registry.register_alias(OntologyAlias(alias=alias, canonical_term_id=term_id))


def resolve_engineering_alias(registry: OntologyRegistry, label: str) -> OntologyTerm:
    try:
        return registry.resolve_alias(label)
    except OntologyTermNotFoundError:
        needle = label.strip().casefold()
        for alias in registry.list_aliases():
            if alias.alias.casefold() == needle:
                return registry.get_term(alias.canonical_term_id)
        raise
