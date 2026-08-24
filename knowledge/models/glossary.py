"""Canonical Glossary — typed view of definitional W3 content."""

from __future__ import annotations

from knowledge.models.document_structure import DocumentStructureNode, StructureKind

__all__ = ("Glossary", "as_glossary")


class Glossary(DocumentStructureNode):
    """Glossary is a document-structure node of kind GLOSSARY."""


def as_glossary(node: DocumentStructureNode) -> Glossary:
    if node.kind is not StructureKind.GLOSSARY:
        raise ValueError("node.kind must be GLOSSARY.")
    return Glossary(
        node_id=node.node_id,
        document_id=node.document_id,
        kind=StructureKind.GLOSSARY,
        title=node.title,
        parsed_artifact_id=node.parsed_artifact_id,
        provenance=node.provenance,
        parent_id=node.parent_id,
        page_start=node.page_start,
        page_end=node.page_end,
        text=node.text,
    )
