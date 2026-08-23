"""
COSMOS Knowledge Foundation

Module:
    knowledge.ontology.models

Purpose:
    Ontology registry contracts for canonical types, aliases, and vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.ontology.exceptions import OntologyValidationError

__all__ = (
    "CanonicalizationMapping",
    "CanonicalizationResult",
    "CanonicalizationStatus",
    "NormalizedTerm",
    "OntologyAlias",
    "OntologyRelationshipRule",
    "OntologyRelationshipRuleType",
    "OntologyRelationshipType",
    "OntologyTerm",
    "OntologyVersionMetadata",
    "RelationshipValidationResult",
    "TaxonomyEdge",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise OntologyValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise OntologyValidationError(f"{field_name} must not be blank.")

    return cleaned


class OntologyRelationshipType(Enum):
    """Controlled relationship vocabulary for ontology normalization."""

    REFERENCES = "references"
    CITES = "cites"
    CONTAINS = "contains"
    DEFINES = "defines"
    USES = "uses"
    DERIVED_FROM = "derived_from"
    VALID_IN = "valid_in"
    CONFLICTS_WITH = "conflicts_with"


class OntologyRelationshipRuleType(Enum):
    """Controlled ontology-term relationship rule vocabulary (KG-027)."""

    IS_A = "is_a"
    PART_OF = "part_of"
    HAS_COMPONENT = "has_component"
    USES = "uses"
    MADE_OF = "made_of"
    COOLED_BY = "cooled_by"
    PRODUCES = "produces"
    OPERATES_WITH = "operates_with"
    DERIVED_FROM = "derived_from"


class CanonicalizationStatus(Enum):
    """Resolution status for a canonicalization mapping."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True, kw_only=True)
class NormalizedTerm:
    """Whitespace-normalized observed term without semantic rewriting."""

    raw_label: str
    normalized_label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "raw_label",
            _validate_non_empty_string("raw_label", self.raw_label),
        )
        object.__setattr__(
            self,
            "normalized_label",
            _validate_non_empty_string(
                "normalized_label",
                self.normalized_label,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalizationMapping:
    """Explicit mapping from an extraction candidate to ontology resolution."""

    mapping_id: str
    extraction_id: str
    observed_label: str
    normalized_term: NormalizedTerm
    canonical_term_id: str | None
    status: CanonicalizationStatus
    provenance: SourceProvenanceRecord
    confidence_score: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mapping_id",
            _validate_non_empty_string("mapping_id", self.mapping_id),
        )
        object.__setattr__(
            self,
            "extraction_id",
            _validate_non_empty_string("extraction_id", self.extraction_id),
        )
        object.__setattr__(
            self,
            "observed_label",
            _validate_non_empty_string("observed_label", self.observed_label),
        )

        if not isinstance(self.normalized_term, NormalizedTerm):
            raise OntologyValidationError(
                "normalized_term must be a NormalizedTerm instance."
            )

        if self.canonical_term_id is not None:
            object.__setattr__(
                self,
                "canonical_term_id",
                _validate_non_empty_string(
                    "canonical_term_id",
                    self.canonical_term_id,
                ),
            )

        if not isinstance(self.status, CanonicalizationStatus):
            raise OntologyValidationError(
                "status must be a CanonicalizationStatus value."
            )

        if not isinstance(self.provenance, SourceProvenanceRecord):
            raise OntologyValidationError(
                "provenance must be a SourceProvenanceRecord instance."
            )

        score = float(self.confidence_score)

        if score < 0.0 or score > 1.0:
            raise OntologyValidationError(
                "confidence_score must be between 0.0 and 1.0."
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "canonical_term_id": self.canonical_term_id,
            "confidence_score": self.confidence_score,
            "extraction_id": self.extraction_id,
            "mapping_id": self.mapping_id,
            "normalized_label": self.normalized_term.normalized_label,
            "observed_label": self.observed_label,
            "provenance": self.provenance.to_mapping(),
            "status": self.status.value,
        }

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalizationResult:
    """Batch canonicalization output for W4 entity candidates."""

    document_id: str
    mappings: tuple[CanonicalizationMapping, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "document_id",
            _validate_non_empty_string("document_id", self.document_id),
        )

        if not isinstance(self.mappings, tuple):
            raise OntologyValidationError("mappings must be a tuple.")

    def to_mapping(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "mappings": [mapping.to_mapping() for mapping in self.mappings],
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class TaxonomyEdge:
    """Directed parent-child taxonomy edge between ontology terms."""

    parent_term_id: str
    child_term_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parent_term_id",
            _validate_non_empty_string("parent_term_id", self.parent_term_id),
        )
        object.__setattr__(
            self,
            "child_term_id",
            _validate_non_empty_string("child_term_id", self.child_term_id),
        )

        if self.parent_term_id == self.child_term_id:
            raise OntologyValidationError(
                "A taxonomy term cannot be its own parent."
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "child_term_id": self.child_term_id,
            "parent_term_id": self.parent_term_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class OntologyRelationshipRule:
    """Compatibility rule for ontology-term relationships (KG-027)."""

    rule_id: str
    relationship_type: OntologyRelationshipRuleType
    source_entity_type: CanonicalEntityType
    target_entity_type: CanonicalEntityType
    source_term_id: str | None = None
    target_term_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rule_id",
            _validate_non_empty_string("rule_id", self.rule_id),
        )

        if not isinstance(
            self.relationship_type,
            OntologyRelationshipRuleType,
        ):
            raise OntologyValidationError(
                "relationship_type must be an OntologyRelationshipRuleType value."
            )

        if not isinstance(self.source_entity_type, CanonicalEntityType):
            raise OntologyValidationError(
                "source_entity_type must be a CanonicalEntityType value."
            )

        if not isinstance(self.target_entity_type, CanonicalEntityType):
            raise OntologyValidationError(
                "target_entity_type must be a CanonicalEntityType value."
            )

        if self.source_term_id is not None:
            object.__setattr__(
                self,
                "source_term_id",
                _validate_non_empty_string(
                    "source_term_id",
                    self.source_term_id,
                ),
            )

        if self.target_term_id is not None:
            object.__setattr__(
                self,
                "target_term_id",
                _validate_non_empty_string(
                    "target_term_id",
                    self.target_term_id,
                ),
            )

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "relationship_type": self.relationship_type.value,
            "rule_id": self.rule_id,
            "source_entity_type": self.source_entity_type.value,
            "target_entity_type": self.target_entity_type.value,
        }

        if self.source_term_id is not None:
            payload["source_term_id"] = self.source_term_id
        if self.target_term_id is not None:
            payload["target_term_id"] = self.target_term_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class RelationshipValidationResult:
    """Explainable ontology relationship validation outcome."""

    permitted: bool
    relationship_type: OntologyRelationshipRuleType
    source_term_id: str
    target_term_id: str
    rule_id: str | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_term_id",
            _validate_non_empty_string("source_term_id", self.source_term_id),
        )
        object.__setattr__(
            self,
            "target_term_id",
            _validate_non_empty_string("target_term_id", self.target_term_id),
        )

        if not isinstance(
            self.relationship_type,
            OntologyRelationshipRuleType,
        ):
            raise OntologyValidationError(
                "relationship_type must be an OntologyRelationshipRuleType value."
            )

        if self.rule_id is not None:
            object.__setattr__(
                self,
                "rule_id",
                _validate_non_empty_string("rule_id", self.rule_id),
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "permitted": self.permitted,
            "reason": self.reason,
            "relationship_type": self.relationship_type.value,
            "rule_id": self.rule_id,
            "source_term_id": self.source_term_id,
            "target_term_id": self.target_term_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class OntologyVersionMetadata:
    """Version metadata for an ontology registry snapshot."""

    ontology_id: str
    ontology_version: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "ontology_id",
            _validate_non_empty_string("ontology_id", self.ontology_id),
        )
        object.__setattr__(
            self,
            "ontology_version",
            _validate_non_empty_string(
                "ontology_version",
                self.ontology_version,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "ontology_id": self.ontology_id,
            "ontology_version": self.ontology_version,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class OntologyAlias:
    """Alias mapping to a canonical ontology term."""

    alias: str
    canonical_term_id: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "alias",
            _validate_non_empty_string("alias", self.alias),
        )
        object.__setattr__(
            self,
            "canonical_term_id",
            _validate_non_empty_string(
                "canonical_term_id",
                self.canonical_term_id,
            ),
        )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "alias": self.alias,
            "canonical_term_id": self.canonical_term_id,
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class OntologyTerm:
    """Canonical ontology term with entity-type classification."""

    term_id: str
    canonical_name: str
    entity_type: CanonicalEntityType
    aliases: tuple[OntologyAlias, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "term_id",
            _validate_non_empty_string("term_id", self.term_id),
        )
        object.__setattr__(
            self,
            "canonical_name",
            _validate_non_empty_string(
                "canonical_name",
                self.canonical_name,
            ),
        )

        if not isinstance(self.entity_type, CanonicalEntityType):
            raise OntologyValidationError(
                "entity_type must be a CanonicalEntityType value."
            )

        if not isinstance(self.aliases, tuple):
            raise OntologyValidationError("aliases must be a tuple.")

        alias_values = {alias.alias.lower() for alias in self.aliases}

        if len(alias_values) != len(self.aliases):
            raise OntologyValidationError(
                "Ontology aliases must be unique per term."
            )

        for index, alias in enumerate(self.aliases):
            if not isinstance(alias, OntologyAlias):
                raise OntologyValidationError(
                    f"aliases[{index}] must be an OntologyAlias instance."
                )

            if alias.canonical_term_id != self.term_id:
                raise OntologyValidationError(
                    "Alias canonical_term_id must match term_id."
                )

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        return {
            "term_id": self.term_id,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type.value,
            "aliases": [alias.to_mapping() for alias in self.aliases],
        }
