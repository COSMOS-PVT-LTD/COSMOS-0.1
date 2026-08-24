"""Typed repository facades over KnowledgeRepository."""

from __future__ import annotations

from knowledge.repositories.assumption_repository import AssumptionRepository
from knowledge.repositories.boundary_condition_repository import BoundaryConditionRepository
from knowledge.repositories.chapter_repository import ChapterRepository
from knowledge.repositories.component_repository import ComponentRepository
from knowledge.repositories.constant_repository import ConstantRepository
from knowledge.repositories.correlation_repository import CorrelationRepository
from knowledge.repositories.design_rule_repository import DesignRuleRepository
from knowledge.repositories.document_repository import DocumentRepository
from knowledge.repositories.empirical_relation_repository import EmpiricalRelationRepository
from knowledge.repositories.equation_repository import EquationRepository
from knowledge.repositories.experiment_repository import ExperimentRepository
from knowledge.repositories.failure_mode_repository import FailureModeRepository
from knowledge.repositories.figure_repository import FigureRepository
from knowledge.repositories.manufacturing_process_repository import ManufacturingProcessRepository
from knowledge.repositories.material_repository import MaterialRepository
from knowledge.repositories.physical_law_repository import PhysicalLawRepository
from knowledge.repositories.process_repository import ProcessRepository
from knowledge.repositories.property_repository import PropertyRepository
from knowledge.repositories.reference_repository import ReferenceRepository
from knowledge.repositories.section_repository import SectionRepository
from knowledge.repositories.simulation_repository import SimulationRepository
from knowledge.repositories.subsystem_repository import SubsystemRepository
from knowledge.repositories.table_repository import TableRepository
from knowledge.repositories.variable_repository import VariableRepository

__all__ = (
    "AssumptionRepository",
    "BoundaryConditionRepository",
    "ChapterRepository",
    "ComponentRepository",
    "ConstantRepository",
    "CorrelationRepository",
    "DesignRuleRepository",
    "DocumentRepository",
    "EmpiricalRelationRepository",
    "EquationRepository",
    "ExperimentRepository",
    "FailureModeRepository",
    "FigureRepository",
    "ManufacturingProcessRepository",
    "MaterialRepository",
    "PhysicalLawRepository",
    "ProcessRepository",
    "PropertyRepository",
    "ReferenceRepository",
    "SectionRepository",
    "SimulationRepository",
    "SubsystemRepository",
    "TableRepository",
    "VariableRepository",
)
