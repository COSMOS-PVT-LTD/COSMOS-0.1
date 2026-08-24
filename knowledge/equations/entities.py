"""Engineering entity candidates from recovered source text only."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("EntityCandidate", "extract_entity_candidates")


@dataclass(frozen=True, slots=True, kw_only=True)
class EntityCandidate:
    candidate_id: str
    kind: str
    statement: str
    document_id: str
    page_number: int | None
    provenance: ProvenanceTrace
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE


def extract_entity_candidates(
    pages: tuple[tuple[int, str], ...],
    *,
    document_id: str,
    reference_id: str,
) -> tuple[EntityCandidate, ...]:
    found: list[EntityCandidate] = []
    counter = 0
    for page_number, text in pages:
        for line in text.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            kind = _kind(cleaned)
            if kind is None:
                continue
            counter += 1
            found.append(
                EntityCandidate(
                    candidate_id=f"{document_id}-ent-{counter:03d}",
                    kind=kind,
                    statement=cleaned,
                    document_id=document_id,
                    page_number=page_number,
                    provenance=ProvenanceTrace(
                        source_reference_id=reference_id,
                        document_id=document_id,
                        page=page_number,
                        extraction_method="pdf-entity-candidate",
                    ),
                ),
            )
    return tuple(found)


def _kind(line: str) -> str | None:
    lowered = line.lower()
    if lowered.startswith("assumption"):
        return "Assumption"
    if lowered.startswith("valid for"):
        return "Applicability"
    if "bibliographic identity" in lowered:
        return "BibliographicMention"
    if lowered.startswith("figure"):
        return "Figure"
    if lowered.startswith("table"):
        return "Table"
    return None
