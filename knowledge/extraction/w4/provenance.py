"""Provenance bridging from W3 parse provenance to graph extraction records."""

from __future__ import annotations

from knowledge.graph.contracts import ProvenanceReference
from knowledge.graph.provenance import ExtractionProvenance, SourceProvenanceRecord
from knowledge.parsers.w3.models import ParseProvenance

__all__ = (
    "EXTRACTOR_NAME",
    "EXTRACTOR_VERSION",
    "to_source_provenance",
)

EXTRACTOR_NAME = "cosmos-w4-extractor"
EXTRACTOR_VERSION = "0.1.0"


def to_source_provenance(
    parse_provenance: ParseProvenance,
    *,
    paragraph_id: str | None = None,
    table_id: str | None = None,
    equation_id: str | None = None,
    figure_id: str | None = None,
) -> SourceProvenanceRecord:
    """Bridge W3 ParseProvenance to frozen SourceProvenanceRecord."""

    location = parse_provenance.location
    page = location.page_number if location is not None else None
    section = location.section_id if location is not None else None

    anchor = ProvenanceReference(
        source_id=parse_provenance.source_id,
        document_id=parse_provenance.document_id,
        page=page,
        section=section,
        paragraph=paragraph_id,
        table=table_id,
        equation=equation_id,
        figure=figure_id,
    )

    extraction = ExtractionProvenance(
        extractor_tool=EXTRACTOR_NAME,
        extractor_version=EXTRACTOR_VERSION,
    )

    return SourceProvenanceRecord(anchor=anchor, extraction=extraction)
