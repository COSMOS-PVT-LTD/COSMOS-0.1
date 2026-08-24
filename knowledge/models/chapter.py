"""Canonical Chapter — typed view of a W3 section hierarchy node."""

from __future__ import annotations

from knowledge.models.document_structure import DocumentStructureNode, StructureKind

__all__ = ("Chapter", "as_chapter")


class Chapter(DocumentStructureNode):
    """Chapter is a document-structure node of kind CHAPTER."""


def as_chapter(node: DocumentStructureNode) -> Chapter:
    if node.kind is not StructureKind.CHAPTER:
        raise ValueError("node.kind must be CHAPTER.")
    return Chapter(
        node_id=node.node_id,
        document_id=node.document_id,
        kind=StructureKind.CHAPTER,
        title=node.title,
        parsed_artifact_id=node.parsed_artifact_id,
        provenance=node.provenance,
        parent_id=node.parent_id,
        page_start=node.page_start,
        page_end=node.page_end,
        text=node.text,
    )
