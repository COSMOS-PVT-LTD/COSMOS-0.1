"""Working knowledge-foundation facade for remaining checklist phases."""

from __future__ import annotations

from pathlib import Path

from knowledge.foundation.audit import AuditLog
from knowledge.foundation.document_pipeline import DocumentKnowledgeDraft, ingest_markdown_to_candidates
from knowledge.foundation.entity_embeddings import EntityEmbeddingIndex
from knowledge.foundation.equation_approval import (
    EquationApprovalPipeline,
    EquationReviewDecision,
    NormalizedEquationCandidate,
)
from knowledge.foundation.real_document_pipeline import (
    PipelineEvent,
    PipelineEventKind,
    RealDocumentPipelineResult,
    run_real_document_pipeline,
)
from knowledge.foundation.governance import (
    KnowledgeAction,
    KnowledgeActor,
    KnowledgeGovernance,
    KnowledgeRole,
)
from knowledge.foundation.keyword_index import KeywordIndex
from knowledge.foundation.persistence import dump_snapshot, load_snapshot
from knowledge.foundation.physics_boundary import PhysicsKnowledgeGateway
from knowledge.foundation.rag_policy import KnowledgePolicy
from knowledge.foundation.reasoning_answer import EngineeringAnswer, assemble_engineering_answer
from knowledge.foundation.seed_corpus import populate_seed_corpus
from knowledge.foundation.unified_search import UnifiedSearchPipeline, UnifiedSearchResult
from knowledge.graph.concept_graph import ConceptEdge, ConceptGraph
from knowledge.graph.integrity import validate_concept_graph
from knowledge.indexing.citation_index import CitationIndex, CitationIndexEntry
from knowledge.indexing.equation_index import EquationIndex
from knowledge.indexing.variable_index import VariableIndex, VariableIndexEntry
from knowledge.interface.engineering_query import EngineeringQueryService, MaterialCard
from knowledge.models.document import Document, DocumentApprovalStatus, DocumentType, SecurityLevel
from knowledge.models.equation import Equation, EquationCategory, EquationStatus
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.reference import Reference, ReferenceStatus, ReferenceType
from knowledge.ontology.engineering_vocabulary import EngineeringRelationship
from knowledge.pdf.registry import SourceRegistry
from knowledge.persistence.sqlite_store import DatabaseUnavailableError, KnowledgeDatabase
from knowledge.references.document_class import DocumentClass
from knowledge.references.ingestion import ReferenceIngestRequest, validate_reference_ingest
from knowledge.references.rights import RightsStatus
from knowledge.ontology.registry import OntologyRegistry
from knowledge.repositories.assumption_repository import AssumptionRepository
from knowledge.repositories.boundary_condition_repository import BoundaryConditionRepository
from knowledge.repositories.component_repository import ComponentRepository
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repositories.design_rule_repository import DesignRuleRepository
from knowledge.repositories.document_repository import DocumentRepository
from knowledge.repositories.empirical_relation_repository import EmpiricalRelationRepository
from knowledge.repositories.equation_repository import EquationRepository
from knowledge.repositories.experiment_repository import ExperimentRepository
from knowledge.repositories.failure_mode_repository import FailureModeRepository
from knowledge.repositories.physical_law_repository import PhysicalLawRepository
from knowledge.repositories.property_repository import PropertyRepository
from knowledge.repositories.reference_repository import ReferenceRepository
from knowledge.repositories.simulation_repository import SimulationRepository
from knowledge.repository.knowledge_repository import EntityNotFoundError

__all__ = ("KnowledgeFoundationService", "SYSTEM_APPROVER")

SYSTEM_APPROVER = KnowledgeActor(
    actor_id="kf-system-approver",
    roles=frozenset(KnowledgeRole),
)


class KnowledgeFoundationService:
    """In-memory working knowledge foundation with seed, search, and governance."""

    def __init__(self, actor: KnowledgeActor | None = None) -> None:
        self.actor = actor or SYSTEM_APPROVER
        self.governance = KnowledgeGovernance()
        self.audit = AuditLog()
        self.ontology = OntologyRegistry()
        self.references = ReferenceRepository()
        self.documents = DocumentRepository()
        self.equations = EquationRepository()
        self.correlations = CorrelationRepository()
        self.design_rules = DesignRuleRepository()
        self.physical_laws = PhysicalLawRepository()
        self.assumptions = AssumptionRepository()
        self.properties = PropertyRepository()
        self.boundary_conditions = BoundaryConditionRepository()
        self.failure_modes = FailureModeRepository()
        self.experiments = ExperimentRepository()
        self.simulations = SimulationRepository()
        self.empirical = EmpiricalRelationRepository()
        self.components = ComponentRepository()
        self.materials: list[MaterialCard] = []
        self.graph = ConceptGraph()
        self.keywords = KeywordIndex()
        self.equation_index = EquationIndex()
        self.variable_index = VariableIndex()
        self.citation_index = CitationIndex()
        self.embeddings = EntityEmbeddingIndex()
        self.approval = EquationApprovalPipeline()
        self.source_registry = SourceRegistry()
        self._pipeline_ids: set[str] = set()
        self.ocr_records: list[dict[str, object]] = []
        self.math_ocr_records: list[dict[str, object]] = []
        self.database: KnowledgeDatabase | None = None

    @classmethod
    def with_seed_corpus(cls, actor: KnowledgeActor | None = None) -> KnowledgeFoundationService:
        service = cls(actor)
        service.governance.authorize(service.actor, KnowledgeAction.INGEST)
        service.governance.authorize(service.actor, KnowledgeAction.MODIFY_ONTOLOGY)
        populate_seed_corpus(service)
        service.audit.record(
            service.actor,
            KnowledgeAction.INGEST,
            entity_id="SEED-CORPUS",
            payload={"kind": "seed", "count": len(service.physical_laws.query())},
        )
        return service

    def query_service(self) -> EngineeringQueryService:
        return EngineeringQueryService(
            equations=self.equations,
            correlations=self.correlations,
            design_rules=self.design_rules,
            physical_laws=self.physical_laws,
            properties=self.properties,
            materials=tuple(self.materials),
            boundary_conditions=self.boundary_conditions,
            failure_modes=self.failure_modes,
            experiments=self.experiments,
            simulations=self.simulations,
            references=self.references,
            documents=self.documents,
        )

    def physics(self) -> PhysicsKnowledgeGateway:
        return PhysicsKnowledgeGateway(self.query_service())

    def search(self, query: str, *, policy: KnowledgePolicy | None = None) -> UnifiedSearchResult:
        pipeline = UnifiedSearchPipeline(
            keywords=self.keywords,
            equations=self.equation_index,
            variables=self.variable_index,
            citations=self.citation_index,
            embeddings=self.embeddings,
            graph=self.graph,
            policy=policy or KnowledgePolicy(),
        )
        return pipeline.search(query)

    def ingest_markdown(self, content: str, *, source_id: str, artifact_id: str, reference_id: str) -> DocumentKnowledgeDraft:
        self.governance.authorize(self.actor, KnowledgeAction.INGEST)
        self.governance.authorize(self.actor, KnowledgeAction.EXTRACT)
        draft = ingest_markdown_to_candidates(
            content,
            source_id=source_id,
            artifact_id=artifact_id,
            reference_id=reference_id,
        )
        self.audit.record(
            self.actor,
            KnowledgeAction.EXTRACT,
            entity_id=draft.document_id,
            payload={"content_hash": draft.content_hash, "equations": len(draft.equation_candidates)},
        )
        return draft

    def ingest_real_pdf(
        self,
        content: bytes,
        *,
        source_id: str,
        document_id: str,
        title: str,
        filename: str,
        reference_id: str,
        expected_hash: str | None = None,
        publisher: str | None = None,
        author: str | None = None,
        edition: str | None = None,
        revision: str | None = None,
        rights_status: RightsStatus | None = None,
        document_class: DocumentClass | None = None,
        license: str | None = None,
        organization: str | None = None,
        publication_year: int | None = None,
        usage_constraints: str | None = None,
    ) -> RealDocumentPipelineResult:
        self.governance.authorize(self.actor, KnowledgeAction.INGEST)
        self.governance.authorize(self.actor, KnowledgeAction.EXTRACT)
        result = run_real_document_pipeline(
            content,
            source_id=source_id,
            document_id=document_id,
            title=title,
            filename=filename,
            reference_id=reference_id,
            registry=self.source_registry,
            expected_hash=expected_hash,
            publisher=publisher,
            author=author,
            edition=edition,
            revision=revision,
            rights_status=rights_status,
            document_class=document_class,
            license=license,
            organization=organization,
            publication_year=publication_year,
            usage_constraints=usage_constraints,
        )
        self._pipeline_ids.update({source_id, document_id, reference_id})
        self.ocr_records.extend(
            [
                {
                    "document_id": item.document_id,
                    "page_number": item.page_number,
                    "image_hash": item.image_hash,
                    "rasterizer": item.rasterizer,
                    "rasterizer_version": item.rasterizer_version,
                    "ocr_backend": item.ocr_backend,
                    "ocr_version": item.ocr_version,
                    "confidence": item.ocr_confidence,
                    "warnings": list(item.warnings),
                    "text_preview": item.ocr_text[:120],
                }
                for item in result.ocr_evidence
            ],
        )
        self.math_ocr_records.extend(
            [
                {
                    "document_id": item.document_id,
                    "page_number": item.page_number,
                    "region_id": item.region_id,
                    "image_hash": item.image_hash,
                    "backend": item.backend,
                    "backend_version": item.backend_version,
                    "source_representation": item.source_representation[:120],
                    "latex": item.latex,
                    "failure": item.failure.value if item.failure else None,
                }
                for item in result.math_ocr_results
            ],
        )
        self.audit.record(
            self.actor,
            KnowledgeAction.EXTRACT,
            entity_id=document_id,
            payload={
                "status": result.status.value,
                "equations": len(result.equation_candidates),
                "content_hash": result.registered.content_hash if result.registered else "",
            },
        )
        return result

    def ingest_reference_pdf(
        self,
        content: bytes,
        request: ReferenceIngestRequest,
        *,
        reference_id: str,
    ) -> RealDocumentPipelineResult:
        validate_reference_ingest(request)
        return self.ingest_real_pdf(
            content,
            source_id=request.source_id,
            document_id=request.document_id,
            title=request.title,
            filename=request.filename,
            reference_id=reference_id,
            publisher=request.publisher,
            author=request.author,
            edition=request.edition,
            rights_status=request.rights.status,
            document_class=request.document_class,
            license=request.rights.license,
            organization=request.organization,
            publication_year=request.publication_year,
            usage_constraints=request.rights.usage_constraints,
        )

    def attach_database(self, path: str | Path) -> KnowledgeDatabase:
        database = KnowledgeDatabase(path)
        database.migrate()
        self.database = database
        return database

    def persist_to_database(self, result: RealDocumentPipelineResult) -> None:
        if self.database is None:
            raise DatabaseUnavailableError("no database attached")
        self.database.persist_pipeline(result)

    def approve_real_equation(
        self,
        result: RealDocumentPipelineResult,
        candidate_id: str,
        decision: EquationReviewDecision,
        *,
        reference_id: str,
        title: str,
    ) -> NormalizedEquationCandidate:
        self.governance.authorize(self.actor, KnowledgeAction.REVIEW)
        if decision is EquationReviewDecision.APPROVE:
            self.governance.authorize(self.actor, KnowledgeAction.APPROVE)
        from knowledge.equations.review import review_validated_equation

        validated = next(
            item for item in result.validated_equations if item.candidate.candidate_id == candidate_id
        )
        reviewed = review_validated_equation(
            validated,
            decision,
            reviewer=self.actor.actor_id,
        )
        events = list(result.events)
        if reviewed.lifecycle is KnowledgeLifecycle.APPROVED:
            self._persist_approved_equation(result, validated.candidate.raw_text, candidate_id, reference_id, title)
            events.append(PipelineEvent(kind=PipelineEventKind.APPROVED, entity_id=candidate_id, detail="governed"))
            events.append(PipelineEvent(kind=PipelineEventKind.PERSISTED, entity_id=candidate_id, detail=reference_id))
            events.append(PipelineEvent(kind=PipelineEventKind.INDEXED, entity_id=candidate_id, detail="keyword+equation"))
            if self.database is not None:
                self.database.persist_approval(
                    candidate_id=candidate_id,
                    decision=decision.value,
                    reviewer=self.actor.actor_id,
                    payload={
                        "expression": validated.candidate.raw_text,
                        "reference_id": reference_id,
                        "source_hash": result.registered.content_hash if result.registered else "",
                    },
                )
        else:
            events.append(PipelineEvent(kind=PipelineEventKind.REJECTED, entity_id=candidate_id, detail=decision.value))
        self.audit.record(
            self.actor,
            KnowledgeAction.APPROVE if decision is EquationReviewDecision.APPROVE else KnowledgeAction.REVIEW,
            entity_id=candidate_id,
            payload={"decision": decision.value, "lifecycle": reviewed.lifecycle.value},
        )
        return reviewed

    def review_equation(
        self,
        candidate: NormalizedEquationCandidate,
        decision: EquationReviewDecision,
    ) -> NormalizedEquationCandidate:
        self.governance.authorize(self.actor, KnowledgeAction.REVIEW)
        if decision is EquationReviewDecision.APPROVE:
            self.governance.authorize(self.actor, KnowledgeAction.APPROVE)
        reviewed = self.approval.review(candidate, decision, reviewer=self.actor.actor_id)
        self.audit.record(
            self.actor,
            KnowledgeAction.APPROVE if decision is EquationReviewDecision.APPROVE else KnowledgeAction.REVIEW,
            entity_id=candidate.extraction_id,
            payload={"decision": decision.value, "lifecycle": reviewed.lifecycle.value},
        )
        return reviewed

    def answer(self, query: str) -> EngineeringAnswer:
        result = self.search(query)
        approved = all(hit.lifecycle is KnowledgeLifecycle.APPROVED for hit in result.hits) and bool(result.hits)
        assumptions = tuple(
            item.statement
            for item in self.assumptions.query(lambda row: row.lifecycle is KnowledgeLifecycle.APPROVED)
            if query.lower() in item.statement.lower()
            or any(entity_id.lower() in query.lower() for entity_id in item.affected_entity_ids)
            or "bartz" in query.lower()
            and "CORR-BARTZ" in item.affected_entity_ids
        )
        return assemble_engineering_answer(
            conclusion=result.hits[0].snippet if result.hits else "No approved knowledge matched the query.",
            equation_ids=tuple(hit.entity_id for hit in result.hits if hit.entity_type in {"Equation", "Correlation", "PhysicalLaw"}),
            document_ids=result.provenance_ids,
            supporting_entities=tuple(hit.entity_id for hit in result.hits),
            source_references=result.provenance_ids,
            assumptions=assumptions,
            validity_range=None,
            domain=result.kind.value,
            evidence=result.evidence,
            contradictions=(),
            approved=approved,
        )

    def _persist_approved_equation(
        self,
        result: RealDocumentPipelineResult,
        expression: str,
        candidate_id: str,
        reference_id: str,
        title: str,
    ) -> None:
        recovered = result.recovered_text
        if not recovered.strip():
            raise ValueError("Cannot persist approved knowledge without recovered source text.")
        author = result.registered.author if result.registered and result.registered.author else "COSMOS"
        try:
            reference = self.references.get(reference_id)
        except EntityNotFoundError:
            reference = Reference(
                reference_id=reference_id,
                title=title,
                authors=(author,),
                reference_type=ReferenceType.INTERNAL_DOCUMENT,
                publication_year=2026,
                status=ReferenceStatus.APPROVED,
                notes="COSMOS-authored qualification original. No third-party prose.",
            )
            self.references.create(reference)
        document_id = result.registered.document_id if result.registered else candidate_id
        try:
            document = self.documents.get(document_id)
        except EntityNotFoundError:
            document = Document(
                document_id=document_id,
                document_version_id="v1",
                title=title,
                content=recovered,
                document_type=DocumentType.INTERNAL_DOCUMENT,
                reference=reference,
                approval_status=DocumentApprovalStatus.APPROVED,
                security_level=SecurityLevel.PUBLIC,
            )
            self.documents.create(document)
        page = result.equation_candidates[0].page_number if result.equation_candidates else 1
        section = next((item.section_id for item in result.equation_candidates if item.candidate_id == candidate_id), None)
        equation = Equation(
            equation_id=candidate_id,
            equation_name=title,
            equation_category=EquationCategory.FLUID_DYNAMICS,
            equation_version="1.0.0",
            source_document=document,
            source_reference=reference,
            expression=expression,
            latex_expression=expression,
            symbolic_expression=expression,
            normalized_expression=expression,
            section=section,
            page_number=page,
            extracted_by="real-pdf-pipeline",
            extraction_confidence=0.7,
            status=EquationStatus.APPROVED,
        )
        if not any(item.equation_id == candidate_id for item in self.equations.query()):
            self.equations.create(equation)
        variables = next(
            (tuple(item.symbol for item in cand.variables) for cand in result.equation_candidates if cand.candidate_id == candidate_id),
            (),
        )
        self.equation_index.add(equation, variables=variables)
        self.keywords.add(
            entity_id=candidate_id,
            entity_type="Equation",
            title=expression,
            terms=(expression, title, *variables, reference_id, document_id),
            lifecycle=KnowledgeLifecycle.APPROVED,
            provenance_id=reference_id,
        )
        for symbol in variables:
            self.variable_index.add(
                VariableIndexEntry(
                    variable_id=f"{candidate_id}-{symbol}",
                    symbol=symbol,
                    name=symbol,
                    equation_ids=(candidate_id,),
                ),
            )
            self._pipeline_ids.add(f"{candidate_id}-{symbol}")
        self.citation_index.add(
            CitationIndexEntry(
                reference_id=reference_id,
                entity_id=candidate_id,
                entity_type="Equation",
                document_id=document_id,
                page=page,
            ),
        )
        self.graph.add(
            ConceptEdge(
                source_id=candidate_id,
                target_id=document_id,
                relationship=EngineeringRelationship.DERIVED_FROM,
            ),
        )
        self._pipeline_ids.update({candidate_id, document_id, reference_id})

    def known_ids(self) -> frozenset[str]:
        ids = {
            *[item.law_id for item in self.physical_laws.query()],
            *[item.correlation_id for item in self.correlations.query()],
            *[item.rule_id for item in self.design_rules.query()],
            *[item.assumption_id for item in self.assumptions.query()],
            *[item.component_id for item in self.components.query()],
            *[item.failure_mode_id for item in self.failure_modes.query()],
            *[item.boundary_condition_id for item in self.boundary_conditions.query()],
            *[item.experiment_id for item in self.experiments.query()],
            *[item.simulation_id for item in self.simulations.query()],
            *[item.document_id for item in self.documents.query()],
            *[item.equation_id for item in self.equations.query()],
            *[card.material_id for card in self.materials],
            *self._pipeline_ids,
        }
        return frozenset(ids)

    def graph_integrity_passed(self) -> bool:
        return validate_concept_graph(self.graph, self.known_ids()).passed

    def snapshot(self) -> dict[str, object]:
        return {
            "schema_version": "1.0.0",
            "laws": [item.law_id for item in self.physical_laws.query()],
            "correlations": [item.correlation_id for item in self.correlations.query()],
            "design_rules": [item.rule_id for item in self.design_rules.query()],
            "materials": [card.material_id for card in self.materials],
            "properties": [item.value_id for item in self.properties.values.query()],
            "assumptions": [item.assumption_id for item in self.assumptions.query()],
            "audit_events": len(self.audit.events()),
            "law_records": [
                {
                    "law_id": item.law_id,
                    "name": item.name,
                    "formulation": item.mathematical_formulation,
                    "lifecycle": item.lifecycle.value,
                    "source_reference_id": item.provenance.source_reference_id,
                    "document_id": item.provenance.document_id,
                }
                for item in self.physical_laws.query()
            ],
            "correlation_records": [
                {
                    "correlation_id": item.correlation_id,
                    "name": item.name,
                    "equation": item.equation,
                    "lifecycle": item.lifecycle.value,
                    "source_reference_id": item.provenance.source_reference_id if item.provenance else "",
                    "document_id": item.provenance.document_id if item.provenance else "",
                }
                for item in self.correlations.query()
            ],
            "property_records": [
                {
                    "value_id": item.value_id,
                    "property_id": item.property_id,
                    "material_id": item.material_id,
                    "numeric_value": item.numeric_value,
                    "unit": item.unit,
                    "lifecycle": item.lifecycle.value,
                    "source_reference_id": item.provenance.source_reference_id,
                    "validity_range": item.validity_range,
                }
                for item in self.properties.values.query()
            ],
            "ocr_records": list(self.ocr_records),
            "math_ocr_records": list(self.math_ocr_records),
        }

    def persist(self, path: str | Path) -> str:
        return dump_snapshot(path, self.snapshot())

    def load_snapshot(self, path: str | Path) -> dict[str, object]:
        return load_snapshot(path)
