"""Canonical Appendix — typed view of a W3 appendix section."""

from __future__ import annotations

from knowledge.models.document_structure import DocumentStructureNode, StructureKind

__all__ = ("Appendix", "as_appendix")


class Appendix(DocumentStructureNode):
    """Appendix is a document-structure node of kind APPENDIX."""


def as_appendix(node: DocumentStructureNode) -> Appendix:
    if node.kind is not StructureKind.APPENDIX:
        raise ValueError("node.kind must be APPENDIX.")
    return Appendix(
        node_id=node.node_id,
        document_id=node.document_id,
        kind=StructureKind.APPENDIX,
        title=node.title,
        parsed_artifact_id=node.parsed_artifact_id,
        provenance=node.provenance,
        parent_id=node.parent_id,
        page_start=node.page_start,
        page_end=node.page_end,
        text=node.text,
    )
