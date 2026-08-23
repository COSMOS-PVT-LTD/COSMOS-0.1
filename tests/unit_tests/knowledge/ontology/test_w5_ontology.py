"""Unit tests for KG-BLOCK-008 W5 ontology (KG-024 → KG-027)."""

from __future__ import annotations

import pytest

from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology import (
    AliasConflictError,
    CanonicalizationStatus,
    DuplicateOntologyTermError,
    OntologyAlias,
    OntologyRegistry,
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    OntologyRelationshipError,
    OntologyTerm,
    OntologyTermNotFoundError,
    OntologyValidationError,
    TaxonomyCycleError,
    TaxonomyEdge,
    ancestors_of,
    canonicalize_entity_candidate,
    canonicalize_extraction_result,
    children_of,
    descendants_of,
    deterministic_ontology_id,
    list_aliases,
    normalize_observed_term,
    register_alias,
    register_relationship_rule,
    register_taxonomy_edge,
    resolve_canonical_term_id,
    validate_relationship,
)
from tests.unit_tests.knowledge.extraction.test_w4_extraction import _parse_and_extract


def _build_registry() -> OntologyRegistry:
    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-material-lox",
            canonical_name="Liquid Oxygen",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="LOX",
                    canonical_term_id="term-material-lox",
                ),
            ),
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-engine-lre",
            canonical_name="Liquid Rocket Engine",
            entity_type=CanonicalEntityType.SUBSYSTEM,
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-prop-cryo",
            canonical_name="Cryogenic Propellant",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-prop",
            canonical_name="Propellant",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )
    return registry


def test_canonicalize_known_term_by_alias() -> None:
    """KG-024 must resolve known aliases to canonical ontology terms."""

    registry = _build_registry()
    extraction = _parse_and_extract("Material: LOX\n")
    entity = next(
        item for item in extraction.entities if item.extracted_label == "LOX"
    )

    mapping = canonicalize_entity_candidate(entity, registry)

    assert mapping.status is CanonicalizationStatus.RESOLVED
    assert mapping.canonical_term_id == "term-material-lox"
    assert mapping.provenance == entity.provenance


def test_unknown_term_remains_unresolved() -> None:
    """KG-024 must leave unknown terms unresolved rather than inventing facts."""

    registry = _build_registry()
    extraction = _parse_and_extract("Material: Unobtainium-9000\n")
    entity = next(item for item in extraction.entities)

    mapping = canonicalize_entity_candidate(entity, registry)

    assert mapping.status is CanonicalizationStatus.UNRESOLVED
    assert mapping.canonical_term_id is None


def test_canonicalization_is_deterministic() -> None:
    """KG-024 must produce identical mappings for repeated input."""

    registry = _build_registry()
    extraction = _parse_and_extract("Material: LOX\n")

    first = canonicalize_extraction_result(extraction, registry)
    second = canonicalize_extraction_result(extraction, registry)

    assert first.to_mapping() == second.to_mapping()


def test_canonicalization_collision_prevention_via_distinct_ids() -> None:
    """KG-024 must keep distinct mapping IDs for distinct candidates."""

    registry = _build_registry()
    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Section A",
                "Material: LOX",
                "# Section B",
                "Material: LOX",
            ],
        ),
    )
    result = canonicalize_extraction_result(extraction, registry)
    lox_mappings = [
        mapping
        for mapping in result.mappings
        if mapping.observed_label == "LOX"
    ]

    assert len(lox_mappings) == 2
    assert lox_mappings[0].mapping_id != lox_mappings[1].mapping_id


def test_register_alias_and_resolve() -> None:
    """KG-025 must register and resolve aliases deterministically."""

    registry = _build_registry()
    register_alias(
        registry,
        alias="liquid oxygen",
        canonical_term_id="term-material-lox",
    )

    assert resolve_canonical_term_id(registry, "liquid oxygen") == "term-material-lox"
    assert len(list_aliases(registry)) >= 2


def test_duplicate_alias_rejection() -> None:
    """KG-025 must reject duplicate alias registration."""

    registry = _build_registry()

    with pytest.raises(AliasConflictError):
        register_alias(
            registry,
            alias="LOX",
            canonical_term_id="term-engine-lre",
        )


def test_alias_normalization_preserves_case_sensitive_symbols() -> None:
    """KG-025 must not treat CO and Co as interchangeable."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-co",
            canonical_name="Carbon Monoxide",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-cobalt",
            canonical_name="Cobalt",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="Co",
                    canonical_term_id="term-cobalt",
                ),
            ),
        ),
    )

    assert resolve_canonical_term_id(registry, "Co") == "term-cobalt"
    assert resolve_canonical_term_id(registry, "CO") is None


def test_taxonomy_parent_child_and_traversal() -> None:
    """KG-026 must support hierarchical taxonomy traversal."""

    registry = _build_registry()
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop",
        child_term_id="term-prop-cryo",
    )
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop-cryo",
        child_term_id="term-material-lox",
    )

    assert [item.term_id for item in children_of(registry, "term-prop")] == [
        "term-prop-cryo",
    ]
    assert [item.term_id for item in descendants_of(registry, "term-prop")] == [
        "term-prop-cryo",
        "term-material-lox",
    ]
    assert [item.term_id for item in ancestors_of(registry, "term-material-lox")] == [
        "term-prop-cryo",
        "term-prop",
    ]


def test_taxonomy_missing_parent_rejection() -> None:
    """KG-026 must reject edges when parent term does not exist."""

    registry = _build_registry()

    with pytest.raises(OntologyTermNotFoundError):
        register_taxonomy_edge(
            registry,
            parent_term_id="missing-parent",
            child_term_id="term-material-lox",
        )


def test_taxonomy_cycle_detection() -> None:
    """KG-026 must reject taxonomy cycles."""

    registry = _build_registry()
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop",
        child_term_id="term-prop-cryo",
    )
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop-cryo",
        child_term_id="term-material-lox",
    )

    with pytest.raises(TaxonomyCycleError):
        register_taxonomy_edge(
            registry,
            parent_term_id="term-material-lox",
            child_term_id="term-prop",
        )


def test_taxonomy_duplicate_edge_rejection() -> None:
    """KG-026 must reject duplicate parent-child edges."""

    registry = _build_registry()
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop",
        child_term_id="term-prop-cryo",
    )

    with pytest.raises(TaxonomyCycleError):
        register_taxonomy_edge(
            registry,
            parent_term_id="term-prop",
            child_term_id="term-prop-cryo",
        )


def test_relationship_rule_validation_permits_valid_relationship() -> None:
    """KG-027 must permit relationships covered by registered rules."""

    registry = _build_registry()
    register_relationship_rule(
        registry,
        OntologyRelationshipRule(
            rule_id="rule-is-a-material",
            relationship_type=OntologyRelationshipRuleType.IS_A,
            source_entity_type=CanonicalEntityType.MATERIAL,
            target_entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    result = validate_relationship(
        registry,
        source_term_id="term-material-lox",
        target_term_id="term-prop-cryo",
        relationship_type=OntologyRelationshipRuleType.IS_A,
    )

    assert result.permitted is True
    assert result.rule_id == "rule-is-a-material"


def test_relationship_rule_validation_rejects_invalid_relationship() -> None:
    """KG-027 must reject relationships without matching rules."""

    registry = _build_registry()

    result = validate_relationship(
        registry,
        source_term_id="term-material-lox",
        target_term_id="term-engine-lre",
        relationship_type=OntologyRelationshipRuleType.PART_OF,
    )

    assert result.permitted is False
    assert "No matching ontology relationship rule" in result.reason


def test_duplicate_relationship_rule_rejection() -> None:
    """KG-027 must reject duplicate relationship rule identifiers."""

    registry = _build_registry()
    rule = OntologyRelationshipRule(
        rule_id="rule-uses",
        relationship_type=OntologyRelationshipRuleType.USES,
        source_entity_type=CanonicalEntityType.SUBSYSTEM,
        target_entity_type=CanonicalEntityType.MATERIAL,
    )

    register_relationship_rule(registry, rule)

    with pytest.raises(OntologyRelationshipError):
        register_relationship_rule(registry, rule)


def test_registry_state_is_order_independent() -> None:
    """Ontology registry digest must be stable across registration order."""

    first = OntologyRegistry()
    second = OntologyRegistry()

    term_a = OntologyTerm(
        term_id="term-a",
        canonical_name="Alpha",
        entity_type=CanonicalEntityType.MATERIAL,
    )
    term_b = OntologyTerm(
        term_id="term-b",
        canonical_name="Beta",
        entity_type=CanonicalEntityType.MATERIAL,
    )

    first.register_term(term_a)
    first.register_term(term_b)
    second.register_term(term_b)
    second.register_term(term_a)

    assert first.registry_digest() == second.registry_digest()


def test_w4_to_w5_integration_preserves_provenance() -> None:
    """Integration must run W4 extraction through W5 canonicalization with provenance."""

    registry = _build_registry()
    register_taxonomy_edge(
        registry,
        parent_term_id="term-prop",
        child_term_id="term-material-lox",
    )
    register_relationship_rule(
        registry,
        OntologyRelationshipRule(
            rule_id="rule-made-of",
            relationship_type=OntologyRelationshipRuleType.MADE_OF,
            source_entity_type=CanonicalEntityType.SUBSYSTEM,
            target_entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    extraction = _parse_and_extract(
        "\n".join(
            [
                "# Propulsion",
                "Material: LOX",
                "The chamber pressure is 20 bar.",
            ],
        ),
    )
    canonical = canonicalize_extraction_result(extraction, registry)
    lox_mapping = next(
        mapping
        for mapping in canonical.mappings
        if mapping.observed_label == "LOX"
    )

    assert lox_mapping.status is CanonicalizationStatus.RESOLVED
    assert lox_mapping.provenance.anchor.source_id == "SRC-001"
    assert validate_relationship(
        registry,
        source_term_id="term-engine-lre",
        target_term_id="term-material-lox",
        relationship_type=OntologyRelationshipRuleType.MADE_OF,
    ).permitted is True


def test_normalize_observed_term_rejects_blank() -> None:
    """Validation must reject blank observed terms."""

    with pytest.raises(ValueError):
        normalize_observed_term("   ")


def test_taxonomy_edge_rejects_self_parent() -> None:
    """Taxonomy edges must reject self-parent relationships."""

    with pytest.raises(OntologyValidationError):
        TaxonomyEdge(parent_term_id="term-a", child_term_id="term-a")


def test_deterministic_ontology_id_is_stable() -> None:
    """Ontology identity generation must be deterministic."""

    first = deterministic_ontology_id("ont", "DOC-001", "part")
    second = deterministic_ontology_id("ont", "DOC-001", "part")

    assert first == second


def test_duplicate_term_registration_rejected() -> None:
    """Registry must reject duplicate ontology term identifiers."""

    registry = OntologyRegistry()
    term = OntologyTerm(
        term_id="term-001",
        canonical_name="Example",
        entity_type=CanonicalEntityType.OTHER,
    )

    registry.register_term(term)

    with pytest.raises(DuplicateOntologyTermError):
        registry.register_term(term)
