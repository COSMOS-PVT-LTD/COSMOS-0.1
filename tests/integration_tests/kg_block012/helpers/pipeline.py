"""Pipeline helpers for KG-BLOCK-012 integration qualification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.extraction.w4 import ExtractionContext, extract_document
from knowledge.extraction.w4.models import ExtractionResult
from knowledge.graph import (
    GraphConstructionBatch,
    GraphConstructor,
    GraphQueryService,
    ProvenanceReference,
)
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.graph.repository import GraphStore
from knowledge.indexing.w7 import W7IndexBundle, W7IndexBuilder
from knowledge.ingestion import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionStage,
    SourceFormat,
)
from knowledge.ingestion_adapters import MarkdownIngestionAdapter
from knowledge.interface import (
    ContextPackager,
    ControlledRAGOrchestrator,
    ControlledRAGRequest,
    ControlledRAGResult,
    CursorContextBuilder,
    CursorDevelopmentContext,
    EngineeringKnowledgeInterface,
    EngineeringKnowledgePayload,
)
from knowledge.interface.models import ContextPackage
from knowledge.ontology import (
    CanonicalizationResult,
    OntologyAlias,
    OntologyRegistry,
    OntologyTerm,
    canonicalize_extraction_result,
)
from knowledge.parsers.w3 import ParseContext, parse_document
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_text_digest
from knowledge.validation import ValidationContext, validate_context
from knowledge.validation.models import ValidationReport

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "documents"
_GOLDEN_DOCUMENT = _FIXTURES_DIR / "golden_propulsion_spec.md"


def normalize_markdown_text(content: str) -> str:
    """Apply the same normalization as the markdown ingestion adapter."""

    return "\n".join(
        line.rstrip()
        for line in content.replace("\r\n", "\n").split("\n")
    )


def load_golden_document() -> str:
    """Return the deterministic golden engineering-document fixture."""

    return normalize_markdown_text(
        _GOLDEN_DOCUMENT.read_text(encoding="utf-8"),
    )


def build_lox_registry() -> OntologyRegistry:
    """Return an ontology registry with LOX material mapping."""

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
    return registry


def parse_and_extract(
    content: str,
    *,
    source_id: str = "SRC-GOLDEN",
    artifact_id: str = "ART-GOLDEN",
) -> ExtractionResult:
    """Execute W1→W2→W3→W4 pipeline for inline or fixture content."""

    normalized = normalize_markdown_text(content)
    digest = sha256_text_digest(normalized)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id=source_id,
            artifact_id=artifact_id,
            content=normalized.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(
                source_format=SourceFormat.MARKDOWN.value,
                license_metadata={"tag": "COSMOS-INTERNAL-TEST"},
            ),
        ),
    )
    artifact = IngestionArtifactRef(
        source_id=source_id,
        artifact_id=artifact_id,
        source_format=SourceFormat.MARKDOWN,
        content_hash=digest,
    )
    adapter = MarkdownIngestionAdapter(vault)
    ingestion = adapter.ingest(
        IngestionRequest(
            artifact=artifact,
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
    parse_result = parse_document(
        ParseContext(
            ingestion_result=ingestion,
            normalized_content=normalized,
        ),
    )
    if parse_result.ingestion_result.stage is not IngestionStage.PARSED:
        msg = "Expected parsed ingestion stage after W3 parse."
        raise AssertionError(msg)

    return extract_document(
        ExtractionContext(
            parsed_document=parse_result.parsed_document,
            normalized_content=normalized,
        ),
    )


@dataclass(frozen=True, slots=True)
class PipelineArtifacts:
    """Artifacts produced by the full W1→W11 qualification pipeline."""

    extraction: ExtractionResult
    canonical: CanonicalizationResult
    validation_report: ValidationReport
    store: GraphStore
    graph_query: GraphQueryService
    index_bundle: W7IndexBundle
    rag_result: ControlledRAGResult
    package: ContextPackage
    cursor_context: CursorDevelopmentContext
    payload: EngineeringKnowledgePayload


def run_full_pipeline(
    content: str | None = None,
    *,
    task: str = "Qualify propulsion specification evidence",
    query_text: str = "chamber pressure LOX",
    request_id: str = "block012-e2e",
    extra_entities: tuple[CandidateEntityExtraction, ...] = (),
) -> PipelineArtifacts:
    """Execute the complete authorized W1→W11 integration path."""

    document = content if content is not None else load_golden_document()
    extraction = parse_and_extract(document)
    registry = build_lox_registry()
    canonical = canonicalize_extraction_result(extraction, registry)
    validation_report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )

    entities = tuple(extraction.entities) + extra_entities
    if not entities:
        entities = (
            CandidateEntityExtraction(
                extraction_id="ENT-CHAMBER-PRESSURE",
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
            ),
        )

    graph_result = GraphConstructor(registry).construct(
        GraphConstructionBatch(entity_extractions=entities),
    )
    store = graph_result.store
    graph_query = GraphQueryService(store)
    index_bundle = W7IndexBuilder().build(store)

    rag_result = ControlledRAGOrchestrator(
        index_bundle=index_bundle,
        graph_query=graph_query,
        store=store,
    ).retrieve(
        ControlledRAGRequest(
            request_id=request_id,
            task=task,
            query=SearchQuery(text=query_text, mode=RetrievalMode.HYBRID),
            allowed_document_ids=(extraction.document_id,),
        ),
        validation_report=validation_report,
    )

    package = ContextPackager().package(rag_result)
    cursor_context = CursorContextBuilder().build(
        project_id="COSMOS",
        engineering_task_id="BLOCK-012-QUAL",
        package=package,
        constraints=("evidence-only",),
    )
    payload = EngineeringKnowledgeInterface().build_payload(cursor_context)

    return PipelineArtifacts(
        extraction=extraction,
        canonical=canonical,
        validation_report=validation_report,
        store=store,
        graph_query=graph_query,
        index_bundle=index_bundle,
        rag_result=rag_result,
        package=package,
        cursor_context=cursor_context,
        payload=payload,
    )
