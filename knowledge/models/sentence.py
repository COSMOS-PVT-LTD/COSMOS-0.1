"""Canonical Sentence — provenance span over a W3 paragraph, not a second parser."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.document_structure import DocumentStructureNode, StructureKind
from knowledge.models.lifecycle import ProvenanceTrace

__all__ = ("Sentence",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Sentence:
    """Sentence-level provenance span referencing a parsed paragraph."""

    sentence_id: str
    document_id: str
    paragraph_id: str
    text: str
    provenance: ProvenanceTrace
    token_start: int | None = None
    token_end: int | None = None

    def __post_init__(self) -> None:
        if not self.sentence_id.strip() or not self.text.strip():
            raise ValueError("sentence_id and text are required.")
        if not self.paragraph_id.strip():
            raise ValueError("paragraph_id must reference a W3 paragraph.")

    def as_structure_node(self) -> DocumentStructureNode:
        return DocumentStructureNode(
            node_id=self.sentence_id,
            document_id=self.document_id,
            kind=StructureKind.SENTENCE,
            title=self.text[:80],
            parsed_artifact_id=self.paragraph_id,
            provenance=self.provenance,
            text=self.text,
        )
