"""Process candidate extractor."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.process import Process

__all__ = ("extract_processes",)


def extract_processes(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[Process, ...]:
    if "process" not in text.lower():
        return ()
    return (
        Process(
            process_id="PROC-CAND-000",
            name="Extracted process candidate",
            description=text[:160],
            domain="ENGINEERING",
            provenance=candidate_provenance(document_id, reference_id),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
