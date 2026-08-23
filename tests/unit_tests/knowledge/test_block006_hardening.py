"""Engineering-review hardening tests for KG-BLOCK-006."""

from __future__ import annotations

import pytest

from knowledge.ingestion import IngestionStage
from knowledge.parsers.w3 import (
    ParseContext,
    ParserContentError,
    ParserEquationError,
    ParserStructureError,
    parse_document,
)
from knowledge.source.integrity import sha256_text_digest
from tests.unit_tests.knowledge.parsers.test_w3_parsing import _ingestion_result


def test_section_parent_child_hierarchy_is_preserved() -> None:
    """KG-014 must link nested sections through parent_section_id."""

    content = "# Root\n## Child\n### Grandchild\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )
    result = parse_document(context)
    sections = result.parsed_document.sections

    assert len(sections) == 3
    assert sections[0].parent_section_id is None
    assert sections[1].parent_section_id == sections[0].section_id
    assert sections[2].parent_section_id == sections[1].section_id


def test_blank_heading_raises_structure_error() -> None:
    """Blank headings must fail with a structure parser error."""

    from knowledge.ingestion import NormalizedDocumentFormat
    from knowledge.ingestion_adapters.normalize import build_structured_text_envelope

    envelope = build_structured_text_envelope(
        {
            "blocks": [{"tag": "h1", "text": "   "}],
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

    with pytest.raises(ParserStructureError):
        parse_document(context)


def test_citations_ignore_markdown_links() -> None:
    """Citation parser must not treat markdown links as citations."""

    content = "See [documentation](https://example.com) for details.\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )
    result = parse_document(context)

    assert result.parsed_document.citations == ()


def test_parser_rejects_already_parsed_stage() -> None:
    """Parser must reject ingestion artifacts already in PARSED stage."""

    content = "# Title\n"
    ingestion = _ingestion_result(content=content)
    parsed_ingestion = ingestion.__class__(
        request=ingestion.request,
        normalized_format=ingestion.normalized_format,
        normalized_content_hash=ingestion.normalized_content_hash,
        parser_version=ingestion.parser_version,
        stage=IngestionStage.PARSED,
        document_id=ingestion.document_id,
    )
    context = ParseContext(
        ingestion_result=parsed_ingestion,
        normalized_content=content,
    )

    with pytest.raises(ParserContentError):
        parse_document(context)


def test_inline_equation_rejects_eval_payload() -> None:
    """Inline equations must reject executable-looking payloads."""

    content = "$eval('1+1')$\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )

    with pytest.raises(ParserEquationError):
        parse_document(context)


def test_unresolved_citation_preserves_citation_key() -> None:
    """Unresolved citations must retain citation_key for downstream handling."""

    content = "Prior work [unknown-ref] is cited.\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )
    result = parse_document(context)

    assert len(result.parsed_document.citations) == 1
    citation = result.parsed_document.citations[0]
    assert citation.reference_id is None
    assert citation.citation_key == "unknown-ref"


def test_ragged_markdown_table_preserves_row_order() -> None:
    """Ragged markdown tables must preserve deterministic row ordering."""

    content = "\n".join(
        [
            "| A | B |",
            "| --- | --- |",
            "| one |",
            "| one | two | three |",
        ],
    )
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )
    result = parse_document(context)
    table = result.parsed_document.tables[0]

    assert len(table.rows) == 3
    assert table.rows[0].row_index == 0
    assert table.rows[2].row_index == 2
    assert table.rows[2].cells[-1].value == "three"


def test_frozen_ingestion_contract_import_smoke() -> None:
    """W3 must remain compatible with frozen ingestion contracts."""

    from knowledge.ingestion import IngestionResult, SourceFormat
    from knowledge.parsers import DocumentParser, NormalizedParsedDocument

    assert IngestionResult is not None
    assert SourceFormat.MARKDOWN.value == "MARKDOWN"
    assert DocumentParser is not None
    assert NormalizedParsedDocument is not None


def test_serialization_round_trip_is_stable() -> None:
    """Serialized parsed output must be stable across repeated execution."""

    content = "# Stable\n\n| a | b |\n| - | - |\n| 1 | 2 |\n"
    ingestion = _ingestion_result(content=content)
    context = ParseContext(
        ingestion_result=ingestion,
        normalized_content=content,
    )

    first = parse_document(context).parsed_document.to_mapping()
    second = parse_document(context).parsed_document.to_mapping()

    assert first == second
    assert sha256_text_digest(str(first)) == sha256_text_digest(str(second))
