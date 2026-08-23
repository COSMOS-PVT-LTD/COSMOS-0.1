"""Public exports for knowledge.ontology."""

from __future__ import annotations

from knowledge.ontology.aliases import list_aliases, register_alias
from knowledge.ontology.canonicalization import (
    canonicalize_entity_candidate,
    canonicalize_extraction_result,
    resolve_canonical_term_id,
)
from knowledge.ontology.exceptions import (
    AliasConflictError,
    CanonicalizationError,
    DuplicateOntologyTermError,
    OntologyError,
    OntologyIdentityError,
    OntologyRegistryError,
    OntologyRelationshipError,
    OntologyTermNotFoundError,
    OntologyValidationError,
    TaxonomyCycleError,
)
from knowledge.ontology.identity import deterministic_ontology_id, registry_state_digest
from knowledge.ontology.models import (
    CanonicalizationMapping,
    CanonicalizationResult,
    CanonicalizationStatus,
    NormalizedTerm,
    OntologyAlias,
    OntologyRelationshipRule,
    OntologyRelationshipRuleType,
    OntologyRelationshipType,
    OntologyTerm,
    OntologyVersionMetadata,
    RelationshipValidationResult,
    TaxonomyEdge,
)
from knowledge.ontology.registry import OntologyRegistry
from knowledge.ontology.relationships import (
    register_relationship_rule,
    validate_relationship,
)
from knowledge.ontology.taxonomy import (
    ancestors_of,
    children_of,
    descendants_of,
    parents_of,
    register_taxonomy_edge,
)
from knowledge.ontology.validation import normalize_observed_term

__all__ = (
    "AliasConflictError",
    "CanonicalizationError",
    "CanonicalizationMapping",
    "CanonicalizationResult",
    "CanonicalizationStatus",
    "DuplicateOntologyTermError",
    "NormalizedTerm",
    "OntologyAlias",
    "OntologyError",
    "OntologyIdentityError",
    "OntologyRegistry",
    "OntologyRegistryError",
    "OntologyRelationshipError",
    "OntologyRelationshipRule",
    "OntologyRelationshipRuleType",
    "OntologyRelationshipType",
    "OntologyTerm",
    "OntologyTermNotFoundError",
    "OntologyValidationError",
    "OntologyVersionMetadata",
    "RelationshipValidationResult",
    "TaxonomyCycleError",
    "TaxonomyEdge",
    "ancestors_of",
    "canonicalize_entity_candidate",
    "canonicalize_extraction_result",
    "children_of",
    "descendants_of",
    "deterministic_ontology_id",
    "list_aliases",
    "normalize_observed_term",
    "parents_of",
    "register_alias",
    "register_relationship_rule",
    "register_taxonomy_edge",
    "registry_state_digest",
    "resolve_canonical_term_id",
    "validate_relationship",
)
