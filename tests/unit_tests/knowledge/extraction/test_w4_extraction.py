"""Unit tests for KG-BLOCK-007 W4 extraction."""

from __future__ import annotations

import pytest

from knowledge.extraction.w4 import (
    ExtractionContext,
    ExtractionOrchestrator,
    ExtractionResult,
    build_default_extraction_registry,
    extract_document,
)
from knowledge.graph import GraphLifecycleState
from knowledge.parsers.w3.exceptions import ParserEquationError
from knowledge.ingestion import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionStage,
    SourceFormat,
)
from knowledge.ingestion_adapters import MarkdownIngestionAdapter
from knowledge.parsers.w3 import ParseContext, parse_document
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_text_digest


def _parse_and_extract(content: str) -> ExtractionResult:
    digest = sha256_text_digest(content)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id="SRC-001",
            artifact_id="ART-001",
            content=content.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.MARKDOWN.value),
        ),
    )
    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
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
            normalized_content=content,
        ),
    )
    assert parse_result.ingestion_result.stage is IngestionStage.PARSED

    return extract_document(
        ExtractionContext(
            parsed_document=parse_result.parsed_document,
            normalized_content=content,
        ),
    )


def test_extract_entities_from_sections_and_labels() -> None:
    """KG-019 must extract entity candidates from headings and labels."""

    content = "\n".join(
        [
            "# Combustion Chamber",
            "Material: Inconel 718",
            "Component: Main Injector",
        ],
    )
    result = _parse_and_extract(content)

    labels = {entity.extracted_label for entity in result.entities}

    assert "Combustion Chamber" in labels
    assert "Inconel 718" in labels
    assert "Main Injector" in labels

    for entity in result.entities:
        assert entity.lifecycle_state is GraphLifecycleState.CANDIDATE


def test_extract_quantities_with_units() -> None:
    """KG-020 must extract numeric quantities without silent unit guessing."""

    content = "\n".join(
        [
            "# Data",
            "Chamber pressure is 5 MPa.",
            "| Name | Value |",
            "| --- | --- |",
            "| Thrust | 20 kN |",
        ],
    )
    result = _parse_and_extract(content)

    assert len(result.quantities) >= 2
    values = {quantity.raw_text for quantity in result.quantities}

    assert any("5 MPa" in value for value in values)
    assert any("20 kN" in value for value in values)

    for quantity in result.quantities:
        assert quantity.ambiguous is False or quantity.unit_token is not None


def test_extract_equations_from_w3_parsed_equations() -> None:
    """KG-021 must produce equation candidates from W3 parsed equations."""

    content = "Formula $F = ma$ in text.\n"
    result = _parse_and_extract(content)

    assert len(result.equations) == 1
    assert result.equations[0].raw_representation == "F = ma"
    assert result.equations[0].lifecycle_state is GraphLifecycleState.EXTRACTED


def test_extract_equations_reject_executable_text() -> None:
    """KG-021 must reject executable equation payloads."""

    content = "$$eval('1')$$\n"

    with pytest.raises(ParserEquationError):
        _parse_and_extract(content)


def test_extract_claims_preserve_candidate_lifecycle() -> None:
    """KG-022 must extract claims without approving them."""

    content = "The chamber pressure is 20 bar.\n"
    result = _parse_and_extract(content)

    assert len(result.claims) == 1
    assert result.claims[0].lifecycle_state is GraphLifecycleState.CANDIDATE
    assert "chamber pressure" in result.claims[0].claim_text


def test_extract_relationships_link_quantities_to_entities() -> None:
    """KG-023 must create deterministic relationship candidates."""

    content = "\n".join(
        [
            "# Combustion Chamber",
            "Operating pressure 5 MPa.",
        ],
    )
    result = _parse_and_extract(content)

    assert result.entities
    assert result.quantities
    quantity_relationships = [
        relationship
        for relationship in result.relationships
        if relationship.relationship_type == "quantity_DESCRIBES_entity"
    ]

    assert quantity_relationships
    relationship = quantity_relationships[0]

    assert relationship.relationship_type == "quantity_DESCRIBES_entity"
    assert relationship.source_extraction_id == result.quantities[0].extraction_id
    assert relationship.target_extraction_id == result.entities[0].extraction_id


def test_extraction_is_deterministic() -> None:
    """Repeated extraction must produce identical serialized output."""

    content = "# Engine\nMaterial: LOX\nThe thrust is 100 kN.\n"

    first = _parse_and_extract(content)
    second = _parse_and_extract(content)

    assert first.to_mapping() == second.to_mapping()


def test_extraction_preserves_provenance_chain() -> None:
    """Extraction candidates must retain source and document provenance."""

    content = "# Engine\nMaterial: LOX\n"
    result = _parse_and_extract(content)
    entity = result.entities[0]

    assert entity.provenance.anchor.source_id == "SRC-001"
    assert entity.provenance.anchor.document_id == "ART-001"


def test_orchestrator_uses_default_registry() -> None:
    """Extraction orchestrator must dispatch through the default registry."""

    content = "# Title\n"
    digest = sha256_text_digest(content)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id="SRC-001",
            artifact_id="ART-001",
            content=content.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.MARKDOWN.value),
        ),
    )
    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
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
        ParseContext(ingestion_result=ingestion, normalized_content=content),
    )
    context = ExtractionContext(
        parsed_document=parse_result.parsed_document,
        normalized_content=content,
    )
    orchestrator = ExtractionOrchestrator(build_default_extraction_registry())

    extracted = orchestrator.extract(context)

    assert extracted.extractor_name == "cosmos-w4-extractor"


def test_ingestion_parse_extract_integration_path() -> None:
    """Integration path must run W2 → W3 → W4 without modifying frozen contracts."""

    content = "\n".join(
        [
            "# Propulsion",
            "Material: RP-1",
            "The chamber pressure is 20 bar.",
            "Thrust level is 50 kN.",
            "Equation $F = ma$ applies.",
        ],
    )
    result = _parse_and_extract(content)

    assert result.entities
    assert result.quantities
    assert result.equations
    assert result.claims
    assert result.extractor_version == "0.1.0"
