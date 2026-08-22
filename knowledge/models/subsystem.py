"""
knowledge.models.subsystem
==========================

Enterprise immutable engineering subsystem model used by the
COSMOS Knowledge Foundation.

Purpose
-------
Defines the canonical engineering Subsystem entity used to
organize all engineering knowledge throughout COSMOS.

A Subsystem represents an engineering decomposition node within
a larger aerospace system. Every Variable, Equation, Constant,
Unit, Dimension, Simulation, Material, Component, Requirement,
Verification activity, Optimization study, CAD model, CFD model,
and Digital Twin artifact may be associated with one or more
Subsystems.

Examples
--------
Vehicle
    ├── Propulsion
    │      ├── Feed System
    │      ├── Injector
    │      ├── Combustion Chamber
    │      ├── Cooling System
    │      ├── Nozzle
    │      └── Ignition
    │
    ├── Structures
    ├── Thermal Control
    ├── Avionics
    ├── Guidance Navigation & Control
    ├── Electrical Power
    ├── Ground Support Equipment
    └── Manufacturing

Design Goals
------------
* Immutable
* Thread-safe
* Fully typed
* Fully validated
* Repository-ready
* Deterministic
* AI-ready
* Knowledge-graph ready
* Digital engineering compatible
* Digital twin compatible
* Enterprise lifecycle managed

This module intentionally contains no numerical simulation,
physics calculations, optimization algorithms, or engineering
analysis.
"""

from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Final

from knowledge.models.document import Document
from knowledge.models.reference import Reference
from knowledge.models.variable import EngineeringDomain


# ============================================================
# Enumerations
# ============================================================


class SubsystemCategory(Enum):
    """
    High-level engineering subsystem classification.
    """

    PROPULSION = "PROPULSION"

    STRUCTURES = "STRUCTURES"

    THERMAL = "THERMAL"

    FLUIDS = "FLUIDS"

    AVIONICS = "AVIONICS"

    GUIDANCE = "GUIDANCE"

    NAVIGATION = "NAVIGATION"

    CONTROL = "CONTROL"

    POWER = "POWER"

    ELECTRICAL = "ELECTRICAL"

    SOFTWARE = "SOFTWARE"

    COMMUNICATION = "COMMUNICATION"

    PAYLOAD = "PAYLOAD"

    GROUND_SUPPORT = "GROUND_SUPPORT"

    MANUFACTURING = "MANUFACTURING"

    TEST = "TEST"

    SAFETY = "SAFETY"

    RELIABILITY = "RELIABILITY"

    OPERATIONS = "OPERATIONS"

    SYSTEM = "SYSTEM"

    OTHER = "OTHER"


class SubsystemStatus(Enum):
    """
    Engineering lifecycle status.
    """

    DRAFT = "DRAFT"

    PROPOSED = "PROPOSED"

    UNDER_DEVELOPMENT = "UNDER_DEVELOPMENT"

    VERIFIED = "VERIFIED"

    VALIDATED = "VALIDATED"

    QUALIFIED = "QUALIFIED"

    CERTIFIED = "CERTIFIED"

    RELEASED = "RELEASED"

    ACTIVE = "ACTIVE"

    DEPRECATED = "DEPRECATED"

    ARCHIVED = "ARCHIVED"


class SystemLevel(Enum):
    """
    Position of a subsystem within the engineering hierarchy.
    """

    ENTERPRISE = "ENTERPRISE"

    VEHICLE = "VEHICLE"

    STAGE = "STAGE"

    SYSTEM = "SYSTEM"

    SUBSYSTEM = "SUBSYSTEM"

    ASSEMBLY = "ASSEMBLY"

    COMPONENT = "COMPONENT"

    SUBCOMPONENT = "SUBCOMPONENT"

    PART = "PART"


class CriticalityLevel(Enum):
    """
    Engineering criticality classification.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    MISSION_CRITICAL = "MISSION_CRITICAL"

    SAFETY_CRITICAL = "SAFETY_CRITICAL"


class TechnologyReadinessLevel(Enum):
    """
    Technology Readiness Level (TRL).

    Based on the NASA TRL scale.
    """

    TRL1 = 1

    TRL2 = 2

    TRL3 = 3

    TRL4 = 4

    TRL5 = 5

    TRL6 = 6

    TRL7 = 7

    TRL8 = 8

    TRL9 = 9


# ============================================================
# Module Constants
# ============================================================

CURRENT_SUBSYSTEM_MODEL_VERSION: Final[str] = "1.0"

MAX_SUBSYSTEM_NAME_LENGTH: Final[int] = 256

MAX_DESCRIPTION_LENGTH: Final[int] = 10000

MAX_ALIAS_COUNT: Final[int] = 256

MAX_KEYWORD_COUNT: Final[int] = 512

# ============================================================
# Subsystem Model
# ============================================================


@dataclass(
    frozen=True,
    slots=True,
)
class Subsystem:
    """
    Enterprise engineering subsystem.

    A Subsystem represents an engineering node within the
    COSMOS engineering hierarchy.

    All engineering knowledge objects may reference one or
    more Subsystems.
    """

    # ========================================================
    # Identity
    # ========================================================

    subsystem_id: str

    name: str

    short_name: str

    symbol: str

    description: str

    # ========================================================
    # Classification
    # ========================================================

    category: SubsystemCategory

    status: SubsystemStatus

    engineering_domain: EngineeringDomain

    system_level: SystemLevel

    criticality: CriticalityLevel

    technology_readiness_level: TechnologyReadinessLevel

    # ========================================================
    # Hierarchy
    # ========================================================

    parent_subsystem_id: str | None

    child_subsystem_ids: tuple[str, ...]

    hierarchy_path: tuple[str, ...]

    hierarchy_depth: int

    # ========================================================
    # Engineering Metadata
    # ========================================================

    engineering_disciplines: tuple[str, ...]

    supported_physics: tuple[str, ...]

    applicable_regimes: tuple[str, ...]

    interfaces: tuple[str, ...]

    design_constraints: tuple[str, ...]

    requirements: tuple[str, ...]

    # ========================================================
    # Knowledge Metadata
    # ========================================================

    aliases: tuple[str, ...]

    common_names: tuple[str, ...]

    search_keywords: tuple[str, ...]

    tags: tuple[str, ...]

    # ========================================================
    # Relationships
    # ========================================================

    related_variable_ids: tuple[str, ...]

    related_equation_ids: tuple[str, ...]

    related_constant_ids: tuple[str, ...]

    related_unit_ids: tuple[str, ...]

    related_dimension_ids: tuple[str, ...]

    related_material_ids: tuple[str, ...]

    related_component_ids: tuple[str, ...]

    related_simulation_ids: tuple[str, ...]

    # ========================================================
    # Documentation
    # ========================================================

    source_reference: Reference | None

    source_document: Document | None

    # ========================================================
    # Repository Metadata
    # ========================================================

    version: str

    status_note: str

    created_timestamp: datetime | None

    modified_timestamp: datetime | None

    approved_timestamp: datetime | None

    created_by: str

    approved_by: str | None

    revision: int

    # ========================================================
    # Future Knowledge Graph
    # ========================================================

    ontology_uri: str | None

    graph_node_id: str | None

    symbolic_identifier: str | None

    embedding_identifier: str | None

    export_identifier: str | None

    llm_summary: str | None

    # ========================================================
    # Engineering Ownership
    # ========================================================

    responsible_team: str | None

    responsible_engineer: str | None

    owning_organization: str | None

    project_name: str | None

    program_name: str | None

    # ========================================================
    # Verification & Validation
    # ========================================================

    verification_status: str | None

    validation_status: str | None

    verification_method: str | None

    verification_document_ids: tuple[str, ...]

    test_case_ids: tuple[str, ...]

    # ========================================================
    # Safety & Reliability
    # ========================================================

    safety_classification: str | None

    reliability_target: float | None

    failure_mode_ids: tuple[str, ...]

    hazard_ids: tuple[str, ...]

    risk_ids: tuple[str, ...]

    # ========================================================
    # Digital Engineering Metadata
    # ========================================================

    cad_model_ids: tuple[str, ...]

    cfd_model_ids: tuple[str, ...]

    fem_model_ids: tuple[str, ...]

    optimization_case_ids: tuple[str, ...]

    simulation_case_ids: tuple[str, ...]

    digital_twin_identifier: str | None

    # ========================================================
    # Manufacturing Metadata
    # ========================================================

    manufacturing_processes: tuple[str, ...]

    manufacturing_constraints: tuple[str, ...]

    inspection_requirements: tuple[str, ...]

    supplier_ids: tuple[str, ...]

    # ========================================================
    # Knowledge Foundation Metadata
    # ========================================================

    repository_path: str | None

    repository_identifier: str | None

    knowledge_tags: tuple[str, ...]

    ontology_terms: tuple[str, ...]

    semantic_keywords: tuple[str, ...]

    # ========================================================
    # AI Metadata
    # ========================================================

    ai_summary: str | None

    ai_embedding_identifier: str | None

    ai_vector_database_id: str | None

    llm_context_identifier: str | None

    symbolic_model_identifier: str | None

    # ========================================================
    # Future Extensions
    # ========================================================

    custom_metadata: Mapping[str, str] | None

    extension_fields: Mapping[str, str] | None  

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the Subsystem immediately after
        construction.
        """

        self.validate()

    # ========================================================
    # Public Validation
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the complete Subsystem.

        Validation responsibilities are delegated to
        specialized private validator methods to keep the
        implementation modular, maintainable, and
        enterprise-scale.
        """

        self._validate_identity()

        self._validate_classification()

        self._validate_hierarchy()

        self._validate_engineering_metadata()

        self._validate_relationships()

        self._validate_documentation()

        self._validate_repository_metadata()

        self._validate_digital_engineering()

        self._validate_ai_metadata()

        self._validate_future_metadata()

    # ========================================================
    # Identity Validation
    # ========================================================

    def _validate_identity(self) -> None:
        """Validate identity fields."""

        self._validate_subsystem_id()

        self._validate_name()

        self._validate_short_name()

        self._validate_symbol()

        self._validate_description()

    # ========================================================
    # Classification Validation
    # ========================================================

    def _validate_classification(self) -> None:
        """Validate engineering classification."""

        self._validate_category()

        self._validate_status()

        self._validate_engineering_domain()

        self._validate_system_level()

        self._validate_criticality()

        self._validate_trl()

    # ========================================================
    # Hierarchy Validation
    # ========================================================

    def _validate_hierarchy(self) -> None:
        """Validate subsystem hierarchy."""

        self._validate_parent()

        self._validate_children()

        self._validate_hierarchy_path()

        self._validate_depth()

    # ========================================================
    # Engineering Metadata
    # ========================================================

    def _validate_engineering_metadata(
        self,
    ) -> None:
        """Validate engineering metadata."""

        self._validate_engineering_disciplines()

        self._validate_supported_physics()

        self._validate_interfaces()

        self._validate_constraints()

        self._validate_requirements()

    # ========================================================
    # Relationships
    # ========================================================

    def _validate_relationships(
        self,
    ) -> None:
        """Validate knowledge relationships."""

        self._validate_related_variables()

        self._validate_related_equations()

        self._validate_related_constants()

        self._validate_related_units()

        self._validate_related_dimensions()

        self._validate_related_materials()

        self._validate_related_components()

        self._validate_related_simulations()

    # ========================================================
    # Documentation
    # ========================================================

    def _validate_documentation(
        self,
    ) -> None:
        """Validate documentation."""

        self._validate_reference()

        self._validate_document()

    # ========================================================
    # Repository Metadata
    # ========================================================

    def _validate_repository_metadata(
        self,
    ) -> None:
        """Validate repository metadata."""

        self._validate_version()

        self._validate_revision()

        self._validate_repository_identifiers()

        self._validate_repository_path()

    # ========================================================
    # Digital Engineering
    # ========================================================

    def _validate_digital_engineering(
        self,
    ) -> None:
        """Validate digital engineering metadata."""

        self._validate_cad_models()

        self._validate_cfd_models()

        self._validate_fem_models()

        self._validate_simulation_cases()

        self._validate_optimization_cases()

    # ========================================================
    # AI Metadata
    # ========================================================

    def _validate_ai_metadata(
        self,
    ) -> None:
        """Validate AI metadata."""

        self._validate_ai_identifiers()

        self._validate_embeddings()

        self._validate_llm_metadata()

    # ========================================================
    # Future Metadata
    # ========================================================

    def _validate_future_metadata(
        self,
    ) -> None:
        """Placeholder for future validation."""
        return
    
    # ========================================================
    # Identity Validators
    # ========================================================

    def _validate_subsystem_id(self) -> None:
        """Validate subsystem identifier."""

        if not isinstance(self.subsystem_id, str):
            raise TypeError(
                "subsystem_id must be a string."
            )

        if not self.subsystem_id.strip():
            raise ValueError(
                "subsystem_id cannot be blank."
            )

    def _validate_name(self) -> None:
        """Validate subsystem name."""

        if not isinstance(self.name, str):
            raise TypeError(
                "name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "name cannot be blank."
            )

        if len(self.name) > MAX_SUBSYSTEM_NAME_LENGTH:
            raise ValueError(
                "Subsystem name exceeds the maximum allowed length."
            )

    def _validate_short_name(self) -> None:
        """Validate short name."""

        if not isinstance(self.short_name, str):
            raise TypeError(
                "short_name must be a string."
            )

        if not self.short_name.strip():
            raise ValueError(
                "short_name cannot be blank."
            )

    def _validate_symbol(self) -> None:
        """Validate engineering symbol."""

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

    def _validate_description(self) -> None:
        """Validate description."""

        if not isinstance(self.description, str):
            raise TypeError(
                "description must be a string."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be blank."
            )

        if len(self.description) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                "Description exceeds the maximum allowed length."
            )

    # ========================================================
    # Classification Validators
    # ========================================================

    def _validate_category(self) -> None:
        """Validate subsystem category."""

        if not isinstance(
            self.category,
            SubsystemCategory,
        ):
            raise TypeError(
                "category must be a SubsystemCategory."
            )

    def _validate_status(self) -> None:
        """Validate subsystem status."""

        if not isinstance(
            self.status,
            SubsystemStatus,
        ):
            raise TypeError(
                "status must be a SubsystemStatus."
            )

    def _validate_engineering_domain(self) -> None:
        """Validate engineering domain."""

        if not isinstance(
            self.engineering_domain,
            EngineeringDomain,
        ):
            raise TypeError(
                "engineering_domain must be an EngineeringDomain."
            )

    def _validate_system_level(self) -> None:
        """Validate system level."""

        if not isinstance(
            self.system_level,
            SystemLevel,
        ):
            raise TypeError(
                "system_level must be a SystemLevel."
            )

    def _validate_criticality(self) -> None:
        """Validate criticality."""

        if not isinstance(
            self.criticality,
            CriticalityLevel,
        ):
            raise TypeError(
                "criticality must be a CriticalityLevel."
            )

    def _validate_trl(self) -> None:
        """Validate technology readiness level."""

        if not isinstance(
            self.technology_readiness_level,
            TechnologyReadinessLevel,
        ):
            raise TypeError(
                "technology_readiness_level must be a TechnologyReadinessLevel."
            )

    # ========================================================
    # Hierarchy Validators
    # ========================================================

    def _validate_parent(self) -> None:
        """Validate parent subsystem."""

        if (
            self.parent_subsystem_id is not None
            and not isinstance(
                self.parent_subsystem_id,
                str,
            )
        ):
            raise TypeError(
                "parent_subsystem_id must be a string or None."
            )

    def _validate_children(self) -> None:
        """Validate child subsystem identifiers."""

        if not isinstance(
            self.child_subsystem_ids,
            tuple,
        ):
            raise TypeError(
                "child_subsystem_ids must be a tuple."
            )

        for child in self.child_subsystem_ids:
            if not isinstance(child, str):
                raise TypeError(
                    "Each child subsystem identifier must be a string."
                )

    def _validate_hierarchy_path(self) -> None:
        """Validate hierarchy path."""

        if not isinstance(
            self.hierarchy_path,
            tuple,
        ):
            raise TypeError(
                "hierarchy_path must be a tuple."
            )

        for node in self.hierarchy_path:
            if not isinstance(node, str):
                raise TypeError(
                    "Hierarchy path entries must be strings."
                )

    def _validate_depth(self) -> None:
        """Validate hierarchy depth."""

        if not isinstance(
            self.hierarchy_depth,
            int,
        ):
            raise TypeError(
                "hierarchy_depth must be an integer."
            )

        if self.hierarchy_depth < 0:
            raise ValueError(
                "hierarchy_depth cannot be negative."
            )

    # ========================================================
    # Engineering Metadata Validators
    # ========================================================

    def _validate_engineering_disciplines(self) -> None:
        """Validate engineering disciplines."""

        self._validate_string_tuple(
            self.engineering_disciplines,
            "engineering_disciplines",
        )

    def _validate_supported_physics(self) -> None:
        """Validate supported physics."""

        self._validate_string_tuple(
            self.supported_physics,
            "supported_physics",
        )

    def _validate_interfaces(self) -> None:
        """Validate subsystem interfaces."""

        self._validate_string_tuple(
            self.interfaces,
            "interfaces",
        )

    def _validate_constraints(self) -> None:
        """Validate design constraints."""

        self._validate_string_tuple(
            self.design_constraints,
            "design_constraints",
        )

    def _validate_requirements(self) -> None:
        """Validate engineering requirements."""

        self._validate_string_tuple(
            self.requirements,
            "requirements",
        )

    # ========================================================
    # Relationship Validators
    # ========================================================

    def _validate_related_variables(self) -> None:
        self._validate_string_tuple(
            self.related_variable_ids,
            "related_variable_ids",
        )

    def _validate_related_equations(self) -> None:
        self._validate_string_tuple(
            self.related_equation_ids,
            "related_equation_ids",
        )

    def _validate_related_constants(self) -> None:
        self._validate_string_tuple(
            self.related_constant_ids,
            "related_constant_ids",
        )

    def _validate_related_units(self) -> None:
        self._validate_string_tuple(
            self.related_unit_ids,
            "related_unit_ids",
        )

    def _validate_related_dimensions(self) -> None:
        self._validate_string_tuple(
            self.related_dimension_ids,
            "related_dimension_ids",
        )

    def _validate_related_materials(self) -> None:
        self._validate_string_tuple(
            self.related_material_ids,
            "related_material_ids",
        )

    def _validate_related_components(self) -> None:
        self._validate_string_tuple(
            self.related_component_ids,
            "related_component_ids",
        )

    def _validate_related_simulations(self) -> None:
        self._validate_string_tuple(
            self.related_simulation_ids,
            "related_simulation_ids",
        )

    # ========================================================
    # Documentation Validators
    # ========================================================

    def _validate_reference(self) -> None:
        """Validate source reference."""

        if (
            self.source_reference is not None
            and not isinstance(
                self.source_reference,
                Reference,
            )
        ):
            raise TypeError(
                "source_reference must be a Reference or None."
            )

    def _validate_document(self) -> None:
        """Validate source document."""

        if (
            self.source_document is not None
            and not isinstance(
                self.source_document,
                Document,
            )
        ):
            raise TypeError(
                "source_document must be a Document or None."
            )

    # ========================================================
    # Repository Validators
    # ========================================================

    def _validate_version(self) -> None:
        """Validate version."""

        if not isinstance(self.version, str):
            raise TypeError(
                "version must be a string."
            )

        if not self.version.strip():
            raise ValueError(
                "version cannot be blank."
            )

    def _validate_revision(self) -> None:
        """Validate revision."""

        if not isinstance(self.revision, int):
            raise TypeError(
                "revision must be an integer."
            )

        if self.revision < 0:
            raise ValueError(
                "revision cannot be negative."
            )

    def _validate_repository_identifiers(self) -> None:
        """Validate repository identifier."""

        if (
            self.repository_identifier is not None
            and not isinstance(
                self.repository_identifier,
                str,
            )
        ):
            raise TypeError(
                "repository_identifier must be a string or None."
            )

    def _validate_repository_path(self) -> None:
        """Validate repository path."""

        if (
            self.repository_path is not None
            and not isinstance(
                self.repository_path,
                str,
            )
        ):
            raise TypeError(
                "repository_path must be a string or None."
            )

    # ========================================================
    # Digital Engineering Validators
    # ========================================================

    def _validate_cad_models(self) -> None:
        self._validate_string_tuple(
            self.cad_model_ids,
            "cad_model_ids",
        )

    def _validate_cfd_models(self) -> None:
        self._validate_string_tuple(
            self.cfd_model_ids,
            "cfd_model_ids",
        )

    def _validate_fem_models(self) -> None:
        self._validate_string_tuple(
            self.fem_model_ids,
            "fem_model_ids",
        )

    def _validate_simulation_cases(self) -> None:
        self._validate_string_tuple(
            self.simulation_case_ids,
            "simulation_case_ids",
        )

    def _validate_optimization_cases(self) -> None:
        self._validate_string_tuple(
            self.optimization_case_ids,
            "optimization_case_ids",
        )

    # ========================================================
    # AI Metadata Validators
    # ========================================================

    def _validate_ai_identifiers(self) -> None:
        """Validate AI identifiers."""

        optional_strings = (
            self.ai_embedding_identifier,
            self.ai_vector_database_id,
            self.llm_context_identifier,
            self.symbolic_model_identifier,
        )

        for value in optional_strings:
            if value is not None and not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    "AI identifiers must be strings or None."
                )

    def _validate_embeddings(self) -> None:
        """Reserved for future embedding validation."""
        return

    def _validate_llm_metadata(self) -> None:
        """Validate AI summary."""

        if (
            self.ai_summary is not None
            and not isinstance(
                self.ai_summary,
                str,
            )
        ):
            raise TypeError(
                "ai_summary must be a string or None."
            )

    # ========================================================
    # Shared Validation Helpers
    # ========================================================

    @staticmethod
    def _validate_string_tuple(
        values: tuple[str, ...],
        field_name: str,
    ) -> None:
        """
        Validate a tuple containing strings.
        """

        if not isinstance(values, tuple):
            raise TypeError(
                f"{field_name} must be a tuple."
            )

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    f"Every element of {field_name} must be a string."
                )

    # ========================================================
    # Serialization Helpers
    # ========================================================

    @staticmethod
    def _serialize_datetime(
        value: datetime | None,
    ) -> str | None:
        """
        Serialize a datetime.

        Parameters
        ----------
        value : datetime | None

        Returns
        -------
        str | None
        """

        if value is None:
            return None

        return value.isoformat()

    @staticmethod
    def _deserialize_datetime(
        value: str | None,
    ) -> datetime | None:
        """
        Deserialize a datetime.

        Parameters
        ----------
        value : str | None

        Returns
        -------
        datetime | None
        """

        if value is None:
            return None

        return datetime.fromisoformat(value)

    @staticmethod
    def _serialize_reference(
        reference: Reference | None,
    ) -> dict[str, object] | None:
        """
        Serialize a Reference.
        """

        if reference is None:
            return None

        return reference.to_dict()

    @staticmethod
    def _deserialize_reference(
        data: object,
    ) -> Reference | None:
        """
        Deserialize a Reference.
        """

        if data is None:
            return None

        if not isinstance(data, dict):
            raise TypeError(
                "Reference must be serialized as a dictionary."
            )

        return Reference.from_dict(data)

    @staticmethod
    def _serialize_document(
        document: Document | None,
    ) -> dict[str, object] | None:
        """
        Serialize a Document.
        """

        if document is None:
            return None

        return document.to_dict()

    @staticmethod
    def _deserialize_document(
        data: object,
    ) -> Document | None:
        """
        Deserialize a Document.
        """

        if data is None:
            return None

        if not isinstance(data, dict):
            raise TypeError(
                "Document must be serialized as a dictionary."
            )

        return Document.from_dict(data)

    @staticmethod
    def _serialize_mapping(
        mapping: Mapping[str, str] | None,
    ) -> dict[str, str] | None:
        """
        Serialize immutable metadata mappings.
        """

        if mapping is None:
            return None

        return dict(mapping)

    @staticmethod
    def _deserialize_mapping(
        mapping: object,
    ) -> Mapping[str, str] | None:
        """
        Deserialize metadata mappings.
        """

        if mapping is None:
            return None

        if not isinstance(mapping, dict):
            raise TypeError(
                "Mapping must be serialized as a dictionary."
            )

        return mapping

    # ========================================================
    # Dictionary Serialization
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize this Subsystem into a deterministic dictionary.

        Returns
        -------
        dict[str, object]
        """

        return {

            # ------------------------------------------------
            # Identity
            # ------------------------------------------------

            "subsystem_id": self.subsystem_id,
            "name": self.name,
            "short_name": self.short_name,
            "symbol": self.symbol,
            "description": self.description,

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            "category": self.category.value,
            "status": self.status.value,
            "engineering_domain": self.engineering_domain.value,
            "system_level": self.system_level.value,
            "criticality": self.criticality.value,
            "technology_readiness_level":
                self.technology_readiness_level.value,

            # ------------------------------------------------
            # Hierarchy
            # ------------------------------------------------

            "parent_subsystem_id": self.parent_subsystem_id,
            "child_subsystem_ids": list(
                self.child_subsystem_ids
            ),
            "hierarchy_path": list(
                self.hierarchy_path
            ),
            "hierarchy_depth": self.hierarchy_depth,

            # ------------------------------------------------
            # Engineering Metadata
            # ------------------------------------------------

            "engineering_disciplines": list(
                self.engineering_disciplines
            ),
            "supported_physics": list(
                self.supported_physics
            ),
            "applicable_regimes": list(
                self.applicable_regimes
            ),
            "interfaces": list(
                self.interfaces
            ),
            "design_constraints": list(
                self.design_constraints
            ),
            "requirements": list(
                self.requirements
            ),

            # ------------------------------------------------
            # Knowledge Metadata
            # ------------------------------------------------

            "aliases": list(self.aliases),
            "common_names": list(self.common_names),
            "search_keywords": list(
                self.search_keywords
            ),
            "tags": list(self.tags),

            # ------------------------------------------------
            # Relationships
            # ------------------------------------------------

            "related_variable_ids": list(
                self.related_variable_ids
            ),
            "related_equation_ids": list(
                self.related_equation_ids
            ),
            "related_constant_ids": list(
                self.related_constant_ids
            ),
            "related_unit_ids": list(
                self.related_unit_ids
            ),
            "related_dimension_ids": list(
                self.related_dimension_ids
            ),
            "related_material_ids": list(
                self.related_material_ids
            ),
            "related_component_ids": list(
                self.related_component_ids
            ),
            "related_simulation_ids": list(
                self.related_simulation_ids
            ),

            # ------------------------------------------------
            # Documentation
            # ------------------------------------------------

            "source_reference":
                self._serialize_reference(
                    self.source_reference
                ),

            "source_document":
                self._serialize_document(
                    self.source_document
                ),

            # ------------------------------------------------
            # Repository Metadata
            # ------------------------------------------------

            "version": self.version,
            "status_note": self.status_note,

            "created_timestamp":
                self._serialize_datetime(
                    self.created_timestamp
                ),

            "modified_timestamp":
                self._serialize_datetime(
                    self.modified_timestamp
                ),

            "approved_timestamp":
                self._serialize_datetime(
                    self.approved_timestamp
                ),

            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "revision": self.revision,

            # ------------------------------------------------
            # Future Knowledge Graph
            # ------------------------------------------------

            "ontology_uri": self.ontology_uri,
            "graph_node_id": self.graph_node_id,
            "symbolic_identifier":
                self.symbolic_identifier,
            "embedding_identifier":
                self.embedding_identifier,
            "export_identifier":
                self.export_identifier,
            "llm_summary": self.llm_summary,

            # ------------------------------------------------
            # Engineering Ownership
            # ------------------------------------------------

            "responsible_team":
                self.responsible_team,
            "responsible_engineer":
                self.responsible_engineer,
            "owning_organization":
                self.owning_organization,
            "project_name":
                self.project_name,
            "program_name":
                self.program_name,

            # ------------------------------------------------
            # Verification & Validation
            # ------------------------------------------------

            "verification_status":
                self.verification_status,
            "validation_status":
                self.validation_status,
            "verification_method":
                self.verification_method,

            "verification_document_ids":
                list(
                    self.verification_document_ids
                ),

            "test_case_ids":
                list(
                    self.test_case_ids
                ),

            # ------------------------------------------------
            # Safety & Reliability
            # ------------------------------------------------

            "safety_classification":
                self.safety_classification,

            "reliability_target":
                self.reliability_target,

            "failure_mode_ids":
                list(
                    self.failure_mode_ids
                ),

            "hazard_ids":
                list(
                    self.hazard_ids
                ),

            "risk_ids":
                list(
                    self.risk_ids
                ),

            # ------------------------------------------------
            # Digital Engineering
            # ------------------------------------------------

            "cad_model_ids":
                list(
                    self.cad_model_ids
                ),

            "cfd_model_ids":
                list(
                    self.cfd_model_ids
                ),

            "fem_model_ids":
                list(
                    self.fem_model_ids
                ),

            "optimization_case_ids":
                list(
                    self.optimization_case_ids
                ),

            "simulation_case_ids":
                list(
                    self.simulation_case_ids
                ),

            "digital_twin_identifier":
                self.digital_twin_identifier,

            # ------------------------------------------------
            # Manufacturing
            # ------------------------------------------------

            "manufacturing_processes":
                list(
                    self.manufacturing_processes
                ),

            "manufacturing_constraints":
                list(
                    self.manufacturing_constraints
                ),

            "inspection_requirements":
                list(
                    self.inspection_requirements
                ),

            "supplier_ids":
                list(
                    self.supplier_ids
                ),

            # ------------------------------------------------
            # Knowledge Foundation
            # ------------------------------------------------

            "repository_path":
                self.repository_path,

            "repository_identifier":
                self.repository_identifier,

            "knowledge_tags":
                list(
                    self.knowledge_tags
                ),

            "ontology_terms":
                list(
                    self.ontology_terms
                ),

            "semantic_keywords":
                list(
                    self.semantic_keywords
                ),

            # ------------------------------------------------
            # AI Metadata
            # ------------------------------------------------

            "ai_summary":
                self.ai_summary,

            "ai_embedding_identifier":
                self.ai_embedding_identifier,

            "ai_vector_database_id":
                self.ai_vector_database_id,

            "llm_context_identifier":
                self.llm_context_identifier,

            "symbolic_model_identifier":
                self.symbolic_model_identifier,

            # ------------------------------------------------
            # Extension Metadata
            # ------------------------------------------------

            "custom_metadata":
                self._serialize_mapping(
                    self.custom_metadata
                ),

            "extension_fields":
                self._serialize_mapping(
                    self.extension_fields
                ),
        }

    # ========================================================
    # Dictionary Deserialization
    # ========================================================
    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Subsystem":
        """
            Reconstruct a Subsystem from its serialized
            dictionary representation.
            """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary."
            )

        # ====================================================
        # Nested Objects
        # ====================================================

        source_reference = cls._deserialize_reference(
            data.get("source_reference")
        )

        source_document = cls._deserialize_document(
            data.get("source_document")
        )

        # ====================================================
        # Datetimes
        # ====================================================

        raw_created_timestamp = data.get(
            "created_timestamp"
        )

        if (
            raw_created_timestamp is not None
            and not isinstance(
                raw_created_timestamp,
                str,
            )
        ):
            raise TypeError(
                "created_timestamp must be a string or None."
            )

        created_timestamp = cls._deserialize_datetime(
            raw_created_timestamp
        )

        raw_modified_timestamp = data.get(
            "modified_timestamp"
        )

        if (
            raw_modified_timestamp is not None
            and not isinstance(
                raw_modified_timestamp,
                str,
            )
        ):
            raise TypeError(
                "modified_timestamp must be a string or None."
            )

        modified_timestamp = cls._deserialize_datetime(
            raw_modified_timestamp
        )

        raw_approved_timestamp = data.get(
            "approved_timestamp"
        )

        if (
            raw_approved_timestamp is not None
            and not isinstance(
                raw_approved_timestamp,
                str,
            )
        ):
            raise TypeError(
                "approved_timestamp must be a string or None."
            )

        approved_timestamp = cls._deserialize_datetime(
            raw_approved_timestamp
        )

        # ====================================================
        # Metadata Mappings
        # ====================================================

        custom_metadata = cls._deserialize_mapping(
            data.get(
                "custom_metadata"
            )
        )

        extension_fields = cls._deserialize_mapping(
            data.get(
                "extension_fields"
            )
        )

        # ====================================================
        # Enum Reconstruction
        # ====================================================

        raw_category = data.get(
            "category"
        )

        if not isinstance(
            raw_category,
            str,
        ):
            raise TypeError(
                "category must be a string."
            )

        category = SubsystemCategory(
            raw_category
        )

        raw_status = data.get(
            "status"
        )

        if not isinstance(
            raw_status,
            str,
        ):
            raise TypeError(
                "status must be a string."
            )

        status = SubsystemStatus(
            raw_status
        )

        raw_engineering_domain = data.get(
            "engineering_domain"
        )

        if not isinstance(
            raw_engineering_domain,
            str,
        ):
            raise TypeError(
                "engineering_domain must be a string."
            )

        engineering_domain = (
            EngineeringDomain(
                raw_engineering_domain
            )
        )

        raw_system_level = data.get(
            "system_level"
        )

        if not isinstance(
            raw_system_level,
            str,
        ):
            raise TypeError(
                "system_level must be a string."
            )

        system_level = SystemLevel(
            raw_system_level
        )

        raw_criticality = data.get(
            "criticality"
        )

        if not isinstance(
            raw_criticality,
            str,
        ):
            raise TypeError(
                "criticality must be a string."
            )

        criticality = CriticalityLevel(
            raw_criticality
        )

        raw_trl = data.get(
            "technology_readiness_level"
        )

        if not isinstance(
            raw_trl,
            int,
        ):
            raise TypeError(
                "technology_readiness_level must be an integer."
            )

        technology_readiness_level = (
            TechnologyReadinessLevel(
                raw_trl
            )
        )

        # ====================================================
        # Identity Fields
        # ====================================================

        raw_subsystem_id = data.get(
            "subsystem_id"
        )

        if not isinstance(
            raw_subsystem_id,
            str,
        ):
            raise TypeError(
                "subsystem_id must be a string."
            )

        subsystem_id = raw_subsystem_id

        raw_name = data.get(
            "name"
        )

        if not isinstance(
            raw_name,
            str,
        ):
            raise TypeError(
                "name must be a string."
            )

        name = raw_name

        raw_short_name = data.get(
            "short_name"
        )

        if not isinstance(
            raw_short_name,
            str,
        ):
            raise TypeError(
                "short_name must be a string."
            )

        short_name = raw_short_name

        raw_symbol = data.get(
            "symbol"
        )

        if not isinstance(
            raw_symbol,
            str,
        ):
            raise TypeError(
                "symbol must be a string."
            )

        symbol = raw_symbol

        raw_description = data.get(
            "description"
        )

        if not isinstance(
            raw_description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        description = raw_description

        # ====================================================
        # Hierarchy
        # ====================================================

        raw_parent_subsystem_id = data.get(
            "parent_subsystem_id"
        )

        if raw_parent_subsystem_id is None:
            parent_subsystem_id = None
        elif isinstance(raw_parent_subsystem_id, str):
            parent_subsystem_id = raw_parent_subsystem_id
        else:
            raise TypeError(
                "parent_subsystem_id must be a string or None."
            )

        raw_child_subsystem_ids = data.get(
            "child_subsystem_ids"
        )

        if raw_child_subsystem_ids is None:
            child_subsystem_ids: tuple[str, ...] = ()
        elif isinstance(raw_child_subsystem_ids, (list, tuple)):
            child_subsystem_ids = tuple(
                str(item)
                for item in raw_child_subsystem_ids
            )
        else:
            raise TypeError(
                "child_subsystem_ids must be a list or tuple."
            )

        raw_hierarchy_path = data.get(
            "hierarchy_path"
        )

        if raw_hierarchy_path is None:
            hierarchy_path: tuple[str, ...] = ()
        elif isinstance(raw_hierarchy_path, (list, tuple)):
            hierarchy_path = tuple(
                str(item)
                for item in raw_hierarchy_path
            )
        else:
            raise TypeError(
                "hierarchy_path must be a list or tuple."
            )

        raw_hierarchy_depth = data.get(
            "hierarchy_depth"
        )

        if not isinstance(
            raw_hierarchy_depth,
            int,
        ):
            raise TypeError(
                "hierarchy_depth must be an integer."
            )

        hierarchy_depth = raw_hierarchy_depth

        # ====================================================
        # Engineering Metadata
        # ====================================================

        def _string_tuple(
            field: str,
        ) -> tuple[str, ...]:
            raw = data.get(field)

            if raw is None:
                return ()

            if not isinstance(raw, (list, tuple)):
                raise TypeError(
                    f"{field} must be a list or tuple."
                )

            return tuple(
                str(item)
                for item in raw
            )

        engineering_disciplines = _string_tuple(
            "engineering_disciplines"
        )

        supported_physics = _string_tuple(
            "supported_physics"
        )

        applicable_regimes = _string_tuple(
            "applicable_regimes"
        )

        interfaces = _string_tuple(
            "interfaces"
        )

        design_constraints = _string_tuple(
            "design_constraints"
        )

        requirements = _string_tuple(
            "requirements"
        )

        # ====================================================
        # Knowledge Metadata
        # ====================================================

        aliases = _string_tuple(
            "aliases"
        )

        common_names = _string_tuple(
            "common_names"
        )

        search_keywords = _string_tuple(
            "search_keywords"
        )

        tags = _string_tuple(
            "tags"
        )

        # ====================================================
        # Relationships
        # ====================================================

        related_variable_ids = _string_tuple(
            "related_variable_ids"
        )

        related_equation_ids = _string_tuple(
            "related_equation_ids"
        )

        related_constant_ids = _string_tuple(
            "related_constant_ids"
        )

        related_unit_ids = _string_tuple(
            "related_unit_ids"
        )

        related_dimension_ids = _string_tuple(
            "related_dimension_ids"
        )

        related_material_ids = _string_tuple(
            "related_material_ids"
        )

        related_component_ids = _string_tuple(
            "related_component_ids"
        )

        related_simulation_ids = _string_tuple(
            "related_simulation_ids"
        )

        # ====================================================
        # Repository Metadata
        # ====================================================

        def _optional_string(field: str) -> str | None:
            raw = data.get(field)

            if raw is None:
                return None

            if not isinstance(raw, str):
                raise TypeError(
                    f"{field} must be a string or None."
                )

            return raw

        def _optional_float(field: str) -> float | None:
            raw = data.get(field)

            if raw is None:
                return None

            if isinstance(raw, (int, float)):
                return float(raw)

            raise TypeError(
                f"{field} must be numeric or None."
            )

        raw_version = data.get("version")
        if not isinstance(raw_version, str):
            raise TypeError("version must be a string.")
        version = raw_version

        raw_status_note = data.get("status_note")
        if not isinstance(raw_status_note, str):
            raise TypeError("status_note must be a string.")
        status_note = raw_status_note

        raw_created_by = data.get("created_by")
        if not isinstance(raw_created_by, str):
            raise TypeError("created_by must be a string.")
        created_by = raw_created_by

        raw_revision = data.get("revision")
        if not isinstance(raw_revision, int):
            raise TypeError("revision must be an integer.")
        revision = raw_revision

        approved_by = _optional_string(
            "approved_by"
        )

        # ====================================================
        # Knowledge Graph Metadata
        # ====================================================

        ontology_uri = _optional_string(
            "ontology_uri"
        )

        graph_node_id = _optional_string(
            "graph_node_id"
        )

        symbolic_identifier = _optional_string(
            "symbolic_identifier"
        )

        embedding_identifier = _optional_string(
            "embedding_identifier"
        )

        export_identifier = _optional_string(
            "export_identifier"
        )

        llm_summary = _optional_string(
            "llm_summary"
        )

        # ====================================================
        # Ownership
        # ====================================================

        responsible_team = _optional_string(
            "responsible_team"
        )

        responsible_engineer = _optional_string(
            "responsible_engineer"
        )

        owning_organization = _optional_string(
            "owning_organization"
        )

        project_name = _optional_string(
            "project_name"
        )

        program_name = _optional_string(
            "program_name"
        )

        # ====================================================
        # Verification & Validation
        # ====================================================

        verification_status = _optional_string(
            "verification_status"
        )

        validation_status = _optional_string(
            "validation_status"
        )

        verification_method = _optional_string(
            "verification_method"
        )

        verification_document_ids = _string_tuple(
            "verification_document_ids"
        )

        test_case_ids = _string_tuple(
            "test_case_ids"
        )

        # ====================================================
        # Safety & Reliability
        # ====================================================

        safety_classification = _optional_string(
            "safety_classification"
        )

        reliability_target = _optional_float(
            "reliability_target"
        )

        failure_mode_ids = _string_tuple(
            "failure_mode_ids"
        )

        hazard_ids = _string_tuple(
            "hazard_ids"
        )

        risk_ids = _string_tuple(
            "risk_ids"
        )

        # ====================================================
        # Digital Engineering
        # ====================================================

        cad_model_ids = _string_tuple(
            "cad_model_ids"
        )

        cfd_model_ids = _string_tuple(
            "cfd_model_ids"
        )

        fem_model_ids = _string_tuple(
            "fem_model_ids"
        )

        optimization_case_ids = _string_tuple(
            "optimization_case_ids"
        )

        simulation_case_ids = _string_tuple(
            "simulation_case_ids"
        )

        digital_twin_identifier = _optional_string(
            "digital_twin_identifier"
        )

        # ====================================================
        # Manufacturing
        # ====================================================

        manufacturing_processes = _string_tuple(
            "manufacturing_processes"
        )

        manufacturing_constraints = _string_tuple(
            "manufacturing_constraints"
        )

        inspection_requirements = _string_tuple(
            "inspection_requirements"
        )

        supplier_ids = _string_tuple(
            "supplier_ids"
        )

        # ====================================================
        # Knowledge Foundation
        # ====================================================

        repository_path = _optional_string(
            "repository_path"
        )

        repository_identifier = _optional_string(
            "repository_identifier"
        )

        knowledge_tags = _string_tuple(
            "knowledge_tags"
        )

        ontology_terms = _string_tuple(
            "ontology_terms"
        )

        semantic_keywords = _string_tuple(
            "semantic_keywords"
        )

        # ====================================================
        # AI Metadata
        # ====================================================

        ai_summary = _optional_string(
            "ai_summary"
        )

        ai_embedding_identifier = _optional_string(
            "ai_embedding_identifier"
        )

        ai_vector_database_id = _optional_string(
            "ai_vector_database_id"
        )

        llm_context_identifier = _optional_string(
            "llm_context_identifier"
        )

        symbolic_model_identifier = _optional_string(
            "symbolic_model_identifier"
        )

        return cls(

            # ------------------------------------------------
            # Identity
            # ------------------------------------------------

            subsystem_id=subsystem_id,

            name=name,

            short_name=short_name,

            symbol=symbol,

            description=description,

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            category=category,

            status=status,

            engineering_domain=engineering_domain,

            system_level=system_level,

            criticality=criticality,

            technology_readiness_level=(
                technology_readiness_level
            ),

            # ------------------------------------------------
            # Hierarchy
            # ------------------------------------------------

            parent_subsystem_id=parent_subsystem_id,

            child_subsystem_ids=child_subsystem_ids,

            hierarchy_path=hierarchy_path,

            hierarchy_depth=hierarchy_depth,

            # ------------------------------------------------
            # Engineering Metadata
            # ------------------------------------------------

            engineering_disciplines=(
                engineering_disciplines
            ),

            supported_physics=(
                supported_physics
            ),

            applicable_regimes=(
                applicable_regimes
            ),

            interfaces=interfaces,

            design_constraints=(
                design_constraints
            ),

            requirements=requirements,

            # ------------------------------------------------
            # Knowledge Metadata
            # ------------------------------------------------

            aliases=aliases,

            common_names=common_names,

            search_keywords=search_keywords,

            tags=tags,

            # ------------------------------------------------
            # Relationships
            # ------------------------------------------------

            related_variable_ids=(
                related_variable_ids
            ),

            related_equation_ids=(
                related_equation_ids
            ),

            related_constant_ids=(
                related_constant_ids
            ),

            related_unit_ids=(
                related_unit_ids
            ),

            related_dimension_ids=(
                related_dimension_ids
            ),

            related_material_ids=(
                related_material_ids
            ),

            related_component_ids=(
                related_component_ids
            ),

            related_simulation_ids=(
                related_simulation_ids
            ),

            # ------------------------------------------------
            # Documentation
            # ------------------------------------------------

            source_reference=source_reference,

            source_document=source_document,

            # ------------------------------------------------
            # Repository Metadata
            # ------------------------------------------------

            version=version,

            status_note=status_note,

            created_timestamp=(
                created_timestamp
            ),

            modified_timestamp=(
                modified_timestamp
            ),

            approved_timestamp=(
                approved_timestamp
            ),

            created_by=created_by,

            approved_by=approved_by,

            revision=revision,

            # ------------------------------------------------
            # Future Knowledge Graph
            # ------------------------------------------------

            ontology_uri=ontology_uri,

            graph_node_id=graph_node_id,

            symbolic_identifier=(
                symbolic_identifier
            ),

            embedding_identifier=(
                embedding_identifier
            ),

            export_identifier=(
                export_identifier
            ),

            llm_summary=llm_summary,

            # ------------------------------------------------
            # Engineering Ownership
            # ------------------------------------------------

            responsible_team=(
                responsible_team
            ),

            responsible_engineer=(
                responsible_engineer
            ),

            owning_organization=(
                owning_organization
            ),

            project_name=project_name,

            program_name=program_name,

            # ------------------------------------------------
            # Verification & Validation
            # ------------------------------------------------

            verification_status=(
                verification_status
            ),

            validation_status=(
                validation_status
            ),

            verification_method=(
                verification_method
            ),

            verification_document_ids=(
                verification_document_ids
            ),

            test_case_ids=(
                test_case_ids
            ),

            # ------------------------------------------------
            # Safety & Reliability
            # ------------------------------------------------

            safety_classification=(
                safety_classification
            ),

            reliability_target=(
                reliability_target
            ),

            failure_mode_ids=(
                failure_mode_ids
            ),

            hazard_ids=hazard_ids,

            risk_ids=risk_ids,

            # ------------------------------------------------
            # Digital Engineering
            # ------------------------------------------------

            cad_model_ids=(
                cad_model_ids
            ),

            cfd_model_ids=(
                cfd_model_ids
            ),

            fem_model_ids=(
                fem_model_ids
            ),

            optimization_case_ids=(
                optimization_case_ids
            ),

            simulation_case_ids=(
                simulation_case_ids
            ),

            digital_twin_identifier=(
                digital_twin_identifier
            ),

            # ------------------------------------------------
            # Manufacturing
            # ------------------------------------------------

            manufacturing_processes=(
                manufacturing_processes
            ),

            manufacturing_constraints=(
                manufacturing_constraints
            ),

            inspection_requirements=(
                inspection_requirements
            ),

            supplier_ids=(
                supplier_ids
            ),

            # ------------------------------------------------
            # Knowledge Foundation
            # ------------------------------------------------

            repository_path=(
                repository_path
            ),

            repository_identifier=(
                repository_identifier
            ),

            knowledge_tags=(
                knowledge_tags
            ),

            ontology_terms=(
                ontology_terms
            ),

            semantic_keywords=(
                semantic_keywords
            ),

            # ------------------------------------------------
            # AI Metadata
            # ------------------------------------------------

            ai_summary=(
                ai_summary
            ),

            ai_embedding_identifier=(
                ai_embedding_identifier
            ),

            ai_vector_database_id=(
                ai_vector_database_id
            ),

            llm_context_identifier=(
                llm_context_identifier
            ),

            symbolic_model_identifier=(
                symbolic_model_identifier
            ),

            # ------------------------------------------------
            # Future Extensions
            # ------------------------------------------------

            custom_metadata=(
                custom_metadata
            ),

            extension_fields=(
                extension_fields
            ),
        )    
    
        # ========================================================
        # Convenience Methods
        # ========================================================

    def copy(
        self,
    ) -> "Subsystem":
        """Return an immutable copy."""

        return self.from_dict(
            self.to_dict()
        )

    def serialize(
        self,
    ) -> dict[str, object]:
        """Alias for to_dict()."""

        return self.to_dict()

    @classmethod
    def deserialize(
        cls,
        payload: dict[str, object],
    ) -> "Subsystem":
        """Alias for from_dict()."""

        return cls.from_dict(
            payload
        )

    def __iter__(
        self,
    ) -> Iterator[tuple[str, object]]:
        """Iterate over serialized fields."""

        yield from self.to_dict().items()

    def __len__(
        self,
    ) -> int:
        """Return serialized field count."""

        return len(
            self.to_dict()
        ) 
    # ========================================================
    # Query Methods
    # ========================================================

    def display_name(
        self,
    ) -> str:
        """
        Return a human-readable display name.

        Returns
        -------
        str
        """

        return f"{self.name} ({self.symbol})"

    def matches_alias(
        self,
        alias: str,
    ) -> bool:
        """
        Determine whether an alias matches.

        Matching is case-insensitive.
        """

        if not isinstance(alias, str):
            return False

        candidate = alias.strip().casefold()

        return any(
            candidate == value.casefold()
            for value in self.aliases
        )

    def matches_keyword(
        self,
        keyword: str,
    ) -> bool:
        """
        Determine whether a keyword matches.

        Matching is case-insensitive.
        """

        if not isinstance(keyword, str):
            return False

        candidate = keyword.strip().casefold()

        return any(
            candidate == value.casefold()
            for value in self.search_keywords
        )

    def has_reference(
        self,
    ) -> bool:
        """
        Determine whether a Reference exists.
        """

        return self.source_reference is not None

    def has_document(
        self,
    ) -> bool:
        """
        Determine whether a Document exists.
        """

        return self.source_document is not None

    def has_parent(
        self,
    ) -> bool:
        """
        Determine whether this subsystem has a parent.
        """

        return self.parent_subsystem_id is not None

    def has_children(
        self,
    ) -> bool:
        """
        Determine whether child subsystems exist.
        """

        return len(self.child_subsystem_ids) > 0

    def is_root(
        self,
    ) -> bool:
        """
        Determine whether this is the root subsystem.
        """

        return self.parent_subsystem_id is None

    def is_leaf(
        self,
    ) -> bool:
        """
        Determine whether this subsystem has no children.
        """

        return len(self.child_subsystem_ids) == 0

    def is_active(
        self,
    ) -> bool:
        """
        Determine whether the subsystem is active.
        """

        return self.status is SubsystemStatus.ACTIVE

    def is_verified(
        self,
    ) -> bool:
        """
        Determine whether the subsystem has been verified.
        """

        return self.status in (
            SubsystemStatus.VERIFIED,
            SubsystemStatus.VALIDATED,
            SubsystemStatus.QUALIFIED,
            SubsystemStatus.CERTIFIED,
            SubsystemStatus.RELEASED,
            SubsystemStatus.ACTIVE,
        )

    def is_mission_critical(
        self,
    ) -> bool:
        """
        Determine whether this subsystem is mission critical.
        """

        return (
            self.criticality
            is CriticalityLevel.MISSION_CRITICAL
        )

    def is_safety_critical(
        self,
    ) -> bool:
        """
        Determine whether this subsystem is safety critical.
        """

        return (
            self.criticality
            is CriticalityLevel.SAFETY_CRITICAL
        )

    # ========================================================
    # Analysis Methods
    # ========================================================

    def child_count(
        self,
    ) -> int:
        """
        Return the number of child subsystems.
        """

        return len(
            self.child_subsystem_ids
        )

    def engineering_discipline_count(
        self,
    ) -> int:
        """
        Return the number of engineering disciplines.
        """

        return len(
            self.engineering_disciplines
        )

    def supported_physics_count(
        self,
    ) -> int:
        """
        Return the number of supported physics domains.
        """

        return len(
            self.supported_physics
        )

    def applicable_regime_count(
        self,
    ) -> int:
        """
        Return the number of applicable engineering regimes.
        """

        return len(
            self.applicable_regimes
        )

    def interface_count(
        self,
    ) -> int:
        """
        Return the number of subsystem interfaces.
        """

        return len(
            self.interfaces
        )

    def requirement_count(
        self,
    ) -> int:
        """
        Return the number of engineering requirements.
        """

        return len(
            self.requirements
        )

    def constraint_count(
        self,
    ) -> int:
        """
        Return the number of design constraints.
        """

        return len(
            self.design_constraints
        )

    def relationship_count(
        self,
    ) -> int:
        """
        Return the total number of knowledge relationships.
        """

        return (
            len(self.related_variable_ids)
            + len(self.related_equation_ids)
            + len(self.related_constant_ids)
            + len(self.related_unit_ids)
            + len(self.related_dimension_ids)
            + len(self.related_material_ids)
            + len(self.related_component_ids)
            + len(self.related_simulation_ids)
        )

    def alias_count(
        self,
    ) -> int:
        """
        Return the number of aliases.
        """

        return len(
            self.aliases
        )

    def common_name_count(
        self,
    ) -> int:
        """
        Return the number of common names.
        """

        return len(
            self.common_names
        )

    def keyword_count(
        self,
    ) -> int:
        """
        Return the number of search keywords.
        """

        return len(
            self.search_keywords
        )

    def tag_count(
        self,
    ) -> int:
        """
        Return the number of subsystem tags.
        """

        return len(
            self.tags
        )

    def knowledge_tag_count(
        self,
    ) -> int:
        """
        Return the number of knowledge tags.
        """

        return len(
            self.knowledge_tags
        )

    def ontology_term_count(
        self,
    ) -> int:
        """
        Return the number of ontology terms.
        """

        return len(
            self.ontology_terms
        )

    def semantic_keyword_count(
        self,
    ) -> int:
        """
        Return the number of semantic keywords.
        """

        return len(
            self.semantic_keywords
        )

    def verification_document_count(
        self,
    ) -> int:
        """
        Return the number of verification documents.
        """

        return len(
            self.verification_document_ids
        )

    def test_case_count(
        self,
    ) -> int:
        """
        Return the number of linked test cases.
        """

        return len(
            self.test_case_ids
        )

    def failure_mode_count(
        self,
    ) -> int:
        """
        Return the number of linked failure modes.
        """

        return len(
            self.failure_mode_ids
        )

    def hazard_count(
        self,
    ) -> int:
        """
        Return the number of hazards.
        """

        return len(
            self.hazard_ids
        )

    def risk_count(
        self,
    ) -> int:
        """
        Return the number of risks.
        """

        return len(
            self.risk_ids
        )

    def cad_model_count(
        self,
    ) -> int:
        """
        Return the number of CAD models.
        """

        return len(
            self.cad_model_ids
        )

    def cfd_model_count(
        self,
    ) -> int:
        """
        Return the number of CFD models.
        """

        return len(
            self.cfd_model_ids
        )

    def fem_model_count(
        self,
    ) -> int:
        """
        Return the number of FEM models.
        """

        return len(
            self.fem_model_ids
        )

    def simulation_case_count(
        self,
    ) -> int:
        """
        Return the number of simulation cases.
        """

        return len(
            self.simulation_case_ids
        )

    def optimization_case_count(
        self,
    ) -> int:
        """
        Return the number of optimization cases.
        """

        return len(
            self.optimization_case_ids
        )

    def manufacturing_process_count(
        self,
    ) -> int:
        """
        Return the number of manufacturing processes.
        """

        return len(
            self.manufacturing_processes
        )

    def supplier_count(
        self,
    ) -> int:
        """
        Return the number of suppliers.
        """

        return len(
            self.supplier_ids
        )

    def hierarchy_size(
        self,
    ) -> int:
        """
        Return the size of the hierarchy represented
        by this subsystem node.

        This includes the current subsystem and all
        immediate child subsystem identifiers.
        """

        return (
            1
            + len(
                self.child_subsystem_ids
            )
        )

    def export_identifier_count(
        self,
    ) -> int:
        """
        Return the number of export identifiers.

        Reserved for future multi-format export support.
        """

        return (
            0
            if self.export_identifier is None
            else 1
        )

