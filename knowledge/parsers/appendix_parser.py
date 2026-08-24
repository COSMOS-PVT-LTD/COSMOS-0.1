"""Appendix parser — W3 structure adapter, not a second parser."""

from __future__ import annotations

from knowledge.models.appendix import Appendix
from knowledge.models.document_structure import DocumentStructureNode, StructureKind
from knowledge.models.lifecycle import ProvenanceTrace

__all__ = ("parse_appendices",)


def parse_appendices(
    headings: tuple[str, ...],
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Appendix, ...]:
    nodes: list[Appendix] = []
    for index, heading in enumerate(headings):
        if not heading.lower().startswith("appendix"):
            continue
        node = DocumentStructureNode(
            node_id=f"APP-{index:03d}",
            document_id=document_id,
            kind=StructureKind.APPENDIX,
            title=heading,
            parsed_artifact_id=f"w3-section-appendix-{index}",
            provenance=ProvenanceTrace(
                source_reference_id=reference_id,
                document_id=document_id,
                extraction_method="w3-heading",
            ),
        )
        nodes.append(
            Appendix(
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
    return tuple(nodes)
