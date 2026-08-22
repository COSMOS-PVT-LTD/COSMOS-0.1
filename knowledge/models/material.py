"""
knowledge.models.material
=========================

Enterprise immutable engineering material model used by the
COSMOS Knowledge Foundation.

Purpose
-------
Defines the canonical Material entity used throughout COSMOS.

A Material represents a physical engineering material together
with its classification, engineering metadata, documentation,
knowledge graph relationships, lifecycle metadata, and AI-ready
metadata.

Examples
--------
GRCop-42
GRCop-84
CuCrZr
Inconel 718
Ti-6Al-4V
AA2195
Stainless Steel 304L
Carbon Phenolic
Silica Tile

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


from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Final

from knowledge.models.document import Document
from knowledge.models.reference import Reference

# ============================================================
# Enumerations
# ============================================================


class MaterialCategory(Enum):
    """
    High-level engineering material classification.
    """

    METAL = "METAL"

    ALLOY = "ALLOY"

    SUPERALLOY = "SUPERALLOY"

    CERAMIC = "CERAMIC"

    POLYMER = "POLYMER"

    COMPOSITE = "COMPOSITE"

    ELASTOMER = "ELASTOMER"

    GLASS = "GLASS"

    CARBON = "CARBON"

    REFRACTORY = "REFRACTORY"

    COATING = "COATING"

    FOAM = "FOAM"

    ADHESIVE = "ADHESIVE"

    OTHER = "OTHER"


class MaterialStatus(Enum):
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


class MaterialCriticality(Enum):
    """
    Engineering criticality classification.
    """

    LOW = "LOW"

    MEDIUM = "MEDIUM"

    HIGH = "HIGH"

    MISSION_CRITICAL = "MISSION_CRITICAL"

    SAFETY_CRITICAL = "SAFETY_CRITICAL"


# Backwards-compatible alias used by older tests/code
DomainCriticality = MaterialCriticality


class MaterialMaturityLevel(Enum):
    """
    Material maturity classification.
    """

    RESEARCH = "RESEARCH"

    EXPERIMENTAL = "EXPERIMENTAL"

    LABORATORY = "LABORATORY"

    PROTOTYPE = "PROTOTYPE"

    QUALIFIED = "QUALIFIED"

    FLIGHT_PROVEN = "FLIGHT_PROVEN"

    HERITAGE = "HERITAGE"


class MaterialClass(Enum):
    """
    Engineering material family.
    """

    FERROUS = "FERROUS"

    NON_FERROUS = "NON_FERROUS"

    NICKEL_BASED = "NICKEL_BASED"

    COBALT_BASED = "COBALT_BASED"

    TITANIUM_BASED = "TITANIUM_BASED"

    ALUMINUM_BASED = "ALUMINUM_BASED"

    COPPER_BASED = "COPPER_BASED"

    MAGNESIUM_BASED = "MAGNESIUM_BASED"

    REFRACTORY_METAL = "REFRACTORY_METAL"

    CERAMIC_MATRIX = "CERAMIC_MATRIX"

    METAL_MATRIX = "METAL_MATRIX"

    POLYMER_MATRIX = "POLYMER_MATRIX"

    CARBON_CARBON = "CARBON_CARBON"

    CARBON_FIBER = "CARBON_FIBER"

    OTHER = "OTHER"

# ============================================================
# Module Constants
# ============================================================

CURRENT_MATERIAL_MODEL_VERSION: Final[str] = "1.0"

MAX_MATERIAL_NAME_LENGTH: Final[int] = 256

MAX_DESCRIPTION_LENGTH: Final[int] = 10000

MAX_ALIAS_COUNT: Final[int] = 256

MAX_KEYWORD_COUNT: Final[int] = 512


# ============================================================
# Material Model
# ============================================================


@dataclass(
    frozen=True,
    slots=True,
)
class Material:
    """
    Enterprise engineering material.

    A Material represents a physical engineering material
    together with its engineering properties, metadata,
    documentation, lifecycle state, and repository
    information.
    """

    # ========================================================
    # Identity
    # ========================================================

    material_id: str

    name: str

    short_name: str

    symbol: str

    chemical_formula: str | None

    description: str

    # ========================================================
    # Classification
    # ========================================================

    category: MaterialCategory

    material_class: MaterialClass

    status: MaterialStatus

    maturity_level: MaterialMaturityLevel

    criticality: MaterialCriticality

    # ========================================================
    # Chemical Information
    # ========================================================

    alloy_family: str | None

    composition: Mapping[str, float]

    uns_designation: str | None

    astm_designation: str | None

    ams_designation: str | None

    nasa_designation: str | None

    # ========================================================
    # Mechanical Properties
    # ========================================================

    density: float | None

    youngs_modulus: float | None

    shear_modulus: float | None

    bulk_modulus: float | None

    poisson_ratio: float | None

    yield_strength: float | None

    ultimate_tensile_strength: float | None

    compressive_strength: float | None

    fatigue_strength: float | None

    fracture_toughness: float | None

    hardness: float | None

    # ========================================================
    # Thermal Properties
    # ========================================================

    melting_point: float | None

    thermal_conductivity: float | None

    specific_heat_capacity: float | None

    coefficient_thermal_expansion: float | None

    emissivity: float | None

    # ========================================================
    # Electrical Properties
    # ========================================================

    electrical_conductivity: float | None

    electrical_resistivity: float | None

    # ========================================================
    # Manufacturing
    # ========================================================

    additive_manufacturing: bool

    machinable: bool

    weldable: bool

    heat_treatable: bool

    manufacturing_processes: tuple[str, ...]

    # ========================================================
    # Compatibility
    # ========================================================

    compatible_propellants: tuple[str, ...]

    corrosion_notes: str | None

    oxidation_behavior: str | None

    cryogenic_capable: bool

    vacuum_compatible: bool

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

    related_subsystem_ids: tuple[str, ...]

    related_engineering_domain_ids: tuple[str, ...]

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
    # Knowledge Graph
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
    # AI Metadata
    # ========================================================

    ai_summary: str | None

    ai_embedding_identifier: str | None

    ai_vector_database_id: str | None

    llm_context_identifier: str |None

    symbolic_model_identifier: str | None

    # ========================================================
    # Future Extensions
    # ========================================================

    custom_metadata: Mapping[str, object] | None

    extension_fields: Mapping[str, object] | None

    repository_path: str | None = None

    repository_identifier: str | None = None

    # ========================================================
    # Initialization
    # ========================================================

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the Material immediately after construction.
        """

        self.validate()

    # ========================================================
    # Public Validation
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the complete Material.

        Validation responsibilities are delegated to
        specialized private validator methods to keep the
        implementation modular, maintainable, and
        enterprise-scale.
        """

        self._validate_identity()

        self._validate_classification()

        self._validate_chemical_information()

        self._validate_mechanical_properties()

        self._validate_thermal_properties()

        self._validate_electrical_properties()

        self._validate_manufacturing()

        self._validate_compatibility()

        self._validate_knowledge_metadata()

        self._validate_relationships()

        self._validate_documentation()

        self._validate_repository_metadata()

        self._validate_knowledge_graph()

        self._validate_engineering_ownership()

        self._validate_verification_validation()

        self._validate_custom_metadata()

        self._validate_extension_fields()

        self._validate_ai_metadata()

        self._validate_future_metadata()

    # ========================================================
    # Identity Validation
    # ========================================================

    def _validate_identity(
        self,
    ) -> None:
        """Validate identity fields."""

        self._validate_material_id()

        self._validate_name()

        self._validate_short_name()

        self._validate_symbol()

        self._validate_chemical_formula()

        self._validate_description()

    # ========================================================
    # Classification Validation
    # ========================================================

    def _validate_classification(
        self,
    ) -> None:
        """Validate material classification."""

        self._validate_category()

        self._validate_material_class()

        self._validate_status()

        self._validate_maturity_level()

        self._validate_criticality()

    # ========================================================
    # Chemical Information Validation
    # ========================================================

    def _validate_chemical_information(
        self,
    ) -> None:
        """Validate chemical information."""

        self._validate_alloy_family()

        self._validate_composition()

        self._validate_uns_designation()

        self._validate_astm_designation()

        self._validate_ams_designation()

        self._validate_nasa_designation()

    # ========================================================
    # Mechanical Properties Validation
    # ========================================================

    def _validate_mechanical_properties(
        self,
    ) -> None:
        """Validate mechanical properties."""

        self._validate_density()

        self._validate_youngs_modulus()

        self._validate_shear_modulus()

        self._validate_bulk_modulus()

        self._validate_poisson_ratio()

        self._validate_yield_strength()

        self._validate_ultimate_tensile_strength()

        self._validate_compressive_strength()

        self._validate_fatigue_strength()

        self._validate_fracture_toughness()

        self._validate_hardness()

    # ========================================================
    # Thermal Properties Validation
    # ========================================================

    def _validate_thermal_properties(
        self,
    ) -> None:
        """Validate thermal properties."""

        self._validate_melting_point()

        self._validate_thermal_conductivity()

        self._validate_specific_heat_capacity()

        self._validate_coefficient_thermal_expansion()

        self._validate_emissivity()

    # ========================================================
    # Electrical Properties Validation
    # ========================================================

    def _validate_electrical_properties(
        self,
    ) -> None:
        """Validate electrical properties."""

        self._validate_electrical_conductivity()

        self._validate_electrical_resistivity()

    # ========================================================
    # Manufacturing Validation
    # ========================================================

    def _validate_manufacturing(
        self,
    ) -> None:
        """Validate manufacturing metadata."""

        self._validate_additive_manufacturing()

        self._validate_machinable()

        self._validate_weldable()

        self._validate_heat_treatable()

        self._validate_manufacturing_processes()

    # ========================================================
    # Compatibility Validation
    # ========================================================

    def _validate_compatibility(
        self,
    ) -> None:
        """Validate compatibility metadata."""

        self._validate_compatible_propellants()

        self._validate_corrosion_notes()

        self._validate_oxidation_behavior()

        self._validate_cryogenic_capable()

        self._validate_vacuum_compatible()

    # ========================================================
    # Knowledge Metadata Validation
    # ========================================================

    def _validate_knowledge_metadata(
        self,
    ) -> None:
        """Validate knowledge metadata."""

        self._validate_aliases()

        self._validate_common_names()

        self._validate_search_keywords()

        self._validate_tags()

    # ========================================================
    # Relationship Validation
    # ========================================================

    def _validate_relationships(
        self,
    ) -> None:
        """Validate knowledge relationships."""

        self._validate_related_variable_ids()

        self._validate_related_equation_ids()

        self._validate_related_constant_ids()

        self._validate_related_unit_ids()

        self._validate_related_dimension_ids()

        self._validate_related_subsystem_ids()

        self._validate_related_engineering_domain_ids()

        self._validate_related_simulation_ids()

    # ========================================================
    # Documentation Validation
    # ========================================================

    def _validate_documentation(
        self,
    ) -> None:
        """Validate documentation."""

        self._validate_reference()

        self._validate_document()

    # ========================================================
    # Repository Metadata Validation
    # ========================================================

    def _validate_repository_metadata(
        self,
    ) -> None:
        """Validate repository metadata."""

        self._validate_version()

        self._validate_status_note()

        self._validate_created_timestamp()

        self._validate_modified_timestamp()

        self._validate_approved_timestamp()

        self._validate_created_by()

        self._validate_approved_by()

        self._validate_revision()

        self._validate_repository_identifiers()

        self._validate_repository_path()

    # ========================================================
    # Knowledge Graph Validation
    # ========================================================

    def _validate_knowledge_graph(
        self,
    ) -> None:
        """Validate knowledge graph metadata."""

        self._validate_ontology()

        self._validate_graph_node()

        self._validate_symbolic_identifier()

        self._validate_embedding_identifier()

        self._validate_export_identifier()

        self._validate_llm_summary()

    #=========================================================
    # custom metadata validation
    # ========================================================    

    def _validate_custom_metadata(
        self,
    ) -> None:
     """ Validate custom metadata."""
     
     if (
        self.custom_metadata is not None
        and
        not isinstance(
            self.custom_metadata,
            Mapping,
        )
     ):
        raise TypeError(
            "custom_metadata must be a mapping."
        ) 

    #=========================================================
    # extension fields validation   
    #=========================================================

    def _validate_extension_fields(
        self,
    ) -> None:
     """Validate extension fields."""
     
     if (
        self.extension_fields is not None
        and
        not isinstance(
            self.extension_fields,
            Mapping,
        )
     ):
        raise TypeError(
            "extension_fields must be a mapping."
        )   

    # ========================================================
    # AI Metadata Validation
    # ========================================================

    def _validate_ai_metadata(
        self,
    ) -> None:
        """Validate AI metadata."""

        self._validate_ai_summary()

        self._validate_ai_identifiers()

    

    # ========================================================
    # Future Metadata Validation
    # ========================================================

    def _validate_future_metadata(
        self,
    ) -> None:
        """
        Placeholder for future validation.
        """

        return

    # ========================================================
    # Identity Validators
    # ========================================================

    def _validate_material_id(self) -> None:
        """
        Validate the material identifier.
        """

        if not isinstance(self.material_id, str):
            raise TypeError(
                "material_id must be a string."
            )

        if not self.material_id.strip():
            raise ValueError(
                "material_id cannot be blank."
            )

    def _validate_name(self) -> None:
        """
        Validate the material name.
        """

        if not isinstance(self.name, str):
            raise TypeError(
                "name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "name cannot be blank."
            )

        if (
            len(self.name)
            > MAX_MATERIAL_NAME_LENGTH
        ):
            raise ValueError(
                "Material name exceeds the maximum allowed length."
            )

    def _validate_short_name(self) -> None:
        """
        Validate the short name.
        """

        if not isinstance(self.short_name, str):
            raise TypeError(
                "short_name must be a string."
            )

        if not self.short_name.strip():
            raise ValueError(
                "short_name cannot be blank."
            )

    def _validate_symbol(self) -> None:
        """
        Validate the material symbol.
        """

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

    def _validate_chemical_formula(self) -> None:
        """
        Validate the chemical formula.
        """

        if (
            self.chemical_formula is not None
            and not isinstance(
                self.chemical_formula,
                str,
            )
        ):
            raise TypeError(
                "chemical_formula must be a string or None."
            )

    def _validate_description(self) -> None:
        """
        Validate the material description.
        """

        if not isinstance(
            self.description,
            str,
        ):
            raise TypeError(
                "description must be a string."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be blank."
            )

        if (
            len(self.description)
            > MAX_DESCRIPTION_LENGTH
        ):
            raise ValueError(
                "Description exceeds the maximum allowed length."
            )

    # ========================================================
    # Classification Validators
    # ========================================================

    def _validate_category(
        self,
    ) -> None:
        """
        Validate the material category.
        """

        if not isinstance(
            self.category,
            MaterialCategory,
        ):
            raise TypeError(
                "category must be a MaterialCategory."
            )

    def _validate_material_class(
        self,
    ) -> None:
        """
        Validate the material class.
        """

        if not isinstance(
            self.material_class,
            MaterialClass,
        ):
            raise TypeError(
                "material_class must be a MaterialClass."
            )

    def _validate_status(
        self,
    ) -> None:
        """
        Validate the material status.
        """

        if not isinstance(
            self.status,
            MaterialStatus,
        ):
            raise TypeError(
                "status must be a MaterialStatus."
            )

    def _validate_maturity_level(
        self,
    ) -> None:
        """
        Validate the material maturity level.
        """

        if not isinstance(
            self.maturity_level,
            MaterialMaturityLevel,
        ):
            raise TypeError(
                "maturity_level must be a MaterialMaturityLevel."
            )

    def _validate_criticality(
        self,
    ) -> None:
        """
        Validate the material criticality.
        """

        if not isinstance(
            self.criticality,
            MaterialCriticality,
        ):
            raise TypeError(
                "criticality must be a MaterialCriticality."
            ) 

    # ========================================================
    # Chemical Information Validators
    # ========================================================

    def _validate_alloy_family(
        self,
    ) -> None:
        """
        Validate the alloy family.
        """

        if (
            self.alloy_family is not None
            and not isinstance(
                self.alloy_family,
                str,
            )
        ):
            raise TypeError(
                "alloy_family must be a string or None."
            )

    def _validate_composition(
        self,
    ) -> None:
        """
        Validate the elemental composition mapping.
        """

        if not isinstance(
            self.composition,
            Mapping,
        ):
            raise TypeError(
                "composition must be a mapping."
            )

        for element, fraction in self.composition.items():

            if not isinstance(
                element,
                str,
            ):
                raise TypeError(
                    "Composition element symbols must be strings."
                )

            if not element.strip():
                raise ValueError(
                    "Composition element symbols cannot be blank."
                )

            if not isinstance(
                fraction,
                (int, float),
            ):
                raise TypeError(
                    "Composition fractions must be numeric."
                )

            if fraction < 0.0:
                raise ValueError(
                    "Composition fractions cannot be negative."
                )

            if fraction > 100.0:
                raise ValueError(
                    "Composition fractions cannot exceed 100."
                )

    def _validate_uns_designation(
        self,
    ) -> None:
        """
        Validate the UNS designation.
        """

        if (
            self.uns_designation is not None
            and not isinstance(
                self.uns_designation,
                str,
            )
        ):
            raise TypeError(
                "uns_designation must be a string or None."
            )

    def _validate_astm_designation(
        self,
    ) -> None:
        """
        Validate the ASTM designation.
        """

        if (
            self.astm_designation is not None
            and not isinstance(
                self.astm_designation,
                str,
            )
        ):
            raise TypeError(
                "astm_designation must be a string or None."
            )

    def _validate_ams_designation(
        self,
    ) -> None:
        """
        Validate the AMS designation.
        """

        if (
            self.ams_designation is not None
            and not isinstance(
                self.ams_designation,
                str,
            )
        ):
            raise TypeError(
                "ams_designation must be a string or None."
            )

    def _validate_nasa_designation(
        self,
    ) -> None:
        """
        Validate the NASA designation.
        """

        if (
            self.nasa_designation is not None
            and not isinstance(
                self.nasa_designation,
                str,
            )
        ):
            raise TypeError(
                "nasa_designation must be a string or None."
            )

    # ========================================================
    # Mechanical Property Validators
    # ========================================================

    def _validate_density(
        self,
    ) -> None:
        """
        Validate material density.
        """

        self._validate_positive_float(
            self.density,
            "density",
        )

    def _validate_youngs_modulus(
        self,
    ) -> None:
        """
        Validate Young's modulus.
        """

        self._validate_positive_float(
            self.youngs_modulus,
            "youngs_modulus",
        )

    def _validate_shear_modulus(
        self,
    ) -> None:
        """
        Validate shear modulus.
        """

        self._validate_positive_float(
            self.shear_modulus,
            "shear_modulus",
        )

    def _validate_bulk_modulus(
        self,
    ) -> None:
        """
        Validate bulk modulus.
        """

        self._validate_positive_float(
            self.bulk_modulus,
            "bulk_modulus",
        )

    def _validate_poisson_ratio(
        self,
    ) -> None:
        """
        Validate Poisson's ratio.
        """

        if self.poisson_ratio is None:
            return

        if not isinstance(
            self.poisson_ratio,
            (int, float),
        ):
            raise TypeError(
                "poisson_ratio must be numeric or None."
            )

        if not (
            0.0
            <= self.poisson_ratio
            <= 0.5
        ):
            raise ValueError(
                "poisson_ratio must be between 0.0 and 0.5."
            )

    def _validate_yield_strength(
        self,
    ) -> None:
        """
        Validate yield strength.
        """

        self._validate_positive_float(
            self.yield_strength,
            "yield_strength",
        )

    def _validate_ultimate_tensile_strength(
        self,
    ) -> None:
        """
        Validate ultimate tensile strength.
        """

        self._validate_positive_float(
            self.ultimate_tensile_strength,
            "ultimate_tensile_strength",
        )

    def _validate_compressive_strength(
        self,
    ) -> None:
        """
        Validate compressive strength.
        """

        self._validate_positive_float(
            self.compressive_strength,
            "compressive_strength",
        )

    def _validate_fatigue_strength(
        self,
    ) -> None:
        """
        Validate fatigue strength.
        """

        self._validate_positive_float(
            self.fatigue_strength,
            "fatigue_strength",
        )

    def _validate_fracture_toughness(
        self,
    ) -> None:
        """
        Validate fracture toughness.
        """

        self._validate_positive_float(
            self.fracture_toughness,
            "fracture_toughness",
        )

    def _validate_hardness(
        self,
    ) -> None:
        """
        Validate material hardness.
        """

        self._validate_positive_float(
            self.hardness,
            "hardness",
        )

    # ========================================================
    # Thermal Property Validators
    # ========================================================

    def _validate_melting_point(
        self,
    ) -> None:
        """
        Validate melting point.
        """

        self._validate_positive_float(
            self.melting_point,
            "melting_point",
        )

    def _validate_thermal_conductivity(
        self,
    ) -> None:
        """
        Validate thermal conductivity.
        """

        self._validate_positive_float(
            self.thermal_conductivity,
            "thermal_conductivity",
        )

    def _validate_specific_heat_capacity(
        self,
    ) -> None:
        """
        Validate specific heat capacity.
        """

        self._validate_positive_float(
            self.specific_heat_capacity,
            "specific_heat_capacity",
        )

    def _validate_coefficient_thermal_expansion(
        self,
    ) -> None:
        """
        Validate coefficient of thermal expansion.
        """

        self._validate_positive_float(
            self.coefficient_thermal_expansion,
            "coefficient_thermal_expansion",
        )

    def _validate_emissivity(
        self,
    ) -> None:
        """
        Validate emissivity.

        Emissivity is dimensionless and must lie within
        the interval [0, 1].
        """

        if self.emissivity is None:
            return

        if not isinstance(
            self.emissivity,
            (int, float),
        ):
            raise TypeError(
                "emissivity must be numeric or None."
            )

        if not (
            0.0 <= self.emissivity <= 1.0
        ):
            raise ValueError(
                "emissivity must be between 0.0 and 1.0."
            )

    # ========================================================
    # Electrical Property Validators
    # ========================================================

    def _validate_electrical_conductivity(
        self,
    ) -> None:
        """
        Validate electrical conductivity.

        Electrical conductivity shall be positive when
        specified.
        """

        self._validate_positive_float(
            self.electrical_conductivity,
            "electrical_conductivity",
        )

    def _validate_electrical_resistivity(
        self,
    ) -> None:
        """
        Validate electrical resistivity.

        Electrical resistivity shall be positive when
        specified.
        """

        self._validate_positive_float(
            self.electrical_resistivity,
            "electrical_resistivity",
        ) 

    # ========================================================
    # Manufacturing Validators
    # ========================================================

    def _validate_additive_manufacturing(
        self,
    ) -> None:
        """
        Validate additive manufacturing capability.
        """

        if not isinstance(
            self.additive_manufacturing,
            bool,
        ):
            raise TypeError(
                "additive_manufacturing must be a bool."
            )

    def _validate_machinable(
        self,
    ) -> None:
        """
        Validate machinability flag.
        """

        if not isinstance(
            self.machinable,
            bool,
        ):
            raise TypeError(
                "machinable must be a bool."
            )

    def _validate_weldable(
        self,
    ) -> None:
        """
        Validate weldability flag.
        """

        if not isinstance(
            self.weldable,
            bool,
        ):
            raise TypeError(
                "weldable must be a bool."
            )

    def _validate_heat_treatable(
        self,
    ) -> None:
        """
        Validate heat treatment capability.
        """

        if not isinstance(
            self.heat_treatable,
            bool,
        ):
            raise TypeError(
                "heat_treatable must be a bool."
            )

    def _validate_manufacturing_processes(
        self,
    ) -> None:
        """
        Validate supported manufacturing processes.
        """

        self._validate_string_tuple(
            self.manufacturing_processes,
            "manufacturing_processes",
        )

    # ========================================================
    # Compatibility Validators
    # ========================================================

    def _validate_compatible_propellants(
        self,
    ) -> None:
        """
        Validate compatible propellants.
        """

        self._validate_string_tuple(
            self.compatible_propellants,
            "compatible_propellants",
        )

    def _validate_corrosion_notes(
        self,
    ) -> None:
        """
        Validate corrosion notes.
        """

        if (
            self.corrosion_notes is not None
            and not isinstance(
                self.corrosion_notes,
                str,
            )
        ):
            raise TypeError(
                "corrosion_notes must be a string or None."
            )

    def _validate_oxidation_behavior(
        self,
    ) -> None:
        """
        Validate oxidation behavior.
        """

        if (
            self.oxidation_behavior is not None
            and not isinstance(
                self.oxidation_behavior,
                str,
            )
        ):
            raise TypeError(
                "oxidation_behavior must be a string or None."
            )

    def _validate_cryogenic_capable(
        self,
    ) -> None:
        """
        Validate cryogenic capability flag.
        """

        if not isinstance(
            self.cryogenic_capable,
            bool,
        ):
            raise TypeError(
                "cryogenic_capable must be a bool."
            )

    def _validate_vacuum_compatible(
        self,
    ) -> None:
        """
        Validate vacuum compatibility flag.
        """

        if not isinstance(
            self.vacuum_compatible,
            bool,
        ):
            raise TypeError(
                "vacuum_compatible must be a bool."
            )

    # ========================================================
    # Knowledge Metadata Validators
    # ========================================================

    def _validate_aliases(
        self,
    ) -> None:
        """
        Validate material aliases.
        """

        self._validate_string_tuple(
            self.aliases,
            "aliases",
        )

        if (
            len(self.aliases)
            > MAX_ALIAS_COUNT
        ):
            raise ValueError(
                "Maximum alias count exceeded."
            )

    def _validate_common_names(
        self,
    ) -> None:
        """
        Validate common material names.
        """

        self._validate_string_tuple(
            self.common_names,
            "common_names",
        )

    def _validate_search_keywords(
        self,
    ) -> None:
        """
        Validate search keywords.
        """

        self._validate_string_tuple(
            self.search_keywords,
            "search_keywords",
        )

        if (
            len(self.search_keywords)
            > MAX_KEYWORD_COUNT
        ):
            raise ValueError(
                "Maximum keyword count exceeded."
            )

    def _validate_tags(
        self,
    ) -> None:
        """
        Validate material tags.
        """

        self._validate_string_tuple(
            self.tags,
            "tags",
        )

    # ========================================================
    # Relationship Validators
    # ========================================================

    def _validate_related_variable_ids(
        self,
    ) -> None:
        """
        Validate related variable identifiers.
        """

        self._validate_string_tuple(
            self.related_variable_ids,
            "related_variable_ids",
        )

    def _validate_related_equation_ids(
        self,
    ) -> None:
        """
        Validate related equation identifiers.
        """

        self._validate_string_tuple(
            self.related_equation_ids,
            "related_equation_ids",
        )

    def _validate_related_constant_ids(
        self,
    ) -> None:
        """
        Validate related constant identifiers.
        """

        self._validate_string_tuple(
            self.related_constant_ids,
            "related_constant_ids",
        )

    def _validate_related_unit_ids(
        self,
    ) -> None:
        """
        Validate related unit identifiers.
        """

        self._validate_string_tuple(
            self.related_unit_ids,
            "related_unit_ids",
        )

    def _validate_related_dimension_ids(
        self,
    ) -> None:
        """
        Validate related dimension identifiers.
        """

        self._validate_string_tuple(
            self.related_dimension_ids,
            "related_dimension_ids",
        )

    def _validate_related_subsystem_ids(
        self,
    ) -> None:
        """
        Validate related subsystem identifiers.
        """

        self._validate_string_tuple(
            self.related_subsystem_ids,
            "related_subsystem_ids",
        )

    def _validate_related_engineering_domain_ids(
        self,
    ) -> None:
        """
        Validate related engineering domain identifiers.
        """

        self._validate_string_tuple(
            self.related_engineering_domain_ids,
            "related_engineering_domain_ids",
        )

    def _validate_related_simulation_ids(
        self,
    ) -> None:
        """
        Validate related simulation identifiers.
        """

        self._validate_string_tuple(
            self.related_simulation_ids,
            "related_simulation_ids",
        )
    # ========================================================
    # Documentation Validators
    # ========================================================

    def _validate_reference(
        self,
    ) -> None:
        """
        Validate the source reference.
        """

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

    def _validate_document(
        self,
    ) -> None:
        """
        Validate the source document.
        """

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
    # Repository Metadata Validators
    # ========================================================

    def _validate_version(
        self,
    ) -> None:
        """
        Validate the material model version.
        """

        if not isinstance(
            self.version,
            str,
        ):
            raise TypeError(
                "version must be a string."
            )

        if not self.version.strip():
            raise ValueError(
                "version cannot be blank."
            )

    def _validate_revision(
        self,
    ) -> None:
        """
        Validate the revision number.
        """

        if not isinstance(
            self.revision,
            int,
        ):
            raise TypeError(
                "revision must be an integer."
            )

        if self.revision < 0:
            raise ValueError(
                "revision cannot be negative."
            )

    def _validate_repository_identifiers(
        self,
    ) -> None:
        """
        Validate repository identifier.
        """

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

    def _validate_repository_path(
        self,
    ) -> None:
        """
        Validate repository path.
        """

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

    def _validate_status_note(
        self,
    ) -> None:
        """
        Validate repository status note.
        """

        if not isinstance(
            self.status_note,
            str,
        ):
            raise TypeError(
                "status_note must be a string."
            )

    def _validate_created_timestamp(
        self,
    ) -> None:
        """
        Validate creation timestamp.
        """

        if (
            self.created_timestamp is not None
            and not isinstance(
                self.created_timestamp,
                datetime,
            )
        ):
            raise TypeError(
                "created_timestamp must be a datetime or None."
            )

    def _validate_modified_timestamp(
        self,
    ) -> None:
        """
        Validate modification timestamp.
        """

        if (
            self.modified_timestamp is not None
            and not isinstance(
                self.modified_timestamp,
                datetime,
            )
        ):
            raise TypeError(
                "modified_timestamp must be a datetime or None."
            )

    def _validate_approved_timestamp(
        self,
    ) -> None:
        """
        Validate approval timestamp.
        """

        if (
            self.approved_timestamp is not None
            and not isinstance(
                self.approved_timestamp,
                datetime,
            )
        ):
            raise TypeError(
                "approved_timestamp must be a datetime or None."
            )

    def _validate_created_by(
        self,
    ) -> None:
        """
        Validate creator identifier.
        """

        if not isinstance(
            self.created_by,
            str,
        ):
            raise TypeError(
                "created_by must be a string."
            )

        if not self.created_by.strip():
            raise ValueError(
                "created_by cannot be blank."
            )

    def _validate_approved_by(
        self,
    ) -> None:
        """
        Validate approver identifier.
        """

        if (
            self.approved_by is not None
            and not isinstance(
                self.approved_by,
                str,
            )
        ):
            raise TypeError(
                "approved_by must be a string or None."
            )

        # ========================================================
    # Knowledge Graph Validators
    # ========================================================

    def _validate_ontology(
        self,
    ) -> None:
        """
        Validate ontology URI.
        """

        if (
            self.ontology_uri is not None
            and not isinstance(
                self.ontology_uri,
                str,
            )
        ):
            raise TypeError(
                "ontology_uri must be a string or None."
            )

    def _validate_graph_node(
        self,
    ) -> None:
        """
        Validate graph node identifier.
        """

        if (
            self.graph_node_id is not None
            and not isinstance(
                self.graph_node_id,
                str,
            )
        ):
            raise TypeError(
                "graph_node_id must be a string or None."
            )

    def _validate_symbolic_identifier(
        self,
    ) -> None:
        """
        Validate symbolic identifier.
        """

        if (
            self.symbolic_identifier is not None
            and not isinstance(
                self.symbolic_identifier,
                str,
            )
        ):
            raise TypeError(
                "symbolic_identifier must be a string or None."
            )

    def _validate_embedding_identifier(
        self,
    ) -> None:
        """
        Validate embedding identifier.
        """

        if (
            self.embedding_identifier is not None
            and not isinstance(
                self.embedding_identifier,
                str,
            )
        ):
            raise TypeError(
                "embedding_identifier must be a string or None."
            )

    def _validate_export_identifier(
        self,
    ) -> None:
        """
        Validate export identifier.
        """

        if (
            self.export_identifier is not None
            and not isinstance(
                self.export_identifier,
                str,
            )
        ):
            raise TypeError(
                "export_identifier must be a string or None."
            )

    def _validate_llm_summary(
        self,
    ) -> None:
        """
        Validate LLM summary.
        """

        if (
            self.llm_summary is not None
            and not isinstance(
                self.llm_summary,
                str,
            )
        ):
            raise TypeError(
                "llm_summary must be a string or None."
            )

        # ========================================================
    # Engineering Ownership Validators
    # ========================================================

    def _validate_engineering_ownership(
        self,
    ) -> None:
        """
        Validate engineering ownership metadata.
        """

        self._validate_responsible_team()

        self._validate_responsible_engineer()

        self._validate_owning_organization()

        self._validate_project_name()

        self._validate_program_name()

    def _validate_responsible_team(
        self,
    ) -> None:
        """
        Validate responsible engineering team.
        """

        if (
            self.responsible_team is not None
            and not isinstance(
                self.responsible_team,
                str,
            )
        ):
            raise TypeError(
                "responsible_team must be a string or None."
            )

    def _validate_responsible_engineer(
        self,
    ) -> None:
        """
        Validate responsible engineer.
        """

        if (
            self.responsible_engineer is not None
            and not isinstance(
                self.responsible_engineer,
                str,
            )
        ):
            raise TypeError(
                "responsible_engineer must be a string or None."
            )

    def _validate_owning_organization(
        self,
    ) -> None:
        """
        Validate owning organization.
        """

        if (
            self.owning_organization is not None
            and not isinstance(
                self.owning_organization,
                str,
            )
        ):
            raise TypeError(
                "owning_organization must be a string or None."
            )

    def _validate_project_name(
        self,
    ) -> None:
        """
        Validate project name.
        """

        if (
            self.project_name is not None
            and not isinstance(
                self.project_name,
                str,
            )
        ):
            raise TypeError(
                "project_name must be a string or None."
            )

    def _validate_program_name(
        self,
    ) -> None:
        """
        Validate program name.
        """

        if (
            self.program_name is not None
            and not isinstance(
                self.program_name,
                str,
            )
        ):
            raise TypeError(
                "program_name must be a string or None."
            )

        # ========================================================
    # Verification & Validation Validators
    # ========================================================

    def _validate_verification_validation(
        self,
    ) -> None:
        """
        Validate verification and validation metadata.
        """

        self._validate_verification_status()

        self._validate_validation_status()

        self._validate_verification_method()

        self._validate_verification_document_ids()

        self._validate_test_case_ids()

    def _validate_verification_status(
        self,
    ) -> None:
        """
        Validate verification status.
        """

        if (
            self.verification_status is not None
            and not isinstance(
                self.verification_status,
                str,
            )
        ):
            raise TypeError(
                "verification_status must be a string or None."
            )

    def _validate_validation_status(
        self,
    ) -> None:
        """
        Validate validation status.
        """

        if (
            self.validation_status is not None
            and not isinstance(
                self.validation_status,
                str,
            )
        ):
            raise TypeError(
                "validation_status must be a string or None."
            )

    def _validate_verification_method(
        self,
    ) -> None:
        """
        Validate verification method.
        """

        if (
            self.verification_method is not None
            and not isinstance(
                self.verification_method,
                str,
            )
        ):
            raise TypeError(
                "verification_method must be a string or None."
            )

    def _validate_verification_document_ids(
        self,
    ) -> None:
        """
        Validate verification document identifiers.
        """

        self._validate_string_tuple(
            self.verification_document_ids,
            "verification_document_ids",
        )

    def _validate_test_case_ids(
        self,
    ) -> None:
        """
        Validate linked test case identifiers.
        """

        self._validate_string_tuple(
            self.test_case_ids,
            "test_case_ids",
        )

    # ========================================================
    # AI Metadata Validators
    # ========================================================

    def _validate_ai_summary(
        self,
    ) -> None:
        """
        Validate AI-generated material summary.
        """

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

    def _validate_ai_identifiers(
        self,
    ) -> None:
        """
        Validate AI-related identifiers.
        """

        optional_strings = (
            self.ai_embedding_identifier,
            self.ai_vector_database_id,
            self.llm_context_identifier,
            self.symbolic_model_identifier,
        )

        for value in optional_strings:

            if (
                value is not None
                and not isinstance(
                    value,
                    str,
                )
            ):
                raise TypeError(
                    "AI identifiers must be strings or None."
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

        if not isinstance(
            values,
            tuple,
        ):
            raise TypeError(
                f"{field_name} must be a tuple."
            )

        for value in values:

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"Every element of {field_name} must be a string."
                )

    @staticmethod
    def _validate_positive_float(
        value: float | int | None,
        field_name: str,
    ) -> None:
        """
        Validate an optional positive numeric value.
        """

        if value is None:
            return

        if not isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            raise TypeError(
                f"{field_name} must be numeric or None."
            )

        if value <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

    @staticmethod
    def _validate_non_negative_float(
        value: float | int | None,
        field_name: str,
    ) -> None:
        """
        Validate an optional non-negative numeric value.
        """

        if value is None:
            return

        if not isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            raise TypeError(
                f"{field_name} must be numeric or None."
            )

        if value < 0:
            raise ValueError(
                f"{field_name} cannot be negative."
            )

    @staticmethod
    def _validate_optional_string(
        value: str | None,
        field_name: str,
    ) -> None:
        """
        Validate an optional string.
        """

        if (
            value is not None
            and not isinstance(
                value,
                str,
            )
        ):
            raise TypeError(
                f"{field_name} must be a string or None."
            )

    @staticmethod
    def _validate_datetime(
        value: datetime | None,
        field_name: str,
    ) -> None:
        """
        Validate an optional datetime.
        """

        if (
            value is not None
            and not isinstance(
                value,
                datetime,
            )
        ):
            raise TypeError(
                f"{field_name} must be a datetime or None."
            )

    @staticmethod
    def _validate_mapping(
        value: Mapping[str, str] | None,
        field_name: str,
    ) -> None:
        """
        Validate a string-to-string mapping.
        """

        if value is None:
            return

        if not isinstance(
            value,
            Mapping,
        ):
            raise TypeError(
                f"{field_name} must be a mapping."
            )

        for key, item in value.items():

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    f"{field_name} keys must be strings."
                )

            if not isinstance(
                item,
                str,
            ):
                raise TypeError(
                    f"{field_name} values must be strings."
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
            Datetime value to serialize.

        Returns
        -------
        str | None
            ISO 8601 formatted datetime string or None.
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
            ISO 8601 datetime string.

        Returns
        -------
        datetime | None
            Deserialized datetime object.
        """

        if value is None:
            return None

        return datetime.fromisoformat(value)

    # ========================================================
    # Reference & Document Serialization Helpers
    # ========================================================

    @staticmethod
    def _serialize_reference(
        reference: Reference | None,
    ) -> dict[str, object] | None:
        """
        Serialize a Reference.

        Parameters
        ----------
        reference : Reference | None

        Returns
        -------
        dict[str, object] | None
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

        Parameters
        ----------
        data : object

        Returns
        -------
        Reference | None
        """

        if data is None:
            return None

        if not isinstance(
            data,
            dict,
        ):
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

        Parameters
        ----------
        document : Document | None

        Returns
        -------
        dict[str, object] | None
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

        Parameters
        ----------
        data : object

        Returns
        -------
        Document | None
        """

        if data is None:
            return None

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "Document must be serialized as a dictionary."
            )

        return Document.from_dict(data)

    # ========================================================
    # Mapping Serialization Helpers
    # ========================================================

    @staticmethod
    def _serialize_mapping(
        mapping: Mapping[str, object] | None,
    ) -> dict[str, object] | None:
        """
        Serialize immutable metadata mappings.

        Parameters
        ----------
        mapping : Mapping[str, object] | None

        Returns
        -------
        dict[str, object] | None
        """

        if mapping is None:
            return None

        return dict(mapping)

    @staticmethod
    def _deserialize_mapping(
        mapping: object,
    ) -> Mapping[str, object] | None:
        """
        Deserialize immutable metadata mappings.

        Parameters
        ----------
        mapping : object

        Returns
        -------
        Mapping[str, object] | None
        """

        if mapping is None:
            return None

        if not isinstance(
            mapping,
            dict,
        ):
            raise TypeError(
                "Mapping must be serialized as a dictionary."
            )

        for key in mapping.keys():

            if not isinstance(
                key,
                str,
            ):
                raise TypeError(
                    "Mapping keys must be strings."
                )

        return mapping

    # ========================================================
    # Dictionary Serialization
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize this Material into a deterministic dictionary.

        Returns
        -------
        dict[str, object]
        """

        return {

            # ------------------------------------------------
            # Identity
            # ------------------------------------------------

            "material_id": self.material_id,

            "name": self.name,

            "short_name": self.short_name,

            "symbol": self.symbol,

            "chemical_formula":
                self.chemical_formula,

            "description":
                self.description,

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            "category":
                self.category.value,

            "material_class":
                self.material_class.value,

            "status":
                self.status.value,

            "maturity_level":
                self.maturity_level.value,

            "criticality":
                self.criticality.value,

            # ------------------------------------------------
            # Chemical Information
            # ------------------------------------------------

            "alloy_family":
                self.alloy_family,

            "composition":
                dict(self.composition),

            "uns_designation":
                self.uns_designation,

            "astm_designation":
                self.astm_designation,

            "ams_designation":
                self.ams_designation,

            "nasa_designation":
                self.nasa_designation,

            # ------------------------------------------------
            # Mechanical Properties
            # ------------------------------------------------

            "density":
                self.density,

            "youngs_modulus":
                self.youngs_modulus,

            "shear_modulus":
                self.shear_modulus,

            "bulk_modulus":
                self.bulk_modulus,

            "poisson_ratio":
                self.poisson_ratio,

            "yield_strength":
                self.yield_strength,

            "ultimate_tensile_strength":
                self.ultimate_tensile_strength,

            "compressive_strength":
                self.compressive_strength,

            "fatigue_strength":
                self.fatigue_strength,

            "fracture_toughness":
                self.fracture_toughness,

            "hardness":
                self.hardness,

            # ------------------------------------------------
            # Thermal Properties
            # ------------------------------------------------

            "melting_point":
                self.melting_point,

            "thermal_conductivity":
                self.thermal_conductivity,

            "specific_heat_capacity":
                self.specific_heat_capacity,

            "coefficient_thermal_expansion":
                self.coefficient_thermal_expansion,

            "emissivity":
                self.emissivity,

            # ------------------------------------------------
            # Electrical Properties
            # ------------------------------------------------

            "electrical_conductivity":
                self.electrical_conductivity,

            "electrical_resistivity":
                self.electrical_resistivity,

            # ------------------------------------------------
            # Manufacturing
            # ------------------------------------------------

            "additive_manufacturing":
                self.additive_manufacturing,

            "machinable":
                self.machinable,

            "weldable":
                self.weldable,

            "heat_treatable":
                self.heat_treatable,

            "manufacturing_processes":
                list(
                    self.manufacturing_processes
                ),

            # ------------------------------------------------
            # Compatibility
            # ------------------------------------------------

            "compatible_propellants":
                list(
                    self.compatible_propellants
                ),

            "corrosion_notes":
                self.corrosion_notes,

            "oxidation_behavior":
                self.oxidation_behavior,

            "cryogenic_capable":
                self.cryogenic_capable,

            "vacuum_compatible":
                self.vacuum_compatible,

            # ------------------------------------------------
            # Knowledge Metadata
            # ------------------------------------------------

            "aliases":
                list(
                    self.aliases
                ),

            "common_names":
                list(
                    self.common_names
                ),

            "search_keywords":
                list(
                    self.search_keywords
                ),

            "tags":
                list(
                    self.tags
                ),

            # ------------------------------------------------
            # Relationships
            # ------------------------------------------------

            "related_variable_ids":
                list(
                    self.related_variable_ids
                ),

            "related_equation_ids":
                list(
                    self.related_equation_ids
                ),

            "related_constant_ids":
                list(
                    self.related_constant_ids
                ),

            "related_unit_ids":
                list(
                    self.related_unit_ids
                ),

            "related_dimension_ids":
                list(
                    self.related_dimension_ids
                ),

            "related_subsystem_ids":
                list(
                    self.related_subsystem_ids
                ),

            "related_engineering_domain_ids":
                list(
                    self.related_engineering_domain_ids
                ),

            "related_simulation_ids":
                list(
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

            "version":
                self.version,

            "status_note":
                self.status_note,

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

            "created_by":
                self.created_by,

            "approved_by":
                self.approved_by,

            "revision":
                self.revision,

            "repository_path":
                self.repository_path,

            "repository_identifier":
                self.repository_identifier,    
        
            # ------------------------------------------------
            # Knowledge Graph
            # ------------------------------------------------

            "ontology_uri":
                self.ontology_uri,

            "graph_node_id":
                self.graph_node_id,

            "symbolic_identifier":
                self.symbolic_identifier,

            "embedding_identifier":
                self.embedding_identifier,

            "export_identifier":
                self.export_identifier,

            "llm_summary":
                self.llm_summary,

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
            # Future Extensions
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
    ) -> "Material":
        """
        Reconstruct a Material from its serialized
        dictionary representation.
        """

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "data must be a dictionary."
            )

        # ------------------------------------------------
        # Nested Objects
        # ------------------------------------------------

        source_reference = (
            cls._deserialize_reference(
                data.get(
                    "source_reference"
                )
            )
        )

        source_document = (
            cls._deserialize_document(
                data.get(
                    "source_document"
                )
            )
        )

        # ------------------------------------------------
        # Datetime Reconstruction
        # ------------------------------------------------

        _created_ts = data.get(
            "created_timestamp"
        )

        created_timestamp = (
            cls._deserialize_datetime(
                _created_ts
                if isinstance(
                    _created_ts,
                    str,
                )
                else None
            )
        )

        _modified_ts = data.get(
            "modified_timestamp"
        )

        modified_timestamp = (
            cls._deserialize_datetime(
                _modified_ts
                if isinstance(
                    _modified_ts,
                    str,
                )
                else None
            )
        )

        _approved_ts = data.get(
            "approved_timestamp"
        )

        approved_timestamp = (
            cls._deserialize_datetime(
                _approved_ts
                if isinstance(
                    _approved_ts,
                    str,
                )
                else None
            )
        )

        # ------------------------------------------------
        # Mapping Reconstruction
        # ------------------------------------------------

        custom_metadata = (
            cls._deserialize_mapping(
                data.get(
                    "custom_metadata"
                )
            )
        )

        extension_fields = (
            cls._deserialize_mapping(
                data.get(
                    "extension_fields"
                )
            )
        )

        raw_composition = data.get(
            "composition"
        )

        if raw_composition is None:

            composition: dict[
                str,
                float,
            ] = {}

        elif isinstance(
            raw_composition,
            dict,
        ):

            composition = {}

            for key, value in raw_composition.items():

                if not isinstance(
                    key,
                    str,
                ):
                    raise TypeError(
                        "composition keys must be strings."
                    )

                if not isinstance(
                    value,
                    (
                        int,
                        float,
                    ),
                ):
                    raise TypeError(
                        "composition values must be numeric."
                    )

                composition[key] = float(
                    value
                )

        else:
            raise TypeError(
                "composition must be a dictionary."
            )

        # ------------------------------------------------
        # Enum Reconstruction
        # ------------------------------------------------

        category = MaterialCategory(
            str(
                data[
                    "category"
                ]
            )
        )

        material_class = (
            MaterialClass(
                str(
                    data[
                        "material_class"
                    ]
                )
            )
        )

        status = MaterialStatus(
            str(
                data[
                    "status"
                ]
            )
        )

        maturity_level = (
            MaterialMaturityLevel(
                str(
                    data[
                        "maturity_level"
                    ]
                )
            )
        )

        criticality = (
            MaterialCriticality(
                str(
                    data[
                        "criticality"
                    ]
                )
            )
        )

        # ------------------------------------------------
        # Section 2A
        # Identity
        # ------------------------------------------------

        if "material_id" not in data:
            raise KeyError("material_id is a required field.")

        raw_material_id = data["material_id"]

        if not isinstance(raw_material_id, str):
            raise TypeError(
                "material_id must be a string."
            )

        material_id = raw_material_id

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

        raw_chemical_formula = data.get(
            "chemical_formula"
        )

        if raw_chemical_formula is None:

            chemical_formula = None

        elif isinstance(
            raw_chemical_formula,
            str,
        ):

            chemical_formula = (
                raw_chemical_formula
            )

        else:
            raise TypeError(
                "chemical_formula must be a string or None."
            )

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

        # ------------------------------------------------
        # Section 2B
        # Chemical Information
        # ------------------------------------------------

        raw_alloy_family = data.get(
            "alloy_family"
        )

        if raw_alloy_family is None:

            alloy_family = None

        elif isinstance(
            raw_alloy_family,
            str,
        ):

            alloy_family = (
                raw_alloy_family
            )

        else:
            raise TypeError(
                "alloy_family must be a string or None."
            )

        #
        # composition was already reconstructed
        # in Section 1 and is reused here.
        #

        raw_uns_designation = data.get(
            "uns_designation"
        )

        if raw_uns_designation is None:

            uns_designation = None

        elif isinstance(
            raw_uns_designation,
            str,
        ):

            uns_designation = (
                raw_uns_designation
            )

        else:
            raise TypeError(
                "uns_designation must be a string or None."
            )

        raw_astm_designation = data.get(
            "astm_designation"
        )

        if raw_astm_designation is None:

            astm_designation = None

        elif isinstance(
            raw_astm_designation,
            str,
        ):

            astm_designation = (
                raw_astm_designation
            )

        else:
            raise TypeError(
                "astm_designation must be a string or None."
            )

        raw_ams_designation = data.get(
            "ams_designation"
        )

        if raw_ams_designation is None:

            ams_designation = None

        elif isinstance(
            raw_ams_designation,
            str,
        ):

            ams_designation = (
                raw_ams_designation
            )

        else:
            raise TypeError(
                "ams_designation must be a string or None."
            )

        raw_nasa_designation = data.get(
            "nasa_designation"
        )

        if raw_nasa_designation is None:

            nasa_designation = None

        elif isinstance(
            raw_nasa_designation,
            str,
        ):

            nasa_designation = (
                raw_nasa_designation
            )

        else:
            raise TypeError(
                "nasa_designation must be a string or None."
            )

        # ------------------------------------------------
        # Section 2C
        # Mechanical Properties
        # ------------------------------------------------

        raw_density = data.get(
            "density"
        )

        if raw_density is None:

            density = None

        elif isinstance(
            raw_density,
            (
                int,
                float,
            ),
        ):

            density = float(
                raw_density
            )

        else:
            raise TypeError(
                "density must be numeric or None."
            )

        raw_youngs_modulus = data.get(
            "youngs_modulus"
        )

        if raw_youngs_modulus is None:

            youngs_modulus = None

        elif isinstance(
            raw_youngs_modulus,
            (
                int,
                float,
            ),
        ):

            youngs_modulus = float(
                raw_youngs_modulus
            )

        else:
            raise TypeError(
                "youngs_modulus must be numeric or None."
            )

        raw_shear_modulus = data.get(
            "shear_modulus"
        )

        if raw_shear_modulus is None:

            shear_modulus = None

        elif isinstance(
            raw_shear_modulus,
            (
                int,
                float,
            ),
        ):

            shear_modulus = float(
                raw_shear_modulus
            )

        else:
            raise TypeError(
                "shear_modulus must be numeric or None."
            )

        raw_bulk_modulus = data.get(
            "bulk_modulus"
        )

        if raw_bulk_modulus is None:

            bulk_modulus = None

        elif isinstance(
            raw_bulk_modulus,
            (
                int,
                float,
            ),
        ):

            bulk_modulus = float(
                raw_bulk_modulus
            )

        else:
            raise TypeError(
                "bulk_modulus must be numeric or None."
            )

        raw_poisson_ratio = data.get(
            "poisson_ratio"
        )

        if raw_poisson_ratio is None:

            poisson_ratio = None

        elif isinstance(
            raw_poisson_ratio,
            (
                int,
                float,
            ),
        ):

            poisson_ratio = float(
                raw_poisson_ratio
            )

        else:
            raise TypeError(
                "poisson_ratio must be numeric or None."
            )

        raw_yield_strength = data.get(
            "yield_strength"
        )

        if raw_yield_strength is None:

            yield_strength = None

        elif isinstance(
            raw_yield_strength,
            (
                int,
                float,
            ),
        ):

            yield_strength = float(
                raw_yield_strength
            )

        else:
            raise TypeError(
                "yield_strength must be numeric or None."
            )

        raw_ultimate_tensile_strength = data.get(
            "ultimate_tensile_strength"
        )

        if raw_ultimate_tensile_strength is None:

            ultimate_tensile_strength = None

        elif isinstance(
            raw_ultimate_tensile_strength,
            (
                int,
                float,
            ),
        ):

            ultimate_tensile_strength = float(
                raw_ultimate_tensile_strength
            )

        else:
            raise TypeError(
                "ultimate_tensile_strength must be numeric or None."
            )

        raw_compressive_strength = data.get(
            "compressive_strength"
        )

        if raw_compressive_strength is None:

            compressive_strength = None

        elif isinstance(
            raw_compressive_strength,
            (
                int,
                float,
            ),
        ):

            compressive_strength = float(
                raw_compressive_strength
            )

        else:
            raise TypeError(
                "compressive_strength must be numeric or None."
            )

        raw_fatigue_strength = data.get(
            "fatigue_strength"
        )

        if raw_fatigue_strength is None:

            fatigue_strength = None

        elif isinstance(
            raw_fatigue_strength,
            (
                int,
                float,
            ),
        ):

            fatigue_strength = float(
                raw_fatigue_strength
            )

        else:
            raise TypeError(
                "fatigue_strength must be numeric or None."
            )

        raw_fracture_toughness = data.get(
            "fracture_toughness"
        )

        if raw_fracture_toughness is None:

            fracture_toughness = None

        elif isinstance(
            raw_fracture_toughness,
            (
                int,
                float,
            ),
        ):

            fracture_toughness = float(
                raw_fracture_toughness
            )

        else:
            raise TypeError(
                "fracture_toughness must be numeric or None."
            )

        raw_hardness = data.get(
            "hardness"
        )

        if raw_hardness is None:

            hardness = None

        elif isinstance(
            raw_hardness,
            (
                int,
                float,
            ),
        ):

            hardness = float(
                raw_hardness
            )

        else:
            raise TypeError(
                "hardness must be numeric or None."
            ) 

        # ------------------------------------------------
        # Section 2D
        # Thermal Properties
        # ------------------------------------------------

        raw_melting_point = data.get(
            "melting_point"
        )

        if raw_melting_point is None:

            melting_point = None

        elif isinstance(
            raw_melting_point,
            (
                int,
                float,
            ),
        ):

            melting_point = float(
                raw_melting_point
            )

        else:
            raise TypeError(
                "melting_point must be numeric or None."
            )

        raw_thermal_conductivity = data.get(
            "thermal_conductivity"
        )

        if raw_thermal_conductivity is None:

            thermal_conductivity = None

        elif isinstance(
            raw_thermal_conductivity,
            (
                int,
                float,
            ),
        ):

            thermal_conductivity = float(
                raw_thermal_conductivity
            )

        else:
            raise TypeError(
                "thermal_conductivity must be numeric or None."
            )

        raw_specific_heat_capacity = data.get(
            "specific_heat_capacity"
        )

        if raw_specific_heat_capacity is None:

            specific_heat_capacity = None

        elif isinstance(
            raw_specific_heat_capacity,
            (
                int,
                float,
            ),
        ):

            specific_heat_capacity = float(
                raw_specific_heat_capacity
            )

        else:
            raise TypeError(
                "specific_heat_capacity must be numeric or None."
            )

        raw_coefficient_thermal_expansion = data.get(
            "coefficient_thermal_expansion"
        )

        if raw_coefficient_thermal_expansion is None:

            coefficient_thermal_expansion = None

        elif isinstance(
            raw_coefficient_thermal_expansion,
            (
                int,
                float,
            ),
        ):

            coefficient_thermal_expansion = float(
                raw_coefficient_thermal_expansion
            )

        else:
            raise TypeError(
                "coefficient_thermal_expansion must be numeric or None."
            )

        raw_emissivity = data.get(
            "emissivity"
        )

        if raw_emissivity is None:

            emissivity = None

        elif isinstance(
            raw_emissivity,
            (
                int,
                float,
            ),
        ):

            emissivity = float(
                raw_emissivity
            )

        else:
            raise TypeError(
                "emissivity must be numeric or None."
            )

        # ------------------------------------------------
        # Section 2E
        # Electrical Properties
        # ------------------------------------------------

        raw_electrical_conductivity = data.get(
            "electrical_conductivity"
        )

        if raw_electrical_conductivity is None:

            electrical_conductivity = None

        elif isinstance(
            raw_electrical_conductivity,
            (
                int,
                float,
            ),
        ):

            electrical_conductivity = float(
                raw_electrical_conductivity
            )

        else:
            raise TypeError(
                "electrical_conductivity must be numeric or None."
            )

        raw_electrical_resistivity = data.get(
            "electrical_resistivity"
        )

        if raw_electrical_resistivity is None:

            electrical_resistivity = None

        elif isinstance(
            raw_electrical_resistivity,
            (
                int,
                float,
            ),
        ):

            electrical_resistivity = float(
                raw_electrical_resistivity
            )

        else:
            raise TypeError(
                "electrical_resistivity must be numeric or None."
            )

        # ------------------------------------------------
        # Section 2F
        # Manufacturing
        # ------------------------------------------------

        raw_additive_manufacturing = data.get(
            "additive_manufacturing"
        )

        if raw_additive_manufacturing is None:

            additive_manufacturing = False

        elif isinstance(
            raw_additive_manufacturing,
            bool,
        ):

            additive_manufacturing = (
                raw_additive_manufacturing
            )

        else:
            raise TypeError(
                "additive_manufacturing must be a bool or None."
            )

        raw_machinable = data.get(
            "machinable"
        )

        if raw_machinable is None:

            machinable = False

        elif isinstance(
            raw_machinable,
            bool,
        ):

            machinable = raw_machinable

        else:
            raise TypeError(
                "machinable must be a bool or None."
            )

        raw_weldable = data.get(
            "weldable"
        )

        if raw_weldable is None:

            weldable = False

        elif isinstance(
            raw_weldable,
            bool,
        ):

            weldable = raw_weldable

        else:
            raise TypeError(
                "weldable must be a bool or None."
            )

        raw_heat_treatable = data.get(
            "heat_treatable"
        )

        if raw_heat_treatable is None:

            heat_treatable = False

        elif isinstance(
            raw_heat_treatable,
            bool,
        ):

            heat_treatable = (
                raw_heat_treatable
            )

        else:
            raise TypeError(
                "heat_treatable must be a bool or None."
            )

        raw_manufacturing_processes = data.get(
            "manufacturing_processes"
        )

        if raw_manufacturing_processes is None:

            manufacturing_processes: tuple[str, ...] = ()

        elif isinstance(
            raw_manufacturing_processes,
            (
                list,
                tuple,
            ),
        ):

            manufacturing_processes = tuple(
                str(item)
                for item in raw_manufacturing_processes
            )

        else:
            raise TypeError(
                "manufacturing_processes must be a list or tuple."
            ) 

        # ------------------------------------------------
        # Section 2G
        # Compatibility
        # ------------------------------------------------

        raw_compatible_propellants = data.get(
            "compatible_propellants"
        )

        if raw_compatible_propellants is None:

            compatible_propellants: tuple[str, ...] = ()

        elif isinstance(
            raw_compatible_propellants,
            (
                list,
                tuple,
            ),
        ):

            compatible_propellants = tuple(
                str(item)
                for item in raw_compatible_propellants
            )

        else:
            raise TypeError(
                "compatible_propellants must be a list or tuple."
            )

        raw_corrosion_notes = data.get(
            "corrosion_notes"
        )

        if raw_corrosion_notes is None:

            corrosion_notes = None

        elif isinstance(
            raw_corrosion_notes,
            str,
        ):

            corrosion_notes = raw_corrosion_notes

        else:
            raise TypeError(
                "corrosion_notes must be a string or None."
            )

        raw_oxidation_behavior = data.get(
            "oxidation_behavior"
        )

        if raw_oxidation_behavior is None:

            oxidation_behavior = None

        elif isinstance(
            raw_oxidation_behavior,
            str,
        ):

            oxidation_behavior = (
                raw_oxidation_behavior
            )

        else:
            raise TypeError(
                "oxidation_behavior must be a string or None."
            )

        raw_cryogenic_capable = data.get(
            "cryogenic_capable"
        )

        if raw_cryogenic_capable is None:

            cryogenic_capable = False

        elif isinstance(
            raw_cryogenic_capable,
            bool,
        ):

            cryogenic_capable = (
                raw_cryogenic_capable
            )

        else:
            raise TypeError(
                "cryogenic_capable must be a bool or None."
            )

        raw_vacuum_compatible = data.get(
            "vacuum_compatible"
        )

        if raw_vacuum_compatible is None:

            vacuum_compatible = False

        elif isinstance(
            raw_vacuum_compatible,
            bool,
        ):

            vacuum_compatible = (
                raw_vacuum_compatible
            )

        else:
            raise TypeError(
                "vacuum_compatible must be a bool or None."
            )

        # ------------------------------------------------
        # Section 2H
        # Knowledge Metadata
        # ------------------------------------------------

        raw_aliases = data.get(
            "aliases"
        )

        if raw_aliases is None:

            aliases: tuple[str, ...] = ()

        elif isinstance(
            raw_aliases,
            (
                list,
                tuple,
            ),
        ):

            aliases = tuple(
                str(item)
                for item in raw_aliases
            )

        else:
            raise TypeError(
                "aliases must be a list or tuple."
            )

        raw_common_names = data.get(
            "common_names"
        )

        if raw_common_names is None:

            common_names: tuple[str, ...] = ()

        elif isinstance(
            raw_common_names,
            (
                list,
                tuple,
            ),
        ):

            common_names = tuple(
                str(item)
                for item in raw_common_names
            )

        else:
            raise TypeError(
                "common_names must be a list or tuple."
            )

        raw_search_keywords = data.get(
            "search_keywords"
        )

        if raw_search_keywords is None:

            search_keywords: tuple[str, ...] = ()

        elif isinstance(
            raw_search_keywords,
            (
                list,
                tuple,
            ),
        ):

            search_keywords = tuple(
                str(item)
                for item in raw_search_keywords
            )

        else:
            raise TypeError(
                "search_keywords must be a list or tuple."
            )

        raw_tags = data.get(
            "tags"
        )

        if raw_tags is None:

            tags: tuple[str, ...] = ()

        elif isinstance(
            raw_tags,
            (
                list,
                tuple,
            ),
        ):

            tags = tuple(
                str(item)
                for item in raw_tags
            )

        else:
            raise TypeError(
                "tags must be a list or tuple."
            )

        # ------------------------------------------------
        # Section 2I
        # Relationships
        # ------------------------------------------------

        raw_related_variable_ids = data.get(
            "related_variable_ids"
        )

        if raw_related_variable_ids is None:

            related_variable_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_variable_ids,
            (
                list,
                tuple,
            ),
        ):

            related_variable_ids = tuple(
                str(item)
                for item in raw_related_variable_ids
            )

        else:
            raise TypeError(
                "related_variable_ids must be a list or tuple."
            )

        raw_related_equation_ids = data.get(
            "related_equation_ids"
        )

        if raw_related_equation_ids is None:

            related_equation_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_equation_ids,
            (
                list,
                tuple,
            ),
        ):

            related_equation_ids = tuple(
                str(item)
                for item in raw_related_equation_ids
            )

        else:
            raise TypeError(
                "related_equation_ids must be a list or tuple."
            )

        raw_related_constant_ids = data.get(
            "related_constant_ids"
        )

        if raw_related_constant_ids is None:

            related_constant_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_constant_ids,
            (
                list,
                tuple,
            ),
        ):

            related_constant_ids = tuple(
                str(item)
                for item in raw_related_constant_ids
            )

        else:
            raise TypeError(
                "related_constant_ids must be a list or tuple."
            )

        raw_related_unit_ids = data.get(
            "related_unit_ids"
        )

        if raw_related_unit_ids is None:

            related_unit_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_unit_ids,
            (
                list,
                tuple,
            ),
        ):

            related_unit_ids = tuple(
                str(item)
                for item in raw_related_unit_ids
            )

        else:
            raise TypeError(
                "related_unit_ids must be a list or tuple."
            )

        raw_related_dimension_ids = data.get(
            "related_dimension_ids"
        )

        if raw_related_dimension_ids is None:

            related_dimension_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_dimension_ids,
            (
                list,
                tuple,
            ),
        ):

            related_dimension_ids = tuple(
                str(item)
                for item in raw_related_dimension_ids
            )

        else:
            raise TypeError(
                "related_dimension_ids must be a list or tuple."
            )

        raw_related_subsystem_ids = data.get(
            "related_subsystem_ids"
        )

        if raw_related_subsystem_ids is None:

            related_subsystem_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_subsystem_ids,
            (
                list,
                tuple,
            ),
        ):

            related_subsystem_ids = tuple(
                str(item)
                for item in raw_related_subsystem_ids
            )

        else:
            raise TypeError(
                "related_subsystem_ids must be a list or tuple."
            )

        raw_related_engineering_domain_ids = data.get(
            "related_engineering_domain_ids"
        )

        if raw_related_engineering_domain_ids is None:

            related_engineering_domain_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_engineering_domain_ids,
            (
                list,
                tuple,
            ),
        ):

            related_engineering_domain_ids = tuple(
                str(item)
                for item in raw_related_engineering_domain_ids
            )

        else:
            raise TypeError(
                "related_engineering_domain_ids must be a list or tuple."
            )

        raw_related_simulation_ids = data.get(
            "related_simulation_ids"
        )

        if raw_related_simulation_ids is None:

            related_simulation_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_related_simulation_ids,
            (
                list,
                tuple,
            ),
        ):

            related_simulation_ids = tuple(
                str(item)
                for item in raw_related_simulation_ids
            )

        else:
            raise TypeError(
                "related_simulation_ids must be a list or tuple."
            )

        # ------------------------------------------------
        # Section 2J
        # Repository Metadata
        # ------------------------------------------------

        raw_version = data.get(
            "version"
        )

        if not isinstance(
            raw_version,
            str,
        ):
            raise TypeError(
                "version must be a string."
            )

        version = raw_version

        raw_status_note = data.get(
            "status_note"
        )

        if not isinstance(
            raw_status_note,
            str,
        ):
            raise TypeError(
                "status_note must be a string."
            )

        status_note = raw_status_note

        #
        # created_timestamp
        # modified_timestamp
        # approved_timestamp
        #
        # Already reconstructed in Section 1.
        #

        raw_created_by = data.get(
            "created_by"
        )

        if not isinstance(
            raw_created_by,
            str,
        ):
            raise TypeError(
                "created_by must be a string."
            )

        created_by = raw_created_by

        raw_approved_by = data.get(
            "approved_by"
        )

        if raw_approved_by is None:

            approved_by = None

        elif isinstance(
            raw_approved_by,
            str,
        ):

            approved_by = raw_approved_by

        else:
            raise TypeError(
                "approved_by must be a string or None."
            )

        raw_revision = data.get(
            "revision"
        )

        if not isinstance(
            raw_revision,
            int,
        ):
            raise TypeError(
                "revision must be an integer."
            )

        revision = raw_revision

        raw_repository_path = data.get(
            "repository_path"
        )

        if raw_repository_path is None:

            repository_path = None

        elif isinstance(
            raw_repository_path,
            str,
        ):

            repository_path = (
                raw_repository_path
            )

        else:
            raise TypeError(
                "repository_path must be a string or None."
            )

        raw_repository_identifier = data.get(
            "repository_identifier"
        )

        if raw_repository_identifier is None:

            repository_identifier = None

        elif isinstance(
            raw_repository_identifier,
            str,
        ):

            repository_identifier = (
                raw_repository_identifier
            )

        else:
            raise TypeError(
                "repository_identifier must be a string or None."
            )

        # ------------------------------------------------
        # Section 2K
        # Knowledge Graph
        # ------------------------------------------------

        raw_ontology_uri = data.get(
            "ontology_uri"
        )

        if raw_ontology_uri is None:

            ontology_uri = None

        elif isinstance(
            raw_ontology_uri,
            str,
        ):

            ontology_uri = (
                raw_ontology_uri
            )

        else:
            raise TypeError(
                "ontology_uri must be a string or None."
            )

        raw_graph_node_id = data.get(
            "graph_node_id"
        )

        if raw_graph_node_id is None:

            graph_node_id = None

        elif isinstance(
            raw_graph_node_id,
            str,
        ):

            graph_node_id = (
                raw_graph_node_id
            )

        else:
            raise TypeError(
                "graph_node_id must be a string or None."
            )

        raw_symbolic_identifier = data.get(
            "symbolic_identifier"
        )

        if raw_symbolic_identifier is None:

            symbolic_identifier = None

        elif isinstance(
            raw_symbolic_identifier,
            str,
        ):

            symbolic_identifier = (
                raw_symbolic_identifier
            )

        else:
            raise TypeError(
                "symbolic_identifier must be a string or None."
            )

        raw_embedding_identifier = data.get(
            "embedding_identifier"
        )

        if raw_embedding_identifier is None:

            embedding_identifier = None

        elif isinstance(
            raw_embedding_identifier,
            str,
        ):

            embedding_identifier = (
                raw_embedding_identifier
            )

        else:
            raise TypeError(
                "embedding_identifier must be a string or None."
            )

        raw_export_identifier = data.get(
            "export_identifier"
        )

        if raw_export_identifier is None:

            export_identifier = None

        elif isinstance(
            raw_export_identifier,
            str,
        ):

            export_identifier = (
                raw_export_identifier
            )

        else:
            raise TypeError(
                "export_identifier must be a string or None."
            )

        raw_llm_summary = data.get(
            "llm_summary"
        )

        if raw_llm_summary is None:

            llm_summary = None

        elif isinstance(
            raw_llm_summary,
            str,
        ):

            llm_summary = (
                raw_llm_summary
            )

        else:
            raise TypeError(
                "llm_summary must be a string or None."
            )

        # ------------------------------------------------
        # Section 2L
        # Engineering Ownership
        # ------------------------------------------------

        raw_responsible_team = data.get(
            "responsible_team"
        )

        if raw_responsible_team is None:

            responsible_team = None

        elif isinstance(
            raw_responsible_team,
            str,
        ):

            responsible_team = (
                raw_responsible_team
            )

        else:
            raise TypeError(
                "responsible_team must be a string or None."
            )

        raw_responsible_engineer = data.get(
            "responsible_engineer"
        )

        if raw_responsible_engineer is None:

            responsible_engineer = None

        elif isinstance(
            raw_responsible_engineer,
            str,
        ):

            responsible_engineer = (
                raw_responsible_engineer
            )

        else:
            raise TypeError(
                "responsible_engineer must be a string or None."
            )

        raw_owning_organization = data.get(
            "owning_organization"
        )

        if raw_owning_organization is None:

            owning_organization = None

        elif isinstance(
            raw_owning_organization,
            str,
        ):

            owning_organization = (
                raw_owning_organization
            )

        else:
            raise TypeError(
                "owning_organization must be a string or None."
            )

        raw_project_name = data.get(
            "project_name"
        )

        if raw_project_name is None:

            project_name = None

        elif isinstance(
            raw_project_name,
            str,
        ):

            project_name = (
                raw_project_name
            )

        else:
            raise TypeError(
                "project_name must be a string or None."
            )

        raw_program_name = data.get(
            "program_name"
        )

        if raw_program_name is None:

            program_name = None

        elif isinstance(
            raw_program_name,
            str,
        ):

            program_name = (
                raw_program_name
            )

        else:
            raise TypeError(
                "program_name must be a string or None."
            )

        
        # ------------------------------------------------
        # Section 2M
        # Verification & Validation
        # ------------------------------------------------

        raw_verification_status = data.get(
            "verification_status"
        )

        if raw_verification_status is None:

            verification_status = None

        elif isinstance(
            raw_verification_status,
            str,
        ):

            verification_status = (
                raw_verification_status
            )

        else:
            raise TypeError(
                "verification_status must be a string or None."
            )

        raw_validation_status = data.get(
            "validation_status"
        )

        if raw_validation_status is None:

            validation_status = None

        elif isinstance(
            raw_validation_status,
            str,
        ):

            validation_status = (
                raw_validation_status
            )

        else:
            raise TypeError(
                "validation_status must be a string or None."
            )

        raw_verification_method = data.get(
            "verification_method"
        )

        if raw_verification_method is None:

            verification_method = None

        elif isinstance(
            raw_verification_method,
            str,
        ):

            verification_method = (
                raw_verification_method
            )

        else:
            raise TypeError(
                "verification_method must be a string or None."
            )

        raw_verification_document_ids = data.get(
            "verification_document_ids"
        )

        if raw_verification_document_ids is None:

            verification_document_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_verification_document_ids,
            (
                list,
                tuple,
            ),
        ):

            verification_document_ids = tuple(
                str(item)
                for item in raw_verification_document_ids
            )

        else:
            raise TypeError(
                "verification_document_ids must be a list or tuple."
            )

        raw_test_case_ids = data.get(
            "test_case_ids"
        )

        if raw_test_case_ids is None:

            test_case_ids: tuple[str, ...] = ()

        elif isinstance(
            raw_test_case_ids,
            (
                list,
                tuple,
            ),
        ):

            test_case_ids = tuple(
                str(item)
                for item in raw_test_case_ids
            )

        else:
            raise TypeError(
                "test_case_ids must be a list or tuple."
            )

        # ------------------------------------------------
        # Section 2N
        # AI Metadata
        # ------------------------------------------------

        raw_ai_summary = data.get(
            "ai_summary"
        )

        if raw_ai_summary is None:

            ai_summary = None

        elif isinstance(
            raw_ai_summary,
            str,
        ):

            ai_summary = (
                raw_ai_summary
            )

        else:
            raise TypeError(
                "ai_summary must be a string or None."
            )

        raw_ai_embedding_identifier = data.get(
            "ai_embedding_identifier"
        )

        if raw_ai_embedding_identifier is None:

            ai_embedding_identifier = None

        elif isinstance(
            raw_ai_embedding_identifier,
            str,
        ):

            ai_embedding_identifier = (
                raw_ai_embedding_identifier
            )

        else:
            raise TypeError(
                "ai_embedding_identifier must be a string or None."
            )

        raw_ai_vector_database_id = data.get(
            "ai_vector_database_id"
        )

        if raw_ai_vector_database_id is None:

            ai_vector_database_id = None

        elif isinstance(
            raw_ai_vector_database_id,
            str,
        ):

            ai_vector_database_id = (
                raw_ai_vector_database_id
            )

        else:
            raise TypeError(
                "ai_vector_database_id must be a string or None."
            )

        raw_llm_context_identifier = data.get(
            "llm_context_identifier"
        )

        if raw_llm_context_identifier is None:

            llm_context_identifier = None

        elif isinstance(
            raw_llm_context_identifier,
            str,
        ):

            llm_context_identifier = (
                raw_llm_context_identifier
            )

        else:
            raise TypeError(
                "llm_context_identifier must be a string or None."
            )

        raw_symbolic_model_identifier = data.get(
            "symbolic_model_identifier"
        )

        if raw_symbolic_model_identifier is None:

            symbolic_model_identifier = None

        elif isinstance(
            raw_symbolic_model_identifier,
            str,
        ):

            symbolic_model_identifier = (
                raw_symbolic_model_identifier
            )

        else:
            raise TypeError(
                "symbolic_model_identifier must be a string or None."
            )

        # ------------------------------------------------
        # Section 2O
        # Future Extensions
        # ------------------------------------------------

        #
        # custom_metadata and extension_fields were
        # reconstructed and validated in Section 1.
        #
        # Normalize them here into strongly typed local
        # variables for the constructor.
        #

        if custom_metadata is None:

            custom_metadata_typed: Mapping[
                str,
                object,
            ] | None = None

        else:

            custom_metadata_typed = (
                custom_metadata
            )

        if extension_fields is None:

            extension_fields_typed: Mapping[
                str,
                object,
            ] | None = None

        else:

            extension_fields_typed = (
                extension_fields
            )

        # ------------------------------------------------
        # Section 3
        # Construct Material
        # ------------------------------------------------

        return cls(

            # ================================================
            # Identity
            # ================================================

            material_id=material_id,

            name=name,

            short_name=short_name,

            symbol=symbol,

            chemical_formula=chemical_formula,

            description=description,

            # ================================================
            # Classification
            # ================================================

            category=category,

            material_class=material_class,

            status=status,

            maturity_level=maturity_level,

            criticality=criticality,

            # ================================================
            # Chemical Information
            # ================================================

            alloy_family=alloy_family,

            composition=composition,

            uns_designation=uns_designation,

            astm_designation=astm_designation,

            ams_designation=ams_designation,

            nasa_designation=nasa_designation,

            # ================================================
            # Mechanical Properties
            # ================================================

            density=density,

            youngs_modulus=youngs_modulus,

            shear_modulus=shear_modulus,

            bulk_modulus=bulk_modulus,

            poisson_ratio=poisson_ratio,

            yield_strength=yield_strength,

            ultimate_tensile_strength=ultimate_tensile_strength,

            compressive_strength=compressive_strength,

            fatigue_strength=fatigue_strength,

            fracture_toughness=fracture_toughness,

            hardness=hardness,

            # ================================================
            # Thermal Properties
            # ================================================

            melting_point=melting_point,

            thermal_conductivity=thermal_conductivity,

            specific_heat_capacity=specific_heat_capacity,

            coefficient_thermal_expansion=coefficient_thermal_expansion,

            emissivity=emissivity,

            # ================================================
            # Electrical Properties
            # ================================================

            electrical_conductivity=electrical_conductivity,

            electrical_resistivity=electrical_resistivity,

            # ================================================
            # Manufacturing
            # ================================================

            additive_manufacturing=additive_manufacturing,

            machinable=machinable,

            weldable=weldable,

            heat_treatable=heat_treatable,

            manufacturing_processes=manufacturing_processes,

            # ================================================
            # Compatibility
            # ================================================

            compatible_propellants=compatible_propellants,

            corrosion_notes=corrosion_notes,

            oxidation_behavior=oxidation_behavior,

            cryogenic_capable=cryogenic_capable,

            vacuum_compatible=vacuum_compatible,

            # ================================================
            # Knowledge Metadata
            # ================================================

            aliases=aliases,

            common_names=common_names,

            search_keywords=search_keywords,

            tags=tags,

            # ================================================
            # Relationships
            # ================================================

            related_variable_ids=related_variable_ids,

            related_equation_ids=related_equation_ids,

            related_constant_ids=related_constant_ids,

            related_unit_ids=related_unit_ids,

            related_dimension_ids=related_dimension_ids,

            related_subsystem_ids=related_subsystem_ids,

            related_engineering_domain_ids=related_engineering_domain_ids,

            related_simulation_ids=related_simulation_ids,

            # ================================================
            # Documentation
            # ================================================

            source_reference=source_reference,

            source_document=source_document,

            # ================================================
            # Repository Metadata
            # ================================================

            version=version,

            status_note=status_note,

            created_timestamp=created_timestamp,

            modified_timestamp=modified_timestamp,

            approved_timestamp=approved_timestamp,

            created_by=created_by,

            approved_by=approved_by,

            revision=revision,

            repository_path=repository_path,

            repository_identifier=repository_identifier,

            # ================================================
            # Knowledge Graph
            # ================================================

            ontology_uri=ontology_uri,

            graph_node_id=graph_node_id,

            symbolic_identifier=symbolic_identifier,

            embedding_identifier=embedding_identifier,

            export_identifier=export_identifier,

            llm_summary=llm_summary,

            # ================================================
            # Engineering Ownership
            # ================================================

            responsible_team=responsible_team,

            responsible_engineer=responsible_engineer,

            owning_organization=owning_organization,

            project_name=project_name,

            program_name=program_name,

            # ================================================
            # Verification & Validation
            # ================================================

            verification_status=verification_status,

            validation_status=validation_status,

            verification_method=verification_method,

            verification_document_ids=verification_document_ids,

            test_case_ids=test_case_ids,

            # ================================================
            # AI Metadata
            # ================================================

            ai_summary=ai_summary,

            ai_embedding_identifier=ai_embedding_identifier,

            ai_vector_database_id=ai_vector_database_id,

            llm_context_identifier=llm_context_identifier,

            symbolic_model_identifier=symbolic_model_identifier,

            # ================================================
            # Future Extensions
            # ================================================

            custom_metadata=custom_metadata_typed,

            extension_fields=extension_fields_typed,
        ) 

    # ========================================================
    # Convenience Methods
    # ========================================================

    def copy(
        self,
    ) -> "Material":
        """
        Return an immutable copy of this Material.

        Returns
        -------
        Material
        """

        return self.from_dict(
            self.to_dict()
        )

    def serialize(
        self,
    ) -> dict[str, object]:
        """
        Serialize this Material.

        This is a convenience wrapper around
        :meth:`to_dict`.

        Returns
        -------
        dict[str, object]
            Serialized representation of this Material.
        """

        return self.to_dict()
    
    @classmethod
    def deserialize(
        cls,
        data: dict[str, object],
    ) -> "Material":
        """
        Deserialize a Material.

        This is a convenience wrapper around
        :meth:`from_dict`.

        Parameters
        ----------
        data : dict[str, object]
            Serialized Material representation.

        Returns
        -------
        Material
            Deserialized Material instance.
        """

        return cls.from_dict(
            data
        )

    def __iter__(
        self,
    ):
        """
        Iterate over the serialized Material fields.

        Returns
        -------
        Iterator[tuple[str, object]]
            Iterator over serialized key-value pairs.
        """

        yield from self.to_dict().items()

    def __len__(
        self,
    ) -> int:
        """
        Return the number of serialized Material fields.

        Returns
        -------
        int
            Number of serialized fields.
        """

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
        Return the preferred display name for this Material.

        Returns
        -------
        str
            Preferred display name.
        """

        if self.short_name:

            return self.short_name

        return self.name

    def matches_alias(
        self,
        alias: str,
    ) -> bool:
        """
        Determine whether the supplied alias matches one of
        this Material's aliases.

        Parameters
        ----------
        alias : str
            Alias to search for.

        Returns
        -------
        bool
            True if the alias exists; otherwise False.
        """

        normalized_alias = (
            alias.strip()
            .casefold()
        )

        return any(
            item.casefold() == normalized_alias
            for item in self.aliases
        ) 

    def matches_keyword(
        self,
        keyword: str,
    ) -> bool:
        """
        Determine whether the supplied keyword matches one of
        this Material's search keywords.

        Parameters
        ----------
        keyword : str
            Keyword to search for.

        Returns
        -------
        bool
            True if the keyword exists; otherwise False.
        """

        normalized_keyword = (
            keyword.strip()
            .casefold()
        )

        return any(
            item.casefold() == normalized_keyword
            for item in self.search_keywords
        ) 

    def has_reference(
        self,
    ) -> bool:
        """
        Determine whether this Material has an associated
        Reference.

        Returns
        -------
        bool
            True if a Reference is associated with this
            Material; otherwise False.
        """

        return self.source_reference is not None 

    def has_document(
        self,
    ) -> bool:
        """
        Determine whether this Material has an associated
        Document.

        Returns
        -------
        bool
            True if a Document is associated with this
            Material; otherwise False.
        """

        return self.source_document is not None 
    
    def is_active(
        self,
    ) -> bool:
        """
        Determine whether this Material is active.

        Returns
        -------
        bool
            True if the Material status is ACTIVE;
            otherwise False.
        """

        return (
            self.status
            is MaterialStatus.ACTIVE
        )
    
    def is_verified(
        self,
    ) -> bool:
        """
        Determine whether this Material has been verified.

        Returns
        -------
        bool
            True if the verification status is
            "Verified" (case-insensitive); otherwise False.
        """

        if self.verification_status is None:

            return False

        return (
            self.verification_status.casefold()
            == "verified"
        )
    
    def is_cryogenic_capable(
        self,
    ) -> bool:
        """
        Determine whether this Material is suitable for
        cryogenic applications.

        Returns
        -------
        bool
            True if the Material is marked as cryogenic
            capable; otherwise False.
        """

        return self.cryogenic_capable is True
    
    def is_vacuum_compatible(
        self,
    ) -> bool:
        """
        Determine whether this Material is suitable for
        vacuum applications.

        Returns
        -------
        bool
            True if the Material is marked as vacuum
            compatible; otherwise False.
        """

        return self.vacuum_compatible is True
    
    # ========================================================
    # Analysis Methods
    # ========================================================

    def alias_count(
        self,
    ) -> int:
        """
        Return the number of aliases associated with this
        Material.

        Returns
        -------
        int
            Number of aliases.
        """

        return len(
            self.aliases
        )
    
    def keyword_count(
        self,
    ) -> int:
        """
        Return the number of search keywords associated
        with this Material.

        Returns
        -------
        int
            Number of search keywords.
        """

        return len(
            self.search_keywords
        )
    
    def tag_count(
        self,
    ) -> int:
        """
        Return the number of tags associated with this
        Material.

        Returns
        -------
        int
            Number of tags.
        """

        return len(
            self.tags
        )
    
    def manufacturing_process_count(
        self,
    ) -> int:
        """
        Return the number of manufacturing processes
        associated with this Material.

        Returns
        -------
        int
            Number of manufacturing processes.
        """

        return len(
            self.manufacturing_processes
        )
    
    def compatible_propellant_count(
        self,
    ) -> int:
        """
        Return the number of compatible propellants
        associated with this Material.

        Returns
        -------
        int
            Number of compatible propellants.
        """

        return len(
            self.compatible_propellants
        )

    def relationship_count(
        self,
    ) -> int:
        """
        Return the total number of relationships
        associated with this Material.

        Returns
        -------
        int
            Total number of relationship identifiers.
        """

        return (
            len(
                self.related_variable_ids
            )
            + len(
                self.related_equation_ids
            )
            + len(
                self.related_constant_ids
            )
            + len(
                self.related_unit_ids
            )
            + len(
                self.related_dimension_ids
            )
            + len(
                self.related_subsystem_ids
            )
            + len(
                self.related_engineering_domain_ids
            )
            + len(
                self.related_simulation_ids
            )
        )
    
    def verification_document_count(
        self,
    ) -> int:
        """
        Return the number of verification documents
        associated with this Material.

        Returns
        -------
        int
            Number of verification documents.
        """

        return len(
            self.verification_document_ids
        )

    def test_case_count(
        self,
    ) -> int:
        """
        Return the number of engineering test cases
        associated with this Material.

        Returns
        -------
        int
            Number of linked test cases.
        """

        return len(
            self.test_case_ids
        )
