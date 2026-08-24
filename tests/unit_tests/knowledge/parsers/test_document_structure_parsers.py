"""Document-structure parser adapters."""

from __future__ import annotations

from knowledge.parsers.appendix_parser import parse_appendices
from knowledge.parsers.glossary_parser import parse_glossaries
from knowledge.parsers.sentence_parser import parse_sentences


def test_appendix_and_glossary_parsers() -> None:
    appendices = parse_appendices(
        ("Appendix A — Nomenclature", "Introduction"),
        document_id="DOC-1",
        reference_id="REF-1",
    )
    glossaries = parse_glossaries(
        ("Glossary of Terms", "Results"),
        document_id="DOC-1",
        reference_id="REF-1",
    )
    assert len(appendices) == 1
    assert len(glossaries) == 1


def test_sentence_spans_preserve_paragraph_id() -> None:
    sentences = parse_sentences(
        "Coolant is single-phase. The Bartz correlation applies.",
        document_id="DOC-1",
        paragraph_id="P-001",
        reference_id="REF-1",
    )
    assert len(sentences) == 2
    assert all(item.paragraph_id == "P-001" for item in sentences)
