"""Engineering query interface — physics and AI use this, not internal stores."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.models.boundary_condition import BoundaryCondition
from knowledge.models.correlation import Correlation
from knowledge.models.design_rule import DesignRule
from knowledge.models.equation import Equation, EquationStatus
from knowledge.models.experiment import Experiment
from knowledge.models.failure_mode import FailureMode
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.models.physical_law import PhysicalLaw
from knowledge.models.property import PropertyValue
from knowledge.models.simulation import Simulation
from knowledge.repositories.boundary_condition_repository import BoundaryConditionRepository
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repositories.design_rule_repository import DesignRuleRepository
from knowledge.repositories.document_repository import DocumentRepository
from knowledge.repositories.equation_repository import EquationRepository
from knowledge.repositories.experiment_repository import ExperimentRepository
from knowledge.repositories.failure_mode_repository import FailureModeRepository
from knowledge.repositories.physical_law_repository import PhysicalLawRepository
from knowledge.repositories.property_repository import PropertyRepository
from knowledge.repositories.reference_repository import ReferenceRepository
from knowledge.repositories.simulation_repository import SimulationRepository

__all__ = ("EngineeringQueryService", "MaterialCard", "QueryConstraints", "SourceHit")


@dataclass(frozen=True, slots=True, kw_only=True)
class QueryConstraints:
    domain: str | None = None
    require_approved: bool = True
    temperature_k: float | None = None
    pressure_pa: float | None = None
    fluid: str | None = None
    material: str | None = None
    geometry: str | None = None
    reynolds_number: float | None = None
    mach_number: float | None = None
    source_authority: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class MaterialCard:
    """Lightweight material identity used by the engineering query surface."""

    material_id: str
    name: str
    aliases: tuple[str, ...]
    classification: str
    lifecycle: KnowledgeLifecycle
    source_reference_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceHit:
    """Controlled source/reference lookup result."""

    source_id: str
    source_type: str
    title: str
    status: str


def _source_match(needle: str, compact: str, source_id: str, title: str) -> bool:
    haystack = f"{source_id} {title}".lower()
    compact_haystack = "".join(ch for ch in haystack if ch.isalnum())
    return needle in haystack or (bool(compact) and compact in compact_haystack)


class EngineeringQueryService:
    """Controlled query surface. Unapproved knowledge cannot outrank approved."""

    def __init__(
        self,
        *,
        equations: EquationRepository,
        correlations: CorrelationRepository,
        design_rules: DesignRuleRepository,
        laws: tuple[PhysicalLaw, ...] = (),
        physical_laws: PhysicalLawRepository | None = None,
        properties: PropertyRepository | None = None,
        materials: tuple[MaterialCard, ...] = (),
        boundary_conditions: BoundaryConditionRepository | None = None,
        failure_modes: FailureModeRepository | None = None,
        experiments: ExperimentRepository | None = None,
        simulations: SimulationRepository | None = None,
        references: ReferenceRepository | None = None,
        documents: DocumentRepository | None = None,
    ) -> None:
        self._equations = equations
        self._correlations = correlations
        self._design_rules = design_rules
        self._laws = laws
        self._physical_laws = physical_laws
        self._properties = properties
        self._materials = materials
        self._boundary_conditions = boundary_conditions
        self._failure_modes = failure_modes
        self._experiments = experiments
        self._simulations = simulations
        self._references = references
        self._documents = documents

    def find_equation(self, query: str, constraints: QueryConstraints | None = None) -> tuple[Equation, ...]:
        constraints = constraints or QueryConstraints()
        needle = query.lower()
        hits = [
            equation
            for equation in self._equations.query()
            if needle in equation.equation_name.lower() or needle in equation.expression.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.status is EquationStatus.APPROVED]
        if constraints.domain:
            hits = [item for item in hits if item.equation_category.value == constraints.domain]
        return tuple(sorted(hits, key=lambda item: item.equation_id))

    def find_correlation(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[Correlation, ...]:
        constraints = constraints or QueryConstraints()
        needle = query.lower()
        hits = [
            item
            for item in self._correlations.query()
            if needle in item.name.lower() or needle in item.equation.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        if constraints.domain:
            hits = [item for item in hits if item.domain.upper() == constraints.domain.upper()]
        if constraints.fluid:
            fluid = constraints.fluid.lower()
            hits = [
                item
                for item in hits
                if item.applicable_fluid is not None and fluid in item.applicable_fluid.lower()
            ]
        if constraints.geometry:
            geometry = constraints.geometry.lower()
            hits = [item for item in hits if item.geometry is not None and geometry in item.geometry.lower()]
        if constraints.reynolds_number is not None:
            hits = [
                item
                for item in hits
                if item.reynolds_range is not None
                and item.reynolds_range[0] <= constraints.reynolds_number <= item.reynolds_range[1]
            ]
        return tuple(sorted(hits, key=lambda item: item.correlation_id))

    def find_design_rule(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[DesignRule, ...]:
        constraints = constraints or QueryConstraints()
        needle = query.lower()
        hits = [item for item in self._design_rules.query() if needle in item.statement.lower()]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        return tuple(sorted(hits, key=lambda item: item.rule_id))

    def find_physical_law(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[PhysicalLaw, ...]:
        needle = query.lower()
        catalog = list(self._laws)
        if self._physical_laws is not None:
            catalog.extend(self._physical_laws.query())
        seen: set[str] = set()
        unique: list[PhysicalLaw] = []
        for item in catalog:
            if item.law_id in seen:
                continue
            seen.add(item.law_id)
            unique.append(item)
        hits = [item for item in unique if needle in item.name.lower() or needle in item.mathematical_formulation.lower()]
        if constraints is not None and constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        if constraints is not None and constraints.domain:
            hits = [item for item in hits if item.domain.upper() == constraints.domain.upper()]
        return tuple(sorted(hits, key=lambda item: item.law_id))

    def find_material(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[MaterialCard, ...]:
        constraints = constraints or QueryConstraints()
        needle = query.lower()
        hits = [
            item
            for item in self._materials
            if needle in item.name.lower()
            or needle in item.material_id.lower()
            or any(needle == alias.lower() for alias in item.aliases)
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        if constraints.material:
            material = constraints.material.lower()
            hits = [item for item in hits if material in item.name.lower() or material in item.material_id.lower()]
        return tuple(sorted(hits, key=lambda item: item.material_id))

    def find_property(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[PropertyValue, ...]:
        constraints = constraints or QueryConstraints()
        if self._properties is None:
            return ()
        needle = query.lower()
        definition_ids = {
            item.property_id
            for item in self._properties.definitions.query()
            if needle in item.property_id.lower() or needle in item.name.lower() or needle in item.symbol.lower()
        }
        hits = [
            item
            for item in self._properties.values.query()
            if needle in item.property_id.lower()
            or needle in item.value_id.lower()
            or item.property_id in definition_ids
            or (item.material_id is not None and needle in item.material_id.lower())
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        if constraints.material:
            material = constraints.material.lower()
            hits = [
                item
                for item in hits
                if item.material_id is not None and material in item.material_id.lower()
            ]
        if constraints.temperature_k is not None:
            hits = [
                item
                for item in hits
                if item.temperature_k is None or abs(item.temperature_k - constraints.temperature_k) <= 5.0
            ]
        if constraints.pressure_pa is not None:
            hits = [
                item
                for item in hits
                if item.pressure_pa is None or abs(item.pressure_pa - constraints.pressure_pa) <= 1.0e4
            ]
        return tuple(sorted(hits, key=lambda item: item.value_id))

    def find_boundary_condition(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[BoundaryCondition, ...]:
        constraints = constraints or QueryConstraints()
        if self._boundary_conditions is None:
            return ()
        needle = query.lower()
        hits = [
            item
            for item in self._boundary_conditions.query()
            if needle in item.name.lower() or needle in item.quantity.lower() or needle in item.geometry_location.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        return tuple(sorted(hits, key=lambda item: item.boundary_condition_id))

    def find_failure_mode(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[FailureMode, ...]:
        constraints = constraints or QueryConstraints()
        if self._failure_modes is None:
            return ()
        needle = query.lower()
        hits = [
            item
            for item in self._failure_modes.query()
            if needle in item.name.lower() or needle in item.mechanism.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        return tuple(sorted(hits, key=lambda item: item.failure_mode_id))

    def find_experiment(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[Experiment, ...]:
        constraints = constraints or QueryConstraints()
        if self._experiments is None:
            return ()
        needle = query.lower()
        hits = [
            item
            for item in self._experiments.query()
            if needle in item.objective.lower() or needle in item.experiment_id.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        return tuple(sorted(hits, key=lambda item: item.experiment_id))

    def find_simulation(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[Simulation, ...]:
        constraints = constraints or QueryConstraints()
        if self._simulations is None:
            return ()
        needle = query.lower()
        hits = [
            item
            for item in self._simulations.query()
            if needle in item.solver.lower()
            or needle in item.physics_model.lower()
            or needle in item.simulation_id.lower()
        ]
        if constraints.require_approved:
            hits = [item for item in hits if item.lifecycle is KnowledgeLifecycle.APPROVED]
        return tuple(sorted(hits, key=lambda item: item.simulation_id))

    def find_source(
        self,
        query: str,
        constraints: QueryConstraints | None = None,
    ) -> tuple[SourceHit, ...]:
        constraints = constraints or QueryConstraints()
        needle = query.lower()
        compact = "".join(ch for ch in needle if ch.isalnum())
        hits: list[SourceHit] = []
        if self._references is not None:
            for reference in self._references.query():
                if not _source_match(needle, compact, reference.reference_id, reference.title):
                    continue
                if constraints.require_approved and reference.status.value != "APPROVED":
                    continue
                hits.append(
                    SourceHit(
                        source_id=reference.reference_id,
                        source_type="Reference",
                        title=reference.title,
                        status=reference.status.value,
                    ),
                )
        if self._documents is not None:
            for document in self._documents.query():
                if not _source_match(needle, compact, document.document_id, document.title):
                    continue
                if constraints.require_approved and document.approval_status.value != "APPROVED":
                    continue
                hits.append(
                    SourceHit(
                        source_id=document.document_id,
                        source_type="Document",
                        title=document.title,
                        status=document.approval_status.value,
                    ),
                )
        if constraints.source_authority:
            authority = constraints.source_authority.lower()
            hits = [item for item in hits if authority in item.source_id.lower() or authority in item.title.lower()]
        return tuple(sorted(hits, key=lambda item: (item.source_type, item.source_id)))
