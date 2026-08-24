"""Glossary parser — W3 heading adapter."""

from __future__ import annotations

from knowledge.models.document_structure import DocumentStructureNode, StructureKind
from knowledge.models.glossary import Glossary
from knowledge.models.lifecycle import ProvenanceTrace

__all__ = ("parse_glossaries",)


def parse_glossaries(
    headings: tuple[str, ...],
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Glossary, ...]:
    items: list[Glossary] = []
    for index, heading in enumerate(headings):
        if "glossary" not in heading.lower():
            continue
        node = DocumentStructureNode(
            node_id=f"GLOSS-{index:03d}",
            document_id=document_id,
            kind=StructureKind.GLOSSARY,
            title=heading,
            parsed_artifact_id=f"w3-section-glossary-{index}",
            provenance=ProvenanceTrace(
                source_reference_id=reference_id,
                document_id=document_id,
                extraction_method="w3-heading",
            ),
        )
        items.append(
            Glossary(
                node_id=node.node_id,
                document_id=node.document_id,
                kind=node.kind,
                title=node.title,
                parsed_artifact_id=node.parsed_artifact_id,
                provenance=node.provenance,
                parent_id=node.parent_id,
                page_start=node.page_start,
                page_end=node.page_end,
                text=node.text,
            ),
        )
    return tuple(items)
