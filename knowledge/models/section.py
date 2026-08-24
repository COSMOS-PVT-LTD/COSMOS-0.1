"""Canonical Section — typed view of a W3 parsed section."""

from __future__ import annotations

from knowledge.models.document_structure import DocumentStructureNode, StructureKind

__all__ = ("Section", "as_section")


class Section(DocumentStructureNode):
    """Section is a document-structure node of kind SECTION."""


def as_section(node: DocumentStructureNode) -> Section:
    if node.kind is not StructureKind.SECTION:
        raise ValueError("node.kind must be SECTION.")
    return Section(
        node_id=node.node_id,
        document_id=node.document_id,
        kind=StructureKind.SECTION,
        title=node.title,
        parsed_artifact_id=node.parsed_artifact_id,
        provenance=node.provenance,
        parent_id=node.parent_id,
        page_start=node.page_start,
        page_end=node.page_end,
        text=node.text,
    )
