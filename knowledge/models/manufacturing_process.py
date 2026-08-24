"""Canonical ManufacturingProcess model."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace, VerificationRecord

__all__ = ("ManufacturingProcess",)


@dataclass(frozen=True, slots=True, kw_only=True)
class ManufacturingProcess:
    """Manufacturing process with material, equipment, and inspection bindings."""

    process_id: str
    name: str
    description: str
    material_ids: tuple[str, ...]
    provenance: ProvenanceTrace
    constraints: tuple[str, ...] = ()
    equipment: str | None = None
    parameters: tuple[str, ...] = ()
    tolerances: str | None = None
    surface_condition: str | None = None
    post_processing: str | None = None
    inspection: str | None = None
    defects: tuple[str, ...] = ()
    applicability: str | None = None
    verification: VerificationRecord | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE

    def __post_init__(self) -> None:
        if not self.process_id.strip() or not self.name.strip():
            raise ValueError("process_id and name are required.")
        if self.lifecycle is KnowledgeLifecycle.APPROVED and self.applicability is None:
            raise ValueError("APPROVED manufacturing processes require applicability.")
