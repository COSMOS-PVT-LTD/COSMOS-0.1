"""Failure-mode candidate extractor."""

from __future__ import annotations

from knowledge.extraction.candidate import candidate_provenance
from knowledge.models.failure_mode import FailureMode
from knowledge.models.lifecycle import KnowledgeLifecycle

__all__ = ("extract_failure_modes",)

_MODES = ("thermal fatigue", "cavitation", "combustion instability", "burn-through")


def extract_failure_modes(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[FailureMode, ...]:
    lowered = text.lower()
    items: list[FailureMode] = []
    for index, name in enumerate(_MODES):
        if name not in lowered:
            continue
        items.append(
            FailureMode(
                failure_mode_id=f"FM-CAND-{index:03d}",
                name=name,
                mechanism=name,
                cause="unreviewed",
                effect="unreviewed",
                severity="UNSPECIFIED",
                likelihood="UNSPECIFIED",
                mitigation="unreviewed",
                provenance=candidate_provenance(document_id, reference_id),
                lifecycle=KnowledgeLifecycle.CANDIDATE,
            ),
        )
    return tuple(items)
