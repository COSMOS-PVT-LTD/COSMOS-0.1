"""Unit tests for knowledge.graph.provenance."""

from __future__ import annotations

import pytest

from knowledge.graph import GraphValidationError, ProvenanceReference
from knowledge.graph.provenance import (
    ExtractionProvenance,
    ReviewStatus,
    SourceLineage,
    SourceProvenanceRecord,
)


def test_extraction_provenance_valid_construction() -> None:
    """Extraction provenance must retain tool and ontology metadata."""

    extraction = ExtractionProvenance(
        extractor_tool="cosmos-pdf-parser",
        extractor_version="0.1.0",
        ontology_version="kg-ontology-0.1",
        review_status=ReviewStatus.CANDIDATE,
    )

    assert extraction.extractor_tool == "cosmos-pdf-parser"
    assert extraction.ontology_version == "kg-ontology-0.1"
    assert extraction.review_status is ReviewStatus.CANDIDATE


def test_extraction_provenance_rejects_blank_tool() -> None:
    """Extractor tool identifiers must not be blank."""

    with pytest.raises(GraphValidationError):
        ExtractionProvenance(
            extractor_tool="",
            extractor_version="0.1.0",
        )


def test_source_lineage_requires_anchor_field() -> None:
    """Lineage objects must include at least one populated field."""

    with pytest.raises(GraphValidationError):
        SourceLineage()


def test_source_lineage_supports_parent_source() -> None:
    """Lineage may reference a parent source identifier."""

    lineage = SourceLineage(parent_source_id="SRC-001")

    assert lineage.parent_source_id == "SRC-001"


def test_source_provenance_record_wraps_anchor() -> None:
    """Composite provenance must preserve the KG-001 anchor."""

    record = SourceProvenanceRecord(
        anchor=ProvenanceReference(
            source_id="SRC-001",
            document_id="DOC-001",
            page=12,
        ),
        extraction=ExtractionProvenance(
            extractor_tool="cosmos-extractor",
            extractor_version="0.1.0",
        ),
        lineage=SourceLineage(parent_artifact_id="ART-001"),
    )

    assert record.anchor.page == 12
    assert record.extraction is not None
    assert record.lineage is not None


def test_source_provenance_record_rejects_invalid_anchor() -> None:
    """Composite provenance must reject non-anchor provenance values."""

    with pytest.raises(GraphValidationError):
        SourceProvenanceRecord(anchor="not-a-provenance-reference")  # type: ignore[arg-type]


def test_source_provenance_record_mapping_is_structured() -> None:
    """Composite provenance mappings must include nested sections."""

    record = SourceProvenanceRecord(
        anchor=ProvenanceReference(document_id="DOC-002"),
    )

    mapping = record.to_mapping()

    assert mapping["anchor"] == {"document_id": "DOC-002"}
    assert "extraction" not in mapping
