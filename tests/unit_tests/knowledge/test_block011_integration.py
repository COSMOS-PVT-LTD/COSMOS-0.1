"""End-to-end integration test for KG-BLOCK-011 pipeline."""

from __future__ import annotations

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
)
from knowledge.ontology import (
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    canonicalize_extraction_result,
)
from knowledge.reasoning.w10 import EvidenceClassification
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.validation import ValidationContext, validate_context
from tests.unit_tests.knowledge.extraction.test_w4_extraction import (
    _parse_and_extract,
)


def test_end_to_end_knowledge_pipeline_preserves_provenance_and_lifecycle() -> None:
    """Full path: extraction → graph → index → search → validation → interface."""

    extraction = _parse_and_extract("Material: LOX\nOperating pressure 5 MPa.\n")
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
    canonical = canonicalize_extraction_result(extraction, registry)
    validation_report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )

    entity = CandidateEntityExtraction(
        extraction_id="ENT-PC",
        document_id=extraction.document_id,
        extracted_label="Chamber Pressure",
        entity_kind=ExtractedEntityKind.QUANTITY,
        canonical_entity_type=CanonicalEntityType.QUANTITY,
        provenance=SourceProvenanceRecord(
            anchor=ProvenanceReference(
                document_id=extraction.document_id,
                page=1,
            ),
        ),
    )
    graph_result = GraphConstructor(registry).construct(
        GraphConstructionBatch(entity_extractions=(entity,)),
    )
    store = graph_result.store
    graph_query = GraphQueryService(store)
    bundle = W7IndexBuilder().build(store)

    rag_result = ControlledRAGOrchestrator(
        index_bundle=bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(
        ControlledRAGRequest(
            request_id="e2e-001",
            task="Review LOX and chamber pressure evidence",
            query=SearchQuery(text="chamber pressure", mode=RetrievalMode.HYBRID),
            allowed_document_ids=(extraction.document_id,),
        ),
        validation_report=validation_report,
    )

    package = ContextPackager().package(rag_result)
    cursor_context = CursorContextBuilder().build(
        project_id="COSMOS",
        engineering_task_id="E2E-TASK",
        package=package,
        constraints=("evidence-only",),
    )
    payload = EngineeringKnowledgeInterface().build_payload(cursor_context)

    assert validation_report.report_digest
    assert payload.provenance_preserved is True
    assert payload.lifecycle_preserved is True
    assert (
        payload.outcome.classification
        in {
            EvidenceClassification.PARTIALLY_SUPPORTED,
            EvidenceClassification.SUPPORTED,
            EvidenceClassification.NO_VERIFIED_RESULT,
        }
    )
    assert cursor_context.content_kind == "knowledge_evidence"
    assert payload.payload_digest
