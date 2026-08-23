"""Engineering-review hardening tests for KG-BLOCK-008."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphLifecycleState
from knowledge.graph.entity import CanonicalEntityType
from knowledge.ontology import (
    AliasConflictError,
    CanonicalizationStatus,
    DuplicateOntologyTermError,
    OntologyAlias,
    OntologyRegistry,
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    OntologyTerm,
    OntologyTermNotFoundError,
    TaxonomyCycleError,
    canonicalize_entity_candidate,
    canonicalize_extraction_result,
    register_relationship_rule,
    register_taxonomy_edge,
    resolve_canonical_term_id,
    validate_relationship,
)
from tests.unit_tests.knowledge.extraction.test_w4_extraction import _parse_and_extract


def test_registry_rejects_duplicate_canonical_names() -> None:
    """Registry must reject case-insensitive duplicate canonical names."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-a",
            canonical_name="Liquid Oxygen",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    with pytest.raises(DuplicateOntologyTermError, match="canonical name"):
        registry.register_term(
            OntologyTerm(
                term_id="term-b",
                canonical_name="liquid oxygen",
                entity_type=CanonicalEntityType.MATERIAL,
            ),
        )


def test_canonicalization_treats_ambiguous_canonical_names_as_unresolved() -> None:
    """Canonicalization must not pick arbitrarily among ambiguous canonical names."""

    registry = OntologyRegistry()
    registry._terms["term-a"] = OntologyTerm(
        term_id="term-a",
        canonical_name="Liquid Oxygen",
        entity_type=CanonicalEntityType.MATERIAL,
    )
    registry._terms["term-b"] = OntologyTerm(
        term_id="term-b",
        canonical_name="liquid oxygen",
        entity_type=CanonicalEntityType.MATERIAL,
    )

    assert resolve_canonical_term_id(registry, "LIQUID OXYGEN") is None


def test_canonicalization_does_not_promote_candidate_lifecycle() -> None:
    """W5 canonicalization must not promote W4 candidates to approved facts."""

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
    extraction = _parse_and_extract("Material: LOX\n")
    entity = next(
        item for item in extraction.entities if item.extracted_label == "LOX"
    )

    mapping = canonicalize_entity_candidate(entity, registry)

    assert entity.lifecycle_state is GraphLifecycleState.CANDIDATE
    assert mapping.status is CanonicalizationStatus.RESOLVED
    assert mapping.extraction_id == entity.extraction_id


def test_canonicalization_preserves_candidate_provenance_fields() -> None:
    """Canonical mappings must retain extraction and source provenance."""

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
    extraction = _parse_and_extract("Material: LOX\n")
    entity = next(
        item for item in extraction.entities if item.extracted_label == "LOX"
    )
    mapping = canonicalize_entity_candidate(entity, registry)

    assert mapping.provenance.anchor.source_id == "SRC-001"
    assert mapping.provenance.anchor.document_id == "ART-001"
    assert mapping.provenance.extraction.extractor_tool == "cosmos-w4-extractor"


def test_validate_relationship_rejects_unknown_endpoint() -> None:
    """Relationship validation must fail clearly for unknown ontology terms."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-a",
            canonical_name="Alpha",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    with pytest.raises(OntologyTermNotFoundError):
        validate_relationship(
            registry,
            source_term_id="missing-term",
            target_term_id="term-a",
            relationship_type=OntologyRelationshipRuleType.IS_A,
        )


def test_taxonomy_three_node_cycle_is_rejected() -> None:
    """Taxonomy must reject A→B→C→A cycles."""

    registry = OntologyRegistry()
    for term_id, name in (
        ("term-a", "A"),
        ("term-b", "B"),
        ("term-c", "C"),
    ):
        registry.register_term(
            OntologyTerm(
                term_id=term_id,
                canonical_name=name,
                entity_type=CanonicalEntityType.MATERIAL,
            ),
        )

    register_taxonomy_edge(registry, parent_term_id="term-a", child_term_id="term-b")
    register_taxonomy_edge(registry, parent_term_id="term-b", child_term_id="term-c")

    with pytest.raises(TaxonomyCycleError):
        register_taxonomy_edge(
            registry,
            parent_term_id="term-c",
            child_term_id="term-a",
        )


def test_w4_objects_remain_unchanged_after_canonicalization() -> None:
    """W5 canonicalization must not mutate frozen W4 extraction result objects."""

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
    extraction = _parse_and_extract("Material: LOX\n")
    before = extraction.to_mapping()

    canonicalize_extraction_result(extraction, registry)

    assert extraction.to_mapping() == before


def test_relationship_validation_is_deterministic() -> None:
    """Relationship validation must be stable across repeated evaluation."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-a",
            canonical_name="Alpha",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-b",
            canonical_name="Beta",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )
    register_relationship_rule(
        registry,
        OntologyRelationshipRule(
            rule_id="rule-is-a",
            relationship_type=OntologyRelationshipRuleType.IS_A,
            source_entity_type=CanonicalEntityType.MATERIAL,
            target_entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    first = validate_relationship(
        registry,
        source_term_id="term-a",
        target_term_id="term-b",
        relationship_type=OntologyRelationshipRuleType.IS_A,
    )
    second = validate_relationship(
        registry,
        source_term_id="term-a",
        target_term_id="term-b",
        relationship_type=OntologyRelationshipRuleType.IS_A,
    )

    assert first.to_mapping() == second.to_mapping()


def test_alias_collision_does_not_overwrite_existing_mapping() -> None:
    """Alias registration must not silently remap an existing alias."""

    registry = OntologyRegistry()
    registry.register_term(
        OntologyTerm(
            term_id="term-a",
            canonical_name="Alpha",
            entity_type=CanonicalEntityType.MATERIAL,
            aliases=(
                OntologyAlias(
                    alias="Alias-A",
                    canonical_term_id="term-a",
                ),
            ),
        ),
    )
    registry.register_term(
        OntologyTerm(
            term_id="term-b",
            canonical_name="Beta",
            entity_type=CanonicalEntityType.MATERIAL,
        ),
    )

    with pytest.raises(AliasConflictError):
        registry.register_alias(
            OntologyAlias(alias="Alias-A", canonical_term_id="term-b"),
        )

    assert registry.resolve_alias("Alias-A").term_id == "term-a"
