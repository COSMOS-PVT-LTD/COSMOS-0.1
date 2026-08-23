"""Contract boundary verification for KG-BLOCK-012."""

from __future__ import annotations

from knowledge.extraction.w4 import ExtractionContext, extract_document
from knowledge.graph import GraphConstructionBatch, GraphConstructor, GraphQueryService
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.w7 import W7IndexBuilder
from knowledge.ingestion import IngestionArtifactRef, IngestionRequest, IngestionStage, SourceFormat
from knowledge.ingestion_adapters import MarkdownIngestionAdapter
from knowledge.ontology import canonicalize_extraction_result
from knowledge.parsers.w3 import ParseContext, parse_document
from knowledge.reasoning.evidence import EvidenceRanker
from knowledge.reasoning.w10 import W10ProvenanceAwareReasoner
from knowledge.search import RetrievalMode, SearchQuery
from knowledge.search.w8 import HybridSearchEngine, ValidationAwareSearchEngine
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_text_digest
from knowledge.validation import ValidationContext, validate_context

from tests.integration_tests.kg_block012.helpers.pipeline import (
    build_lox_registry,
    load_golden_document,
    normalize_markdown_text,
    parse_and_extract,
    run_full_pipeline,
)


def _ingest_and_parse(content: str, *, source_id: str, artifact_id: str):
    from tests.integration_tests.kg_block012.helpers.pipeline import normalize_markdown_text

    normalized = normalize_markdown_text(content)
    text_digest = sha256_text_digest(normalized)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id=source_id,
            artifact_id=artifact_id,
            content=normalized.encode("utf-8"),
            content_hash=text_digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.MARKDOWN.value),
        ),
    )
    adapter = MarkdownIngestionAdapter(vault)
    ingestion = adapter.ingest(
        IngestionRequest(
            artifact=IngestionArtifactRef(
                source_id=source_id,
                artifact_id=artifact_id,
                source_format=SourceFormat.MARKDOWN,
                content_hash=text_digest,
            ),
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
    return parse_document(
        ParseContext(ingestion_result=ingestion, normalized_content=normalized),
    )


def test_w1_to_w2_source_identity_preserved() -> None:
    """W1 vault artifact identity must survive W2 ingestion."""

    extraction = parse_and_extract(load_golden_document())

    assert extraction.source_id == "SRC-GOLDEN"
    assert extraction.artifact_id == "ART-GOLDEN"
    assert extraction.document_id


def test_w2_to_w3_ingestion_stage_and_document_id_preserved() -> None:
    """W2 ingestion output must bind to W3 parse context without identity loss."""

    content = load_golden_document()
    parse_result = _ingest_and_parse(
        content,
        source_id="SRC-CONTRACT",
        artifact_id="ART-CONTRACT",
    )

    assert parse_result.ingestion_result.stage is IngestionStage.PARSED
    assert parse_result.parsed_document.document_id
    assert parse_result.parsed_document.source_id == "SRC-CONTRACT"


def test_w3_to_w4_parse_document_id_preserved() -> None:
    """W3 parsed document must drive W4 extraction with same document identity."""

    content = load_golden_document()
    parse_result = _ingest_and_parse(content, source_id="SRC-W34", artifact_id="ART-W34")
    extraction = extract_document(
        ExtractionContext(
            parsed_document=parse_result.parsed_document,
            normalized_content=normalize_markdown_text(content),
        ),
    )

    assert extraction.document_id == "ART-W34"
    assert extraction.source_id == "SRC-W34"


def test_w4_to_w5_canonicalization_preserves_document_id() -> None:
    """W4 extraction candidates must canonicalize without document identity mutation."""

    extraction = parse_and_extract(load_golden_document())
    canonical = canonicalize_extraction_result(extraction, build_lox_registry())

    assert canonical.document_id == extraction.document_id
    assert canonical.document_id == "ART-GOLDEN"


def test_w5_to_w6_graph_construction_preserves_provenance() -> None:
    """W5 canonical mappings must feed W6 graph without provenance loss."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )

    for node in graph_result.store.list_nodes():
        assert node.properties.get("document_id")
        assert node.properties.get("lifecycle_state")


def test_w6_to_w7_index_bundle_binds_graph_digest() -> None:
    """W6 graph store digest must bind W7 index bundle."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    bundle = W7IndexBuilder().build(graph_result.store)
    expected_digest = canonical_graph_record_digest(graph_result.store.snapshot())

    assert bundle.source_digest == expected_digest


def test_w7_to_w8_search_returns_document_identity() -> None:
    """W7 index bundle must support W8 search with provenance fields."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    bundle = W7IndexBuilder().build(store)
    query = GraphQueryService(store)
    page = HybridSearchEngine(bundle, query, store).search(
        SearchQuery(text="LOX", mode=RetrievalMode.HYBRID, limit=10),
    )

    for result in page.results:
        assert result.target_id
        if result.document_id is not None:
            assert isinstance(result.document_id, str)


def test_w8_to_w9_validation_aware_search_is_read_only() -> None:
    """W9 validation report must filter W8 results without mutating graph."""

    extraction = parse_and_extract(load_golden_document())
    registry = build_lox_registry()
    canonical = canonicalize_extraction_result(extraction, registry)
    report = validate_context(
        ValidationContext(
            document_id=extraction.document_id,
            source_id=extraction.source_id,
            extraction_result=extraction,
            canonicalization_result=canonical,
        ),
    )
    graph_result = GraphConstructor(registry).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    before_digest = canonical_graph_record_digest(store.snapshot())
    bundle = W7IndexBuilder().build(store)
    query = GraphQueryService(store)
    hybrid = HybridSearchEngine(bundle, query, store)
    filtered = ValidationAwareSearchEngine(hybrid, validation_report=report).search(
        SearchQuery(text="LOX", mode=RetrievalMode.HYBRID),
    )

    assert canonical_graph_record_digest(store.snapshot()) == before_digest
    assert filtered.total_count >= 0


def test_w9_to_w10_reasoning_consumes_evidence_bundle() -> None:
    """W10 reasoning must consume W8/W9 evidence without promotion."""

    extraction = parse_and_extract(load_golden_document())
    graph_result = GraphConstructor(build_lox_registry()).construct(
        GraphConstructionBatch(entity_extractions=extraction.entities or ()),
    )
    store = graph_result.store
    bundle = W7IndexBuilder().build(store)
    query = GraphQueryService(store)
    page = HybridSearchEngine(bundle, query, store).search(
        SearchQuery(text="pressure", mode=RetrievalMode.HYBRID),
    )
    evidence = EvidenceRanker(query).assemble(page.results)
    outcome = W10ProvenanceAwareReasoner().assess(evidence)

    assert outcome.classification.value
    for item in evidence.items:
        assert item.lifecycle_state in {
            "CANDIDATE",
            "EXTRACTED",
            "REVIEWED",
            "APPROVED",
            "REJECTED",
            "DEPRECATED",
        }


def test_w10_to_w11_interface_preserves_outcome_classification() -> None:
    """W11 interface must preserve W10 reasoning outcome without mutation."""

    first = run_full_pipeline(request_id="contract-w10-w11-a")
    second = run_full_pipeline(request_id="contract-w10-w11-b")

    assert first.payload.outcome.classification == second.payload.outcome.classification
    assert first.rag_result.provider_invoked is False
    assert first.cursor_context.content_kind == "knowledge_evidence"
