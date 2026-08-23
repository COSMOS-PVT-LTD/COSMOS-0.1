"""Unit tests for KG-BLOCK-011 W11 interface (KG-048 → KG-051)."""

from __future__ import annotations

import pytest

from knowledge.extraction import (
    CandidateEntityExtraction,
    ExtractedEntityKind,
)
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.interface import (
    ContextPackager,
    ControlledRAGOrchestrator,
    ControlledRAGRequest,
    CursorContextBuilder,
    EngineeringKnowledgeInterface,
    InterfaceValidationError,
)
from knowledge.ontology import OntologyRegistry
from knowledge.reasoning.w10 import EvidenceClassification
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.validation.identity import validation_report_digest
from knowledge.validation.models import (
    ValidationCategory,
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
    ValidationStatus,
)


def _provenance() -> SourceProvenanceRecord:
    return SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-001", page=1),
    )


def _build_stack():
    entity = CandidateEntityExtraction(
        extraction_id="ENT-PC",
        document_id="DOC-001",
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=_provenance(),
    )

    graph_result = GraphConstructor(OntologyRegistry()).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    )
    store = graph_result.store
    graph_query = GraphQueryService(store)
    bundle = W7IndexBuilder().build(store)

    return store, graph_query, bundle


def _rag_request() -> ControlledRAGRequest:
    return ControlledRAGRequest(
        request_id="req-001",
        task="Review chamber pressure",
        query=SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID),
        allowed_document_ids=("DOC-001",),
    )


def test_kg048_controlled_rag_does_not_invoke_provider() -> None:
    """KG-048 must perform retrieval only without provider invocation."""

    store, graph_query, bundle = _build_stack()
    orchestrator = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    )
    result = orchestrator.retrieve(_rag_request())

    assert result.provider_invoked is False
    assert result.context.evidence.has_retrieval_results


def test_kg048_validation_aware_filtering_excludes_invalid_targets() -> None:
    """KG-048 must support validation-aware retrieval filtering."""

    store, graph_query, bundle = _build_stack()
    orchestrator = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    )
    finding = ValidationFinding(
        finding_id="vf-test",
        rule_id="VAL-TEST",
        severity=ValidationSeverity.HIGH,
        category=ValidationCategory.SCHEMA,
        status=ValidationStatus.INVALID,
        object_id="ENT-PC",
        message="invalid",
    )
    report = ValidationReport(
        findings=(finding,),
        report_digest=validation_report_digest(finding.finding_id),
    )
    result = orchestrator.retrieve(_rag_request(), validation_report=report)

    assert result.context.evidence.items == ()


def test_kg048_source_restriction_enforced() -> None:
    """KG-048 must enforce allowed document restrictions."""

    store, graph_query, bundle = _build_stack()
    orchestrator = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    )
    request = ControlledRAGRequest(
        request_id="req-002",
        task="Review",
        query=SearchQuery(text="chamber", mode=RetrievalMode.HYBRID),
        allowed_document_ids=("DOC-OTHER",),
    )
    result = orchestrator.retrieve(request)

    assert result.context.evidence.items == ()


def test_kg049_context_package_has_stable_digest() -> None:
    """KG-049 must produce deterministic package digests."""

    store, graph_query, bundle = _build_stack()
    result = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(_rag_request())

    first = ContextPackager().package(result)
    second = ContextPackager().package(result)

    assert first.package_digest == second.package_digest


def test_kg050_cursor_context_marks_content_as_knowledge_evidence() -> None:
    """KG-050 must mark content as knowledge evidence, not executable."""

    store, graph_query, bundle = _build_stack()
    result = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(_rag_request())
    package = ContextPackager().package(result)
    cursor_context = CursorContextBuilder().build(
        project_id="COSMOS",
        engineering_task_id="TASK-001",
        package=package,
        constraints=("do-not-execute-source",),
        assumptions=("candidate-only",),
    )

    assert cursor_context.content_kind == "knowledge_evidence"
    assert "do-not-execute-source" in cursor_context.constraints


def test_kg051_engineering_payload_preserves_provenance_and_lifecycle() -> None:
    """KG-051 must preserve provenance and lifecycle in engineering payload."""

    store, graph_query, bundle = _build_stack()
    result = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(_rag_request())
    package = ContextPackager().package(result)
    cursor_context = CursorContextBuilder().build(
        project_id="COSMOS",
        engineering_task_id="TASK-001",
        package=package,
    )
    payload = EngineeringKnowledgeInterface().build_payload(cursor_context)

    assert payload.provenance_preserved is True
    assert payload.lifecycle_preserved is True
    assert (
        payload.outcome.classification
        is EvidenceClassification.PARTIALLY_SUPPORTED
    )


def test_kg048_deterministic_context_assembly() -> None:
    """KG-048 controlled retrieval must be deterministic."""

    store, graph_query, bundle = _build_stack()
    orchestrator = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    )
    request = _rag_request()

    first = orchestrator.retrieve(request)
    second = orchestrator.retrieve(request)

    assert first.to_mapping() == second.to_mapping()


def test_kg048_request_validation_rejects_blank_task() -> None:
    """KG-048 must validate request contracts."""

    with pytest.raises(InterfaceValidationError, match="task"):
        ControlledRAGRequest(
            request_id="req-bad",
            task="   ",
            query=SearchQuery(text="chamber", mode=RetrievalMode.HYBRID),
        )


def test_kg051_payload_digest_is_stable() -> None:
    """KG-051 payload digest must be stable across repeated builds."""

    store, graph_query, bundle = _build_stack()
    result = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(_rag_request())
    package = ContextPackager().package(result)
    cursor_context = CursorContextBuilder().build(
        project_id="COSMOS",
        engineering_task_id="TASK-001",
        package=package,
    )
    interface = EngineeringKnowledgeInterface()

    first = interface.build_payload(cursor_context)
    second = interface.build_payload(cursor_context)

    assert first.payload_digest == second.payload_digest
