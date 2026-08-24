"""Recover document structure from extracted page text. Never invents headings."""

from __future__ import annotations

from dataclasses import dataclass
import re

from knowledge.models.document_structure import DocumentStructureNode, StructureKind
from knowledge.models.lifecycle import ProvenanceTrace
from knowledge.pdf.models import PageExtraction

__all__ = ("ExtractedDocumentStructure", "extract_document_structure")

_CHAPTER = re.compile(r"^(chapter\s+\d+\b.*)$", re.IGNORECASE)
_SECTION = re.compile(r"^(\d+\.\d+)\s+(.+)$")
_FIGURE = re.compile(r"^(figure|fig\.)\s+\d+", re.IGNORECASE)
_TABLE = re.compile(r"^table\s+\d+", re.IGNORECASE)
_EQUATION_LABEL = re.compile(r"(eq(?:uation)?\.?\s*[\d.-]+|\(\d+(?:\.\d+)?\))", re.IGNORECASE)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractedDocumentStructure:
    document_id: str
    nodes: tuple[DocumentStructureNode, ...]
    paragraphs: tuple[DocumentStructureNode, ...]
    headings: tuple[DocumentStructureNode, ...]
    captions: tuple[DocumentStructureNode, ...]
    equation_labels: tuple[str, ...]

    def nodes_of(self, kind: StructureKind) -> tuple[DocumentStructureNode, ...]:
        return tuple(node for node in self.nodes if node.kind is kind)


def extract_document_structure(
    pages: tuple[PageExtraction, ...],
    *,
    document_id: str,
    reference_id: str,
) -> ExtractedDocumentStructure:
    nodes: list[DocumentStructureNode] = []
    paragraphs: list[DocumentStructureNode] = []
    headings: list[DocumentStructureNode] = []
    captions: list[DocumentStructureNode] = []
    labels: list[str] = []
    parent_id: str | None = None
    counter = 0

    for page in pages:
        for raw_line in page.text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            counter += 1
            node_id = f"{document_id}-n{counter:04d}"
            provenance = ProvenanceTrace(
                source_reference_id=reference_id,
                document_id=document_id,
                page=page.page_number,
                extraction_method="pdf-structure",
            )
            label_match = _EQUATION_LABEL.search(line)
            if label_match:
                labels.append(label_match.group(0))
            if _CHAPTER.match(line):
                node = DocumentStructureNode(
                    node_id=node_id,
                    document_id=document_id,
                    kind=StructureKind.CHAPTER,
                    title=line,
                    parsed_artifact_id=f"{document_id}-p{page.page_number}",
                    provenance=provenance,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    text=line,
                )
                parent_id = node_id
                headings.append(node)
                nodes.append(node)
                continue
            if _SECTION.match(line):
                node = DocumentStructureNode(
                    node_id=node_id,
                    document_id=document_id,
                    kind=StructureKind.SECTION,
                    title=line,
                    parsed_artifact_id=f"{document_id}-p{page.page_number}",
                    provenance=provenance,
                    parent_id=parent_id,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    text=line,
                )
                headings.append(node)
                nodes.append(node)
                continue
            if _FIGURE.match(line) or _TABLE.match(line):
                node = DocumentStructureNode(
                    node_id=node_id,
                    document_id=document_id,
                    kind=StructureKind.PARAGRAPH,
                    title=line,
                    parsed_artifact_id=f"{document_id}-p{page.page_number}",
                    provenance=provenance,
                    parent_id=parent_id,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    text=line,
                )
                captions.append(node)
                nodes.append(node)
                continue
            node = DocumentStructureNode(
                node_id=node_id,
                document_id=document_id,
                kind=StructureKind.PARAGRAPH,
                title=line[:80],
                parsed_artifact_id=f"{document_id}-p{page.page_number}",
                provenance=provenance,
                parent_id=parent_id,
                page_start=page.page_number,
                page_end=page.page_number,
                text=line,
            )
            paragraphs.append(node)
            nodes.append(node)

    return ExtractedDocumentStructure(
        document_id=document_id,
        nodes=tuple(nodes),
        paragraphs=tuple(paragraphs),
        headings=tuple(headings),
        captions=tuple(captions),
        equation_labels=tuple(labels),
    )
