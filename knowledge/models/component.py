"""Canonical Component model (injector, chamber, nozzle, turbopump, ...)."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace

__all__ = ("Component",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Component:
    """Engineering component with interfaces, constraints, and source."""

    component_id: str
    name: str
    classification: str
    provenance: ProvenanceTrace
    geometry: str | None = None
    material_ids: tuple[str, ...] = ()
    interface_ids: tuple[str, ...] = ()
    operating_conditions: str | None = None
    requirement_ids: tuple[str, ...] = ()
    constraint_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    failure_mode_ids: tuple[str, ...] = ()
    design_rule_ids: tuple[str, ...] = ()
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    verification_status: str = "UNREVIEWED"

    def __post_init__(self) -> None:
        if not self.component_id.strip() or not self.name.strip():
            raise ValueError("component_id and name are required.")
        if not self.classification.strip():
            raise ValueError("classification is required.")
