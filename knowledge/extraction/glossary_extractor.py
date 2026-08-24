"""Glossary candidate extractor — maps definitional headings to structure nodes."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.document_structure import DocumentStructureNode, StructureKind

__all__ = ("extract_glossary_nodes",)


def extract_glossary_nodes(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[DocumentStructureNode, ...]:
    if "glossary" not in text.lower():
        return ()
    return (
        DocumentStructureNode(
            node_id="GLOSS-CAND-000",
            document_id=document_id,
            kind=StructureKind.GLOSSARY,
            title="Glossary",
            parsed_artifact_id="w3-unresolved",
            provenance=candidate_provenance(document_id, reference_id),
            text=text[:200],
        ),
    )
