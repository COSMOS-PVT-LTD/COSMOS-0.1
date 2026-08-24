"""Canonical engineering Correlation model (Bartz, Dittus-Boelter, etc.)."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.engineering_relation import EngineeringRelation, EngineeringRelationKind
from knowledge.models.lifecycle import (
    KnowledgeLifecycle,
    ProvenanceTrace,
    UncertaintyRecord,
    VersionRecord,
)

__all__ = ("Correlation",)


@dataclass(frozen=True, slots=True, kw_only=True)
class Correlation:
    """Empirical/semi-empirical heat-transfer or fluid correlation."""

    correlation_id: str
    name: str
    equation: str
    variables: tuple[str, ...]
    dimensionless_groups: tuple[str, ...]
    applicable_fluid: str | None = None
    geometry: str | None = None
    reynolds_range: tuple[float, float] | None = None
    prandtl_range: tuple[float, float] | None = None
    temperature_range_k: tuple[float, float] | None = None
    pressure_range_pa: tuple[float, float] | None = None
    uncertainty: UncertaintyRecord | None = None
    accuracy: str | None = None
    assumptions: tuple[str, ...] = ()
    source_page: int | None = None
    provenance: ProvenanceTrace | None = None
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.CANDIDATE
    version: VersionRecord | None = None
    validation_status: str = "UNREVIEWED"
    domain: str = "HEAT_TRANSFER"

    def __post_init__(self) -> None:
        if not self.correlation_id.strip() or not self.name.strip():
            raise ValueError("correlation_id and name are required.")
        if not self.equation.strip():
            raise ValueError("equation is required.")
        if self.provenance is None:
            raise ValueError("provenance is required.")
        for bound in (
            self.reynolds_range,
            self.prandtl_range,
            self.temperature_range_k,
            self.pressure_range_pa,
        ):
            if bound is not None and bound[0] > bound[1]:
                raise ValueError("range bounds must be ordered low ≤ high.")

    def as_relation(self) -> EngineeringRelation:
        assert self.provenance is not None
        return EngineeringRelation(
            relation_id=self.correlation_id,
            name=self.name,
            kind=EngineeringRelationKind.CORRELATION,
            statement=self.equation,
            domain=self.domain,
            provenance=self.provenance,
            lifecycle=self.lifecycle,
            version=self.version,
            uncertainty=self.uncertainty,
            assumptions=self.assumptions,
            variable_ids=self.variables,
            applicability=self.geometry,
        )
