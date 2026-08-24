"""Canonical Process model."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("Process",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Process:
    """Engineering or operational process."""

    process_id: str
    name: str
    description: str
    domain: str
    provenance: ProvenanceTrace
    input_ids: tuple[str, ...] = ()
    output_ids: tuple[str, ...] = ()
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE

    def __post_init__(self) -> None:
        if not self.process_id.strip() or not self.name.strip():
            raise ValueError("process_id and name are required.")
