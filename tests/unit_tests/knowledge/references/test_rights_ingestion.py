"""Rights-aware reference ingestion. UNKNOWN is never treated as cleared."""

from __future__ import annotations

from knowledge.foundation import KnowledgeFoundationService
from knowledge.pdf.corpus import nasa_class_pdf_bytes, reynolds_pdf_bytes
from knowledge.pdf.models import ExtractionStatus
from knowledge.references import (
    DocumentClass,
    ReferenceIngestRequest,
    RightsRecord,
    RightsStatus,
    validate_reference_ingest,
)


def test_unknown_and_restricted_rights_are_blocked() -> None:
    unknown = ReferenceIngestRequest(
        source_id="SRC-U",
        document_id="DOC-U",
        title="unknown",
        filename="u.pdf",
        rights=RightsRecord(status=RightsStatus.UNKNOWN),
        document_class=DocumentClass.UNKNOWN,
    )
    restricted = ReferenceIngestRequest(
        source_id="SRC-R",
        document_id="DOC-R",
        title="restricted",
        filename="r.pdf",
        rights=RightsRecord(status=RightsStatus.RESTRICTED),
        document_class=DocumentClass.ROCKET_PROPULSION_TEXTBOOK,
    )
    assert validate_reference_ingest(unknown).accepted is False
    assert validate_reference_ingest(restricted).accepted is False
    service = KnowledgeFoundationService()
    blocked = service.ingest_reference_pdf(
        reynolds_pdf_bytes(),
        unknown,
        reference_id="REF-U",
    )
    assert blocked.status is ExtractionStatus.RIGHTS_BLOCKED
    assert blocked.equation_candidates == ()
    assert blocked.registered is None


def test_internal_nasa_class_fixture_is_ingestible() -> None:
    request = ReferenceIngestRequest(
        source_id="SRC-NASA-CLASS",
        document_id="DOC-NASA-CLASS",
        title="COSMOS NASA-class structural fixture",
        filename="nasa_class.pdf",
        rights=RightsRecord(
            status=RightsStatus.INTERNAL,
            notes="COSMOS original. Not a NASA publication.",
        ),
        document_class=DocumentClass.NASA_TECHNICAL_REPORT,
        author="COSMOS",
        organization="COSMOS",
        publication_year=2026,
    )
    assert validate_reference_ingest(request).accepted is True
    service = KnowledgeFoundationService()
    result = service.ingest_reference_pdf(
        nasa_class_pdf_bytes(),
        request,
        reference_id="REF-NASA-CLASS",
    )
    assert result.status is ExtractionStatus.TEXT_AVAILABLE
    assert result.registered is not None
    assert result.registered.rights_status is RightsStatus.INTERNAL
    assert result.registered.document_class is DocumentClass.NASA_TECHNICAL_REPORT
    assert result.equation_candidates
    assert "not a nasa publication" in result.recovered_text.lower()
    assert result.authoritative is False
