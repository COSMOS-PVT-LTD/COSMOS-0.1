"""Canonical document structure — wraps W3 parse artifacts, does not duplicate them."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from knowledge.models.lifecycle import ProvenanceTrace

__all__ = (
    "CanonicalDocumentStructure",
    "DocumentStructureNode",
    "StructureKind",
)


class StructureKind(Enum):
    """Document-semantic node kinds mapped from W3 parse artifacts."""

    CHAPTER = "CHAPTER"
    SECTION = "SECTION"
    APPENDIX = "APPENDIX"
    GLOSSARY = "GLOSSARY"
    SENTENCE = "SENTENCE"
    PARAGRAPH = "PARAGRAPH"


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentStructureNode:
    """Canonical structure node that references a W3 parsed object."""

    node_id: str
    document_id: str
    kind: StructureKind
    title: str
    parsed_artifact_id: str
    provenance: ProvenanceTrace
    parent_id: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    text: str | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.document_id.strip():
            raise ValueError("node_id and document_id are required.")
        if not self.parsed_artifact_id.strip():
            raise ValueError("parsed_artifact_id must reference a W3 artifact.")


@dataclass(frozen=True, slots=True, kw_only=True)
class CanonicalDocumentStructure:
    """Document-level structure assembled from W3 parse output."""

    document_id: str
    nodes: tuple[DocumentStructureNode, ...]

    def nodes_of(self, kind: StructureKind) -> tuple[DocumentStructureNode, ...]:
        return tuple(node for node in self.nodes if node.kind is kind)
