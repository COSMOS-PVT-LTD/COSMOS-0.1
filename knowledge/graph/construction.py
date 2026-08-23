"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.construction

Purpose:
    Deterministic graph construction pipeline from extraction candidates.
"""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.extraction.claim import (
    CandidateClaimExtraction,
    CandidateRelationshipExtraction,
)
from knowledge.extraction.entity import CandidateEntityExtraction
from knowledge.extraction.equation import CandidateEquationExtraction
from knowledge.graph.contracts import (
    GraphNode,
    GraphNodeIdentity,
    GraphRelationship,
    PropertyValue,
)
from knowledge.graph.entity import (
    CanonicalEntityReference,
    CanonicalEntityType,
    GraphEntityRecord,
)
from knowledge.graph.exceptions import (
    GraphConstructionError,
    GraphStorageError,
    GraphValidationError,
)
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.graph.memory_store import InMemoryGraphStore
from knowledge.graph.relationship import GraphEntityRelationshipRecord
from knowledge.graph.repository import GraphStore
from knowledge.graph.snapshot import GraphSnapshot, create_graph_snapshot
from knowledge.ontology.registry import OntologyRegistry, OntologyTermNotFoundError

__all__ = (
    "GraphConstructionBatch",
    "GraphConstructionResult",
    "GraphConstructor",
    "graph_node_id_for_extraction",
)

_MODEL_NAME_BY_TYPE: dict[str, str] = {
    CanonicalEntityType.REFERENCE.value: "reference",
    CanonicalEntityType.DOCUMENT.value: "document",
    CanonicalEntityType.EQUATION.value: "equation",
    CanonicalEntityType.VARIABLE.value: "variable",
    CanonicalEntityType.QUANTITY.value: "quantity",
    CanonicalEntityType.UNIT.value: "unit",
    CanonicalEntityType.DIMENSION.value: "dimension",
    CanonicalEntityType.CONSTANT.value: "constant",
    CanonicalEntityType.MATERIAL.value: "material",
    CanonicalEntityType.SUBSYSTEM.value: "subsystem",
    CanonicalEntityType.ENGINEERING_DOMAIN.value: "engineering_domain",
    CanonicalEntityType.CLAIM.value: "document",
    CanonicalEntityType.OTHER.value: "document",
}


def graph_node_id_for_extraction(extraction_id: str) -> str:
    """Return the deterministic graph node identifier for an extraction."""

    cleaned = extraction_id.strip()

    if not cleaned:
        raise GraphValidationError("extraction_id must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphConstructionBatch:
    """Input batch of extraction candidates for graph construction."""

    entity_extractions: tuple[CandidateEntityExtraction, ...] = ()
    equation_extractions: tuple[CandidateEquationExtraction, ...] = ()
    claim_extractions: tuple[CandidateClaimExtraction, ...] = ()
    relationship_extractions: tuple[CandidateRelationshipExtraction, ...] = ()

    def __post_init__(self) -> None:
        for field_name, values in (
            ("entity_extractions", self.entity_extractions),
            ("equation_extractions", self.equation_extractions),
            ("claim_extractions", self.claim_extractions),
            ("relationship_extractions", self.relationship_extractions),
        ):
            if not isinstance(values, tuple):
                raise GraphValidationError(f"{field_name} must be a tuple.")


@dataclass(frozen=True, slots=True, kw_only=True)
class GraphConstructionResult:
    """Result of a deterministic graph construction operation."""

    store: GraphStore
    entity_records: tuple[GraphEntityRecord, ...]
    relationship_records: tuple[GraphEntityRelationshipRecord, ...]
    snapshot: GraphSnapshot


class GraphConstructor:
    """
    Build graph nodes and relationships from extraction candidates.

    Candidate knowledge remains in candidate lifecycle states; this pipeline
    does not approve extracted information.
    """

    def __init__(self, ontology_registry: OntologyRegistry) -> None:
        self._ontology_registry = ontology_registry

    def construct(
        self,
        batch: GraphConstructionBatch,
        *,
        snapshot_sequence: int = 1,
    ) -> GraphConstructionResult:
        """Construct a graph store from a deterministic extraction batch."""

        if not isinstance(batch, GraphConstructionBatch):
            raise GraphValidationError(
                "batch must be a GraphConstructionBatch instance."
            )

        store = InMemoryGraphStore()
        entity_records: list[GraphEntityRecord] = []
        relationship_records: list[GraphEntityRelationshipRecord] = []

        for entity_extraction in sorted(
            batch.entity_extractions,
            key=lambda item: item.extraction_id,
        ):
            record = self._entity_record_from_extraction(entity_extraction)
            entity_records.append(record)
            store.add_node(record.node)

        for equation_extraction in sorted(
            batch.equation_extractions,
            key=lambda item: item.extraction_id,
        ):
            record = self._equation_record_from_extraction(equation_extraction)
            entity_records.append(record)
            store.add_node(record.node)

        for claim_extraction in sorted(
            batch.claim_extractions,
            key=lambda item: item.claim_id,
        ):
            record = self._claim_record_from_extraction(claim_extraction)
            entity_records.append(record)
            store.add_node(record.node)

        for relationship_extraction in sorted(
            batch.relationship_extractions,
            key=lambda item: item.relationship_id,
        ):
            relationship_record = self._relationship_record_from_extraction(
                relationship_extraction,
            )
            self._ensure_relationship_endpoints_exist(
                store,
                relationship_record.relationship.source_node_id,
                relationship_record.relationship.target_node_id,
            )
            relationship_records.append(relationship_record)
            store.add_relationship(relationship_record.relationship)

        snapshot = create_graph_snapshot(
            store.snapshot(),
            sequence_number=snapshot_sequence,
        )

        return GraphConstructionResult(
            store=store,
            entity_records=tuple(entity_records),
            relationship_records=tuple(relationship_records),
            snapshot=snapshot,
        )

    def _normalized_label(self, extracted_label: str) -> str:
        try:
            term = self._ontology_registry.resolve_alias(extracted_label)
        except OntologyTermNotFoundError:
            return extracted_label

        return term.canonical_name

    def _model_name_for_entity_type(self, entity_type: str) -> str:
        model_name = _MODEL_NAME_BY_TYPE.get(entity_type)

        if model_name is None:
            raise GraphConstructionError(
                f"Unsupported canonical entity type '{entity_type}'."
            )

        return model_name

    def _entity_record_from_extraction(
        self,
        extraction: CandidateEntityExtraction,
    ) -> GraphEntityRecord:
        if extraction.lifecycle_state is GraphLifecycleState.APPROVED:
            raise GraphConstructionError(
                "Entity extraction must not be approved before graph "
                "construction."
            )

        node_id = graph_node_id_for_extraction(extraction.extraction_id)
        canonical_name = self._normalized_label(extraction.extracted_label)

        node = GraphNode(
            identity=GraphNodeIdentity(
                node_id=node_id,
                node_type=extraction.canonical_entity_type.value,
            ),
            properties={
                "extracted_label": extraction.extracted_label,
                "canonical_name": canonical_name,
                "lifecycle_state": extraction.lifecycle_state.value,
                "document_id": extraction.document_id,
                "entity_kind": extraction.entity_kind.value,
            },
        )

        return GraphEntityRecord(
            node=node,
            canonical_reference=CanonicalEntityReference(
                entity_id=node_id,
                entity_type=extraction.canonical_entity_type,
                model_name=self._model_name_for_entity_type(
                    extraction.canonical_entity_type.value,
                ),
            ),
        )

    def _equation_record_from_extraction(
        self,
        extraction: CandidateEquationExtraction,
    ) -> GraphEntityRecord:
        if extraction.lifecycle_state is GraphLifecycleState.APPROVED:
            raise GraphConstructionError(
                "Equation extraction must not be approved before graph "
                "construction."
            )

        node_id = graph_node_id_for_extraction(extraction.extraction_id)

        properties: dict[str, PropertyValue] = {
            "lifecycle_state": extraction.lifecycle_state.value,
            "document_id": extraction.document_id,
            "confidence_band": extraction.confidence_band.value,
            "confidence_score": extraction.confidence_score,
        }

        if extraction.latex_representation is not None:
            properties["latex_representation"] = extraction.latex_representation

        node = GraphNode(
            identity=GraphNodeIdentity(
                node_id=node_id,
                node_type=CanonicalEntityType.EQUATION.value,
            ),
            properties=properties,
        )

        return GraphEntityRecord(
            node=node,
            canonical_reference=CanonicalEntityReference(
                entity_id=node_id,
                entity_type=CanonicalEntityType.EQUATION,
                model_name="equation",
            ),
        )

    def _claim_record_from_extraction(
        self,
        extraction: CandidateClaimExtraction,
    ) -> GraphEntityRecord:
        if extraction.lifecycle_state is GraphLifecycleState.APPROVED:
            raise GraphConstructionError(
                "Claim extraction must not be approved before graph "
                "construction."
            )

        node_id = graph_node_id_for_extraction(extraction.claim_id)

        node = GraphNode(
            identity=GraphNodeIdentity(
                node_id=node_id,
                node_type=CanonicalEntityType.CLAIM.value,
            ),
            properties={
                "lifecycle_state": extraction.lifecycle_state.value,
                "document_id": extraction.document_id,
                "conflict_visibility": extraction.conflict_visibility.value,
                "confidence_score": extraction.confidence_score,
            },
        )

        return GraphEntityRecord(
            node=node,
            canonical_reference=CanonicalEntityReference(
                entity_id=node_id,
                entity_type=CanonicalEntityType.CLAIM,
                model_name="document",
            ),
        )

    def _relationship_record_from_extraction(
        self,
        extraction: CandidateRelationshipExtraction,
    ) -> GraphEntityRelationshipRecord:
        if extraction.lifecycle_state is GraphLifecycleState.APPROVED:
            raise GraphConstructionError(
                "Relationship extraction must not be approved before graph "
                "construction."
            )

        relationship = GraphRelationship(
            relationship_id=extraction.relationship_id,
            relationship_type=extraction.relationship_type,
            source_node_id=graph_node_id_for_extraction(
                extraction.source_extraction_id,
            ),
            target_node_id=graph_node_id_for_extraction(
                extraction.target_extraction_id,
            ),
            properties={
                "lifecycle_state": extraction.lifecycle_state.value,
                "document_id": extraction.document_id,
                "confidence_score": extraction.confidence_score,
            },
        )

        return GraphEntityRelationshipRecord(
            relationship=relationship,
            provenance=extraction.provenance,
        )

    def _ensure_relationship_endpoints_exist(
        self,
        store: GraphStore,
        source_node_id: str,
        target_node_id: str,
    ) -> None:
        """Verify relationship endpoints exist before graph insertion."""

        for endpoint_id, endpoint_role in (
            (source_node_id, "source"),
            (target_node_id, "target"),
        ):
            try:
                store.get_node(endpoint_id)
            except GraphStorageError as exc:
                raise GraphConstructionError(
                    "Relationship "
                    f"{endpoint_role} endpoint '{endpoint_id}' "
                    "does not exist in the constructed graph."
                ) from exc
