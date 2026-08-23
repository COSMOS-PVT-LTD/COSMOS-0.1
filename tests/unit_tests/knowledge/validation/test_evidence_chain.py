"""Step 6 evidence-chain validation tests."""

from __future__ import annotations

from knowledge.extraction import CandidateEntityExtraction, ExtractedEntityKind
from knowledge.graph import ProvenanceReference
from knowledge.graph.entity import CanonicalEntityType
from knowledge.graph.provenance import SourceProvenanceRecord
from knowledge.extraction.w4.models import ExtractionResult
from knowledge.validation import ValidationContext, validate_evidence_chain


def test_validate_evidence_chain_flags_missing_document_anchor() -> None:
    """Evidence-chain validation must flag provenance without document anchors."""

    extraction = ExtractionResult(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        extractor_name="test",
        extractor_version="1.0",
        entities=(
            CandidateEntityExtraction(
                extraction_id="ENT-1",
                document_id="DOC-001",
                extracted_label="Pressure",
                entity_kind=ExtractedEntityKind.QUANTITY,
                canonical_entity_type=CanonicalEntityType.QUANTITY,
                provenance=SourceProvenanceRecord(
                    anchor=ProvenanceReference(source_id="SRC-001", page=1),
                ),
            ),
        ),
    )

    findings = validate_evidence_chain(
        ValidationContext(
            document_id="DOC-001",
            extraction_result=extraction,
        ),
    )

    assert any(finding.rule_id == "VAL-EVC-004" for finding in findings)


def test_validate_evidence_chain_passes_valid_entity() -> None:
    """Evidence-chain validation must pass when provenance anchors are present."""

    extraction = ExtractionResult(
        document_id="DOC-001",
        source_id="SRC-001",
        artifact_id="ART-001",
        extractor_name="test",
        extractor_version="1.0",
        entities=(
            CandidateEntityExtraction(
                extraction_id="ENT-1",
                document_id="DOC-001",
                extracted_label="Pressure",
                entity_kind=ExtractedEntityKind.QUANTITY,
                canonical_entity_type=CanonicalEntityType.QUANTITY,
                provenance=SourceProvenanceRecord(
                    anchor=ProvenanceReference(document_id="DOC-001", page=1),
                ),
            ),
        ),
    )

    findings = validate_evidence_chain(
        ValidationContext(
            document_id="DOC-001",
            extraction_result=extraction,
        ),
    )

    assert findings == ()
