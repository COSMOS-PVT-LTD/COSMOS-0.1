"""
W3 parsing pipeline orchestrating KG-014 → KG-018.
"""

from __future__ import annotations

from dataclasses import replace

from knowledge.graph.provenance import ExtractionProvenance
from knowledge.ingestion.models import IngestionStage, NormalizedDocumentFormat
from knowledge.parsers.w3.content import ParseContext, ParseResult
from knowledge.parsers.w3.exceptions import ParserContentError
from knowledge.parsers.w3.equations import extract_equations
from knowledge.parsers.w3.figures import extract_figures
from knowledge.parsers.w3.models import StructuredParsedDocument
from knowledge.parsers.w3.references import extract_citations, extract_references
from knowledge.parsers.w3.structure import parse_document_structure
from knowledge.parsers.w3.tables import extract_tables

__all__ = (
    "PARSER_NAME",
    "PARSER_VERSION",
    "W3DocumentParser",
    "parse_document",
)

PARSER_NAME = "cosmos-w3-document-parser"
PARSER_VERSION = "0.1.0"


class W3DocumentParser:
    """Production W3 parser consuming normalized ingestion output."""

    @property
    def parser_name(self) -> str:
        return PARSER_NAME

    @property
    def parser_version(self) -> str:
        return PARSER_VERSION

    def parse(self, context: ParseContext) -> ParseResult:
        return parse_document(context)


def parse_document(context: ParseContext) -> ParseResult:
    """Parse normalized content into a structured W3 document representation."""

    if context.ingestion_result.stage not in (
        IngestionStage.NORMALIZED,
        IngestionStage.REGISTERED,
    ):
        raise ParserContentError(
            "Parser requires ingestion stage NORMALIZED or REGISTERED."
        )

    context.verify_content_hash()

    content = context.normalized_content
    is_structured = (
        context.normalized_format == NormalizedDocumentFormat.STRUCTURED_TEXT
    )
    document_id = context.document_id
    source_id = context.source_id
    artifact_id = context.artifact_id
    content_hash = context.ingestion_result.normalized_content_hash

    structure = parse_document_structure(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        is_structured_envelope=is_structured,
    )
    tables = extract_tables(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        is_structured_envelope=is_structured,
    )
    figures = extract_figures(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        is_structured_envelope=is_structured,
    )
    equations = extract_equations(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
    )
    references = extract_references(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
    )
    reference_ids_by_key = {
        str(reference.ordering_index): reference.reference_id
        for reference in references
    }
    citations = extract_citations(
        content=content,
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        content_hash=content_hash,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        reference_ids_by_key=reference_ids_by_key,
    )

    parsed_document = StructuredParsedDocument(
        document_id=document_id,
        source_id=source_id,
        artifact_id=artifact_id,
        parser_name=PARSER_NAME,
        parser_version=PARSER_VERSION,
        normalized_content_hash=content_hash,
        sections=structure.sections,
        paragraphs=structure.paragraphs,
        tables=tables,
        figures=figures,
        equations=equations,
        citations=citations,
        references=references,
        extraction=ExtractionProvenance(
            extractor_tool=PARSER_NAME,
            extractor_version=PARSER_VERSION,
        ),
    )

    advanced_ingestion = replace(
        context.ingestion_result,
        stage=IngestionStage.PARSED,
        document_id=document_id,
    )

    return ParseResult(
        parsed_document=parsed_document,
        ingestion_result=advanced_ingestion,
    )
