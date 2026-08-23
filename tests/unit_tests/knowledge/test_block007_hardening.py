"""Engineering-review hardening tests for KG-BLOCK-007."""

from __future__ import annotations

import pytest

from knowledge.extraction.exceptions import ExtractionValidationError
from knowledge.extraction.w4 import (
    ExtractionContext,
    ExtractionInputError,
    ExtractionRegistry,
    UnsupportedExtractionError,
    W4ExtractionPipeline,
    deterministic_extraction_id,
    extract_document,
    extract_equation_candidates,
)
from knowledge.graph.lifecycle import GraphLifecycleState
from knowledge.parsers.w3.models import (
    LocationAnchor,
    ParsedEquation,
    ParseProvenance,
    StructuredParsedDocument,
)
from tests.unit_tests.knowledge.extraction.test_w4_extraction import _parse_and_extract


def test_entity_extraction_is_deterministic() -> None:
    """KG-019 must emit stable entity IDs across repeated extraction."""

    content = "# Combustion Chamber\nMaterial: Inconel 718\n"
    first = _parse_and_extract(content)
    second = _parse_and_extract(content)

    assert [entity.extraction_id for entity in first.entities] == [
        entity.extraction_id for entity in second.entities
    ]


def test_entity_extraction_avoids_unlabeled_noun_phrase_false_positives() -> None:
    """KG-019 must not classify ordinary prose noun phrases as entities."""

    content = "\n".join(
        [
            "# Introduction",
            "engine pressure varies during startup.",
            "pressure vessel integrity is monitored.",
            "combustion chamber temperature rises.",
        ],
    )
    result = _parse_and_extract(content)
    labels = {entity.extracted_label.lower() for entity in result.entities}

    assert "engine pressure" not in labels
    assert "pressure vessel" not in labels
    assert "combustion chamber" not in labels


def test_same_entity_label_in_distinct_sections_is_preserved() -> None:
    """KG-019 must not collapse identical labels from different sections."""

    content = "\n".join(
        [
            "# Section A",
            "Component: Main Injector",
            "# Section B",
            "Component: Main Injector",
        ],
    )
    result = _parse_and_extract(content)
    injector_entities = [
        entity
        for entity in result.entities
        if entity.extracted_label == "Main Injector"
    ]

    assert len(injector_entities) == 2


def test_quantity_extraction_preserves_distinct_occurrences() -> None:
    """KG-020 must not collapse identical values from different locations."""

    content = "\n".join(
        [
            "# Chamber A",
            "Pressure is 5 MPa.",
            "# Chamber B",
            "Pressure is 5 MPa.",
        ],
    )
    result = _parse_and_extract(content)

    assert len(result.quantities) == 2
    assert result.quantities[0].extraction_id != result.quantities[1].extraction_id


def test_quantity_without_unit_does_not_fabricate_units() -> None:
    """KG-020 must not invent units for bare numeric assignments."""

    content = "pressure = 20\n"
    result = _parse_and_extract(content)

    assert len(result.quantities) == 1
    quantity = result.quantities[0]

    assert quantity.unit_token is None
    assert quantity.dimensionless is True
    assert quantity.numeric_value == 20.0


def test_quantity_parsing_handles_representative_engineering_units() -> None:
    """KG-020 must parse common engineering quantity expressions."""

    content = "\n".join(
        [
            "# Data",
            "Values: 20 MPa, 300 K, 5 kg/s, 1.2 m, 10 kN, 0.85, 3.5e2 Pa.",
        ],
    )
    result = _parse_and_extract(content)
    raw_values = {quantity.raw_text for quantity in result.quantities}

    assert "20 MPa" in raw_values
    assert "300 K" in raw_values
    assert "5 kg/s" in raw_values
    assert "1.2 m" in raw_values
    assert "10 kN" in raw_values


def test_equation_extraction_rejects_executable_text_at_w4_boundary() -> None:
    """KG-021 must reject dangerous equation payloads even when W3 is bypassed."""

    provenance = ParseProvenance(
        source_id="SRC-001",
        artifact_id="ART-001",
        content_hash="hash",
        document_id="DOC-001",
        location=LocationAnchor(line_number=1),
    )
    document = StructuredParsedDocument(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        parser_name="test-parser",
        parser_version="0.0.0",
        normalized_content_hash="hash",
        equations=(
            ParsedEquation(
                equation_id="eq-001",
                normalized_text="__import__('os')",
                provenance=provenance,
            ),
        ),
    )
    context = ExtractionContext(
        parsed_document=document,
        normalized_content="__import__('os')",
    )

    with pytest.raises(ExtractionInputError):
        extract_equation_candidates(context)


def test_claim_extraction_preserves_source_certainty_wording() -> None:
    """KG-022 must retain original claim wording without rewriting certainty."""

    measured = "The chamber pressure was measured at 19.8 MPa."
    expected = "The chamber pressure is expected to be approximately 20 MPa."

    measured_result = _parse_and_extract(measured)
    expected_result = _parse_and_extract(expected)

    assert measured_result.claims == ()
    assert len(expected_result.claims) == 1
    assert expected_result.claims[0].claim_text == expected
    assert expected_result.claims[0].lifecycle_state is GraphLifecycleState.CANDIDATE


def test_relationship_extraction_is_deterministically_ordered() -> None:
    """KG-023 must emit stable relationship ordering."""

    content = "\n".join(
        [
            "# Combustion Chamber",
            "Operating pressure 5 MPa.",
            "The chamber pressure is 20 bar.",
        ],
    )
    first = _parse_and_extract(content)
    second = _parse_and_extract(content)

    assert [item.relationship_id for item in first.relationships] == [
        item.relationship_id for item in second.relationships
    ]


def test_registry_rejects_duplicate_extractor_names() -> None:
    """Registry must reject duplicate extractor registrations."""

    with pytest.raises(ExtractionValidationError, match="Duplicate extractor"):
        ExtractionRegistry((W4ExtractionPipeline(), W4ExtractionPipeline()))


def test_deterministic_extraction_id_is_stable() -> None:
    """Identity generation must be stable and prefix-qualified."""

    first = deterministic_extraction_id("ent", "DOC-001", "key-a", "label")
    second = deterministic_extraction_id("ent", "DOC-001", "key-a", "label")
    different = deterministic_extraction_id("ent", "DOC-001", "key-b", "label")

    assert first == second
    assert first != different
    assert first.startswith("ent-")


def test_empty_document_extraction_returns_empty_candidates() -> None:
    """Pipeline must safely handle documents with no extractable content."""

    document = StructuredParsedDocument(
        document_id="DOC-EMPTY",
        source_id="SRC-001",
        artifact_id="ART-001",
        parser_name="test-parser",
        parser_version="0.0.0",
        normalized_content_hash="hash",
    )
    result = extract_document(
        ExtractionContext(parsed_document=document, normalized_content=""),
    )

    assert result.entities == ()
    assert result.quantities == ()
    assert result.equations == ()
    assert result.claims == ()
    assert result.relationships == ()


def test_provenance_survives_w3_to_w4_integration() -> None:
    """Provenance chain must survive ingestion → parse → extraction."""

    content = "# Engine\nMaterial: LOX\n"
    result = _parse_and_extract(content)
    entity = next(entity for entity in result.entities if entity.extracted_label == "LOX")

    assert entity.provenance.anchor.source_id == "SRC-001"
    assert entity.provenance.anchor.document_id == "ART-001"
    assert entity.provenance.extraction.extractor_tool == "cosmos-w4-extractor"


def test_orchestrator_rejects_unknown_extractor_name() -> None:
    """Registry lookup must fail clearly for unsupported extractors."""

    registry = ExtractionRegistry((W4ExtractionPipeline(),))

    with pytest.raises(UnsupportedExtractionError):
        registry.get("unknown-extractor")


def test_identity_rejects_empty_prefix_or_document_id() -> None:
    """Identity helper must reject empty required inputs."""

    with pytest.raises(ValueError):
        deterministic_extraction_id("", "DOC-001", "part")

    with pytest.raises(ValueError):
        deterministic_extraction_id("ent", "", "part")
