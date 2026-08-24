"""Manufacturing-process candidate extractor."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.manufacturing_process import ManufacturingProcess

__all__ = ("extract_manufacturing_processes",)


def extract_manufacturing_processes(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[ManufacturingProcess, ...]:
    if "manufactur" not in text.lower() and "weld" not in text.lower():
        return ()
    return (
        ManufacturingProcess(
            process_id="MFG-CAND-000",
            name="Extracted manufacturing process",
            description=text[:160],
            material_ids=(),
            provenance=candidate_provenance(document_id, reference_id),
            lifecycle=KnowledgeLifecycle.CANDIDATE,
        ),
    )
