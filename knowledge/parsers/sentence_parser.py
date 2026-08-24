"""Sentence parser — spans over paragraph text, not a competing document parser."""

from __future__ import annotations

import re

from knowledge.models.lifecycle import ProvenanceTrace
from knowledge.models.sentence import Sentence

__all__ = ("parse_sentences",)

_SENTENCE = re.compile(r"(?s).+?(?:[.!?](?:\s|$)|$)")


def parse_sentences(
    paragraph_text: str,
    *,
    document_id: str,
    paragraph_id: str,
    reference_id: str,
) -> tuple[Sentence, ...]:
    items: list[Sentence] = []
    for index, match in enumerate(_SENTENCE.finditer(paragraph_text.strip())):
        text = match.group(0).strip()
        if not text:
            continue
        items.append(
            Sentence(
                sentence_id=f"{paragraph_id}-S{index:03d}",
                document_id=document_id,
                paragraph_id=paragraph_id,
                text=text,
                provenance=ProvenanceTrace(
                    source_reference_id=reference_id,
                    document_id=document_id,
                    extraction_method="sentence-span",
                ),
            ),
        )
    return tuple(items)
