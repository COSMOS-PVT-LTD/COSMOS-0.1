"""Unit tests for KG-BLOCK-006 W3 parsing."""

from __future__ import annotations

import json

import pytest

from knowledge.ingestion import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    IngestionStage,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.normalize import build_structured_text_envelope
from knowledge.parsers.w3 import (
    ParseContext,
    ParserContentError,
    ParserEquationError,
    ParserOrchestrator,
    ParserTableError,
    UnsupportedStructureError,
    build_default_parser_registry,
    parse_document,
)
from knowledge.source.integrity import sha256_text_digest


def _ingestion_result(
    *,
    content: str,
    normalized_format: NormalizedDocumentFormat = NormalizedDocumentFormat.MARKDOWN,
    document_id: str = "DOC-001",
) -> IngestionResult:
    artifact = IngestionArtifactRef(
        source_id="SRC-001",
        artifact_id="ART-001",
        source_format=SourceFormat.MARKDOWN,
        content_hash=sha256_text_digest(content),
    )

    return IngestionResult(
        request=IngestionRequest(
            artifact=artifact,
            adapter_name="cosmos-markdown-ingestion",
            adapter_version="0.1.0",
        ),
        normalized_format=normalized_format,
        normalized_content_hash=sha256_text_digest(content),
        parser_version="cosmos-markdown-ingestion-0.1.0",
        document_id=document_id,
    )


def _parse(content: str, **kwargs: object) -> object:
    ingestion = _ingestion_result(content=content, **kwargs)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )

    return parse_document(context)


def test_parse_document_structure_hierarchy_and_ordering() -> None:
    """KG-014 must preserve heading hierarchy and paragraph ordering."""

    content = "\n".join(
        [
            "# Introduction",
            "First paragraph.",
            "## Methods",
            "Second paragraph.",
        ],
    )
    result = _parse(content)

    assert len(result.parsed_document.sections) == 2
    assert result.parsed_document.sections[0].level == 1
    assert result.parsed_document.sections[1].level == 2
    assert len(result.parsed_document.paragraphs) == 2
    assert result.parsed_document.paragraphs[0].ordering_index == 1
    assert result.parsed_document.paragraphs[1].ordering_index == 2


def test_parse_document_is_deterministic() -> None:
    """Repeated parsing must produce identical serialized output."""

    content = "# Title\n\nBody paragraph.\n"

    first = _parse(content)
    second = _parse(content)

    assert first.parsed_document.to_mapping() == second.parsed_document.to_mapping()


def test_parse_empty_document_structure() -> None:
    """Empty documents must parse without fabricated structure."""

    result = _parse("   \n\n  ")

    assert result.parsed_document.sections == ()
    assert result.parsed_document.paragraphs == ()


def test_parse_rejects_content_hash_mismatch() -> None:
    """Parser must reject normalized content that does not match ingestion hash."""

    content = "# Title"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content="# Different",
    )

    with pytest.raises(Exception):
        parse_document(context)


def test_extract_markdown_table() -> None:
    """KG-015 must parse markdown tables with headers and rows."""

    content = "\n".join(
        [
            "# Data",
            "| Name | Value |",
            "| --- | --- |",
            "| Pressure | 100 |",
        ],
    )
    result = _parse(content)

    assert len(result.parsed_document.tables) == 1
    table = result.parsed_document.tables[0]
    assert table.column_count == 2
    assert len(table.rows) == 2
    assert table.rows[0].cells[0].is_header is True


def test_extract_xlsx_envelope_table() -> None:
    """KG-015 must parse XLSX structured envelopes."""

    envelope = build_structured_text_envelope(
        {
            "cells": [{"cell": "A1", "value": "Header"}, {"cell": "B1", "value": "100"}],
            "format": "XLSX",
        },
    )
    ingestion = _ingestion_result(
        content=envelope,
        normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
    )
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=envelope,
    )
    result = parse_document(context)

    assert len(result.parsed_document.tables) == 1
    assert result.parsed_document.tables[0].rows[0].cells[0].value == "Header"


def test_extract_figure_metadata() -> None:
    """KG-016 must capture figure caption and source reference."""

    content = "![Chamber diagram](figures/chamber.png)\n"
    result = _parse(content)

    assert len(result.parsed_document.figures) == 1
    assert result.parsed_document.figures[0].caption == "Chamber diagram"
    assert result.parsed_document.figures[0].source_reference == "figures/chamber.png"


def test_extract_equations_without_execution() -> None:
    """KG-017 must extract equations as text without evaluation."""

    content = "Inline $F = ma$ and block:\n\n$$E = mc^2$$\n"
    result = _parse(content)

    assert len(result.parsed_document.equations) == 2
    assert result.parsed_document.equations[1].normalized_text == "E = mc^2"
    assert "E" in result.parsed_document.equations[1].variable_references


def test_extract_equations_rejects_executable_patterns() -> None:
    """KG-017 must reject executable-looking equation text."""

    content = "$$__import__('os')$$\n"

    with pytest.raises(ParserEquationError):
        _parse(content)


def test_extract_references_and_citations() -> None:
    """KG-018 must distinguish citation occurrences from reference records."""

    content = "\n".join(
        [
            "Result shown in prior work [1].",
            "",
            "# References",
            "1. Chamber Design Study (2020)",
        ],
    )
    result = _parse(content)

    assert len(result.parsed_document.references) == 1
    assert len(result.parsed_document.citations) == 1
    assert result.parsed_document.citations[0].reference_id == (
        result.parsed_document.references[0].reference_id
    )


def test_parse_advances_ingestion_stage_to_parsed() -> None:
    """Successful parsing must advance ingestion stage to PARSED."""

    result = _parse("# Title\n")

    assert result.ingestion_result.stage == IngestionStage.PARSED


def test_parse_preserves_provenance_fields() -> None:
    """Parsed elements must retain source and artifact provenance."""

    result = _parse("# Title\n\nParagraph.\n")
    paragraph = result.parsed_document.paragraphs[0]

    assert paragraph.provenance.source_id == "SRC-001"
    assert paragraph.provenance.artifact_id == "ART-001"
    assert paragraph.provenance.document_id == "DOC-001"


def test_html_envelope_structure_parsing() -> None:
    """Structured HTML envelopes must parse sections and paragraphs."""

    envelope = build_structured_text_envelope(
        {
            "blocks": [
                {"tag": "h1", "text": "Title"},
                {"tag": "p", "text": "Body"},
            ],
            "format": "HTML",
        },
    )
    ingestion = _ingestion_result(
        content=envelope,
        normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
    )
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=envelope,
    )
    result = parse_document(context)

    assert len(result.parsed_document.sections) == 1
    assert len(result.parsed_document.paragraphs) == 1


def test_binary_envelope_parses_without_structure() -> None:
    """Binary PDF envelopes without text must not fabricate structure."""

    envelope = json.dumps(
        {
            "binary": True,
            "byte_length": 10,
            "content_hash": "a" * 64,
            "format": "PDF",
            "text_available": False,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    ingestion = _ingestion_result(
        content=envelope,
        normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
    )
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=envelope,
    )
    result = parse_document(context)

    assert result.parsed_document.sections == ()
    assert result.parsed_document.paragraphs == ()


def test_malformed_table_envelope_raises() -> None:
    """Malformed structured table input must raise a typed parser error."""

    envelope = build_structured_text_envelope({"format": "XLSX", "cells": "invalid"})
    ingestion = _ingestion_result(
        content=envelope,
        normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
    )
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=envelope,
    )

    with pytest.raises(ParserTableError):
        parse_document(context)


def test_unsupported_envelope_format_raises() -> None:
    """Unsupported structured formats must fail explicitly."""

    envelope = build_structured_text_envelope({"format": "UNKNOWN"})
    ingestion = _ingestion_result(
        content=envelope,
        normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
    )
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=envelope,
    )

    with pytest.raises(UnsupportedStructureError):
        parse_document(context)


def test_parser_orchestrator_uses_default_registry() -> None:
    """Parser orchestrator must dispatch through the default registry."""

    content = "# Orchestrator\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )
    orchestrator = ParserOrchestrator(build_default_parser_registry())

    result = orchestrator.parse(context)

    assert result.parsed_document.parser_name == "cosmos-w3-document-parser"


def test_ingestion_to_parse_integration_path() -> None:
    """Integration path must preserve provenance from ingestion through parsing."""

    from knowledge.ingestion_adapters import MarkdownIngestionAdapter
    from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata

    markdown = "# Integration\n\nBody with $x = 1$.\n"
    vault = InMemorySourceVault()
    digest = sha256_text_digest(markdown)
    vault.store(
        VaultArtifact(
            source_id="SRC-INT",
            artifact_id="ART-INT",
            content=markdown.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.MARKDOWN.value),
        ),
    )
    artifact = IngestionArtifactRef(
        source_id="SRC-INT",
        artifact_id="ART-INT",
        source_format=SourceFormat.MARKDOWN,
        content_hash=digest,
    )
    adapter = MarkdownIngestionAdapter(vault)
    request = IngestionRequest(
        artifact=artifact,
        adapter_name=adapter.adapter_name,
        adapter_version=adapter.adapter_version,
    )
    ingestion_result = adapter.ingest(request)

    context = ParseContext(
        ingestion_result=ingestion_result,
        normalized_content=markdown,
    )
    parse_result = parse_document(context)

    assert parse_result.ingestion_result.stage == IngestionStage.PARSED
    assert parse_result.parsed_document.source_id == "SRC-INT"
    assert parse_result.parsed_document.normalized_content_hash == (
        ingestion_result.normalized_content_hash
    )
    assert len(parse_result.parsed_document.equations) == 1


def test_adversarial_script_content_is_data_not_executed() -> None:
    """Script-like content must be stored as paragraph length metadata only."""

    content = "<script>alert('x')</script>\n"
    result = _parse(content)

    assert len(result.parsed_document.paragraphs) == 1
    assert result.parsed_document.paragraphs[0].text_length > 0


def test_parse_context_rejects_invalid_ingestion_result() -> None:
    """ParseContext must validate ingestion result type."""

    with pytest.raises(ParserContentError):
        ParseContext(ingestion_result="invalid", normalized_content="x")  # type: ignore[arg-type]
