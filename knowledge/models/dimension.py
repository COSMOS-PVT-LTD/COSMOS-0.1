"""
COSMOS Knowledge Foundation

Module
------
dimension.py

Purpose
-------
Defines the immutable Dimension model used throughout
the COSMOS Knowledge Foundation.

A Dimension represents the canonical physical dimension
of an engineering quantity independent of any specific
measurement unit.

Unlike the Unit model, which describes how a quantity is
measured (e.g. metre, kilogram, pascal), the Dimension
model describes the underlying physical nature of that
quantity through its SI base dimension exponents.

The Dimension model serves as the foundation for:

* Dimensional analysis
* Equation validation
* Unit consistency checking
* Engineering knowledge representation
* AI-assisted engineering reasoning
* Future symbolic mathematics
* Future Pint integration
* Future SymPy integration
* Future OpenMDAO integration

Design Goals
------------
* Immutable
* Thread-safe
* Fully typed
* Deterministic
* Repository-ready
* AI-ready
* Extensible
* Aerospace-grade

This module intentionally contains no numerical
algorithms, dimensional arithmetic, symbolic
manipulation, or repository logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from dataclasses import field
from datetime import datetime
from types import MappingProxyType
from typing import Mapping
from collections.abc import Iterator

from knowledge.models.document import Document
from knowledge.models.reference import Reference
from knowledge.models.variable import EngineeringDomain
# ============================================================
# Enumerations
# ============================================================


class DimensionCategory(Enum):
    """
    Classification of engineering dimensions.
    """

    BASE = "BASE"
    DERIVED = "DERIVED"
    DIMENSIONLESS = "DIMENSIONLESS"
    EMPIRICAL = "EMPIRICAL"
    CUSTOM = "CUSTOM"


class PhysicalQuantity(Enum):
    """
    Canonical engineering quantity represented by a
    physical dimension.
    """

    # --------------------------------------------------------
    # SI Base Quantities
    # --------------------------------------------------------

    LENGTH = "LENGTH"
    MASS = "MASS"
    TIME = "TIME"
    TEMPERATURE = "TEMPERATURE"
    ELECTRIC_CURRENT = "ELECTRIC_CURRENT"
    AMOUNT_OF_SUBSTANCE = "AMOUNT_OF_SUBSTANCE"
    LUMINOUS_INTENSITY = "LUMINOUS_INTENSITY"

    # --------------------------------------------------------
    # Geometric
    # --------------------------------------------------------

    AREA = "AREA"
    VOLUME = "VOLUME"
    ANGLE = "ANGLE"

    # --------------------------------------------------------
    # Kinematics
    # --------------------------------------------------------

    VELOCITY = "VELOCITY"
    ACCELERATION = "ACCELERATION"
    ANGULAR_VELOCITY = "ANGULAR_VELOCITY"

    # --------------------------------------------------------
    # Dynamics
    # --------------------------------------------------------

    FORCE = "FORCE"
    MOMENTUM = "MOMENTUM"
    PRESSURE = "PRESSURE"
    STRESS = "STRESS"
    STRAIN = "STRAIN"

    # --------------------------------------------------------
    # Thermodynamics
    # --------------------------------------------------------

    ENERGY = "ENERGY"
    POWER = "POWER"
    HEAT = "HEAT"
    HEAT_FLUX = "HEAT_FLUX"
    THERMAL_CONDUCTIVITY = "THERMAL_CONDUCTIVITY"
    SPECIFIC_HEAT = "SPECIFIC_HEAT"
    ENTHALPY = "ENTHALPY"
    ENTROPY = "ENTROPY"

    # --------------------------------------------------------
    # Fluid Mechanics
    # --------------------------------------------------------

    DENSITY = "DENSITY"
    DYNAMIC_VISCOSITY = "DYNAMIC_VISCOSITY"
    KINEMATIC_VISCOSITY = "KINEMATIC_VISCOSITY"
    MASS_FLOW_RATE = "MASS_FLOW_RATE"
    VOLUMETRIC_FLOW_RATE = "VOLUMETRIC_FLOW_RATE"

    # --------------------------------------------------------
    # General
    # --------------------------------------------------------

    FREQUENCY = "FREQUENCY"
    DIMENSIONLESS = "DIMENSIONLESS"

    OTHER = "OTHER"


class DimensionStatus(Enum):
    """
    Lifecycle status of the Dimension definition.
    """

    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    EXPERIMENTAL = "EXPERIMENTAL"

# ============================================================
# Dimension Model
# ============================================================


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Dimension:
    """
    Immutable representation of an engineering dimension.

    A Dimension describes the physical nature of an
    engineering quantity independently of the unit used
    to measure it.

    Examples
    --------
    Pressure

        kg·m⁻¹·s⁻²

    Velocity

        m·s⁻¹

    Density

        kg·m⁻³

    Notes
    -----
    This model forms the foundation of dimensional
    analysis throughout COSMOS.
    """

    # ========================================================
    # Identity
    # ========================================================

    dimension_id: str

    name: str

    symbol: str

    description: str

    # ========================================================
    # Classification
    # ========================================================

    category: DimensionCategory

    physical_quantity: PhysicalQuantity

    status: DimensionStatus = (
        DimensionStatus.ACTIVE
    )

    # ========================================================
    # SI Base Dimension Exponents
    # ========================================================

    length_exponent: int = 0

    mass_exponent: int = 0

    time_exponent: int = 0

    electric_current_exponent: int = 0

    temperature_exponent: int = 0

    amount_of_substance_exponent: int = 0

    luminous_intensity_exponent: int = 0

    # ========================================================
    # Canonical Representation
    # ========================================================

    canonical_expression: str = ""

    is_dimensionless: bool = False

    is_base_dimension: bool = False

    is_derived_dimension: bool = True   
    
    # ========================================================
    # Engineering Metadata
    # ========================================================

    engineering_domain: EngineeringDomain = (
        EngineeringDomain.GENERAL
    )

    engineering_disciplines: tuple[str, ...] = ()

    applicable_regimes: tuple[str, ...] = ()

    engineering_notes: str | None = None

    aliases: tuple[str, ...] = ()

    common_names: tuple[str, ...] = ()

    search_keywords: tuple[str, ...] = ()

    # ========================================================
    # Knowledge Foundation Metadata
    # ========================================================

    source_reference: Reference | None = None

    source_document: Document | None = None

    related_equation_ids: tuple[str, ...] = ()

    related_variable_ids: tuple[str, ...] = ()

    related_constant_ids: tuple[str, ...] = ()

    related_unit_ids: tuple[str, ...] = ()

    parent_dimension_id: str | None = None

    child_dimension_ids: tuple[str, ...] = ()

    # ========================================================
    # Repository Metadata
    # ========================================================

    version: str = "1.0"

    status_note: str | None = None

    tags: tuple[str, ...] = ()

    created_timestamp: datetime | None = None

    modified_timestamp: datetime | None = None

    created_by: str | None = None

    approved_by: str | None = None

    approved_timestamp: datetime | None = None

    # ========================================================
    # Governance Metadata
    # ========================================================

    verification_status: str | None = None

    approval_status: str | None = None

    approval_notes: str | None = None

    review_cycle: str | None = None

    lifecycle_stage: str | None = None

    is_verified: bool = False

    is_deprecated: bool = False

    replacement_dimension_id: str | None = None

    # ========================================================
    # Future Symbolic Mathematics Metadata
    # ========================================================

    symbolic_representation: str | None = None

    canonical_symbol: str | None = None

    symbolic_dimension_expression: str | None = None

    symbolic_dimension_vector: tuple[int, ...] = ()

    symbolic_metadata: Mapping[str, object] = field(
        default_factory=dict
    )

    # ========================================================
    # Future Extension Point
    # ========================================================

    dimension_vector: object | None = None     

    # ========================================================
    # Construction
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate the Dimension after construction.

        All validation is delegated to specialized
        private validator methods to maintain a clear
        separation of responsibilities.
        """

        self.validate()

    # ========================================================
    # Validation
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the complete Dimension object.

        Validation is delegated to specialized private
        validator methods to improve maintainability,
        readability, and unit-test isolation.

        Raises
        ------
        TypeError
            If a field has an invalid type.

        ValueError
            If a field contains an invalid value.
        """

        # ----------------------------------------------------
        # Core identity
        # ----------------------------------------------------

        self._validate_dimension_id()
        self._validate_name()
        self._validate_symbol()
        self._validate_description()

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        self._validate_category()
        self._validate_physical_quantity()
        self._validate_status()

        # ----------------------------------------------------
        # SI base exponents
        # ----------------------------------------------------

        self._validate_exponents()

        # ----------------------------------------------------
        # Canonical representation
        # ----------------------------------------------------

        self._validate_canonical_representation()

        # ----------------------------------------------------
        # Engineering metadata
        # ----------------------------------------------------

        self._validate_engineering_metadata()

        # ----------------------------------------------------
        # Knowledge Foundation metadata
        # ----------------------------------------------------

        self._validate_reference()
        self._validate_document()
        self._validate_relationships()

        # ----------------------------------------------------
        # Repository metadata
        # ----------------------------------------------------

        self._validate_repository_metadata()

        # ----------------------------------------------------
        # Governance metadata
        # ----------------------------------------------------

        self._validate_governance_metadata()

        # ----------------------------------------------------
        # Future symbolic mathematics
        # ----------------------------------------------------

        self._validate_symbolic_metadata()

    # ========================================================
    # Core Validators
    # ========================================================

    def _validate_dimension_id(self) -> None:
        """
        Validate the Dimension identifier.
        """

        if not isinstance(self.dimension_id, str):
            raise TypeError(
                "dimension_id must be a string."
            )

        if not self.dimension_id.strip():
            raise ValueError(
                "dimension_id cannot be blank."
            )

    def _validate_name(self) -> None:
        """
        Validate the Dimension name.
        """

        if not isinstance(self.name, str):
            raise TypeError(
                "name must be a string."
            )

        if not self.name.strip():
            raise ValueError(
                "name cannot be blank."
            )

    def _validate_symbol(self) -> None:
        """
        Validate the engineering symbol.
        """

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

    def _validate_description(self) -> None:
        """
        Validate the description.
        """

        if not isinstance(self.description, str):
            raise TypeError(
                "description must be a string."
            )

        if not self.description.strip():
            raise ValueError(
                "description cannot be blank."
            )

    def _validate_category(self) -> None:
        """
        Validate the Dimension category.
        """

        if not isinstance(
            self.category,
            DimensionCategory,
        ):
            raise TypeError(
                "category must be a DimensionCategory."
            )

    def _validate_physical_quantity(self) -> None:
        """
        Validate the physical quantity classification.
        """

        if not isinstance(
            self.physical_quantity,
            PhysicalQuantity,
        ):
            raise TypeError(
                "physical_quantity must be a PhysicalQuantity."
            )

    def _validate_status(self) -> None:
        """
        Validate the lifecycle status.
        """

        if not isinstance(
            self.status,
            DimensionStatus,
        ):
            raise TypeError(
                "status must be a DimensionStatus."
            )

    def _validate_exponents(self) -> None:
        """
        Validate all SI base-dimension exponents.
        """

        exponent_fields = (
            ("length_exponent", self.length_exponent),
            ("mass_exponent", self.mass_exponent),
            ("time_exponent", self.time_exponent),
            (
                "electric_current_exponent",
                self.electric_current_exponent,
            ),
            (
                "temperature_exponent",
                self.temperature_exponent,
            ),
            (
                "amount_of_substance_exponent",
                self.amount_of_substance_exponent,
            ),
            (
                "luminous_intensity_exponent",
                self.luminous_intensity_exponent,
            ),
        )

        for field_name, value in exponent_fields:
            if not isinstance(value, int):
                raise TypeError(
                    f"{field_name} must be an integer."
                )

    def _validate_canonical_representation(
        self,
    ) -> None:
        """
        Validate the canonical representation.
        """

        if not isinstance(
            self.canonical_expression,
            str,
        ):
            raise TypeError(
                "canonical_expression must be a string."
            )

        if not isinstance(
            self.is_dimensionless,
            bool,
        ):
            raise TypeError(
                "is_dimensionless must be a bool."
            )

        if not isinstance(
            self.is_base_dimension,
            bool,
        ):
            raise TypeError(
                "is_base_dimension must be a bool."
            )

        if not isinstance(
            self.is_derived_dimension,
            bool,
        ):
            raise TypeError(
                "is_derived_dimension must be a bool."
            )

        if (
            self.is_base_dimension
            and self.is_derived_dimension
        ):
            raise ValueError(
                "A Dimension cannot be both a base "
                "dimension and a derived dimension."
            )

        if (
            self.is_dimensionless
            and any(
                exponent != 0
                for exponent in (
                    self.length_exponent,
                    self.mass_exponent,
                    self.time_exponent,
                    self.electric_current_exponent,
                    self.temperature_exponent,
                    self.amount_of_substance_exponent,
                    self.luminous_intensity_exponent,
                )
            )
        ):
            raise ValueError(
                "A dimensionless Dimension must have "
                "all SI exponents equal to zero."
            )

    # ========================================================
    # Knowledge Foundation Validators
    # ========================================================

    def _validate_reference(self) -> None:
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
                "source_reference must be a Reference "
                "or None."
            )

    def _validate_document(self) -> None:
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
                "source_document must be a Document "
                "or None."
            )

    def _validate_relationships(self) -> None:
        """
        Validate relationships to other Knowledge
        Foundation entities.
        """

        relationship_fields = (
            (
                "related_equation_ids",
                self.related_equation_ids,
            ),
            (
                "related_variable_ids",
                self.related_variable_ids,
            ),
            (
                "related_constant_ids",
                self.related_constant_ids,
            ),
            (
                "related_unit_ids",
                self.related_unit_ids,
            ),
            (
                "child_dimension_ids",
                self.child_dimension_ids,
            ),
            (
                "engineering_disciplines",
                self.engineering_disciplines,
            ),
            (
                "applicable_regimes",
                self.applicable_regimes,
            ),
            (
                "aliases",
                self.aliases,
            ),
            (
                "common_names",
                self.common_names,
            ),
            (
                "search_keywords",
                self.search_keywords,
            ),
            (
                "tags",
                self.tags,
            ),
        )

        for field_name, values in relationship_fields:

            if not isinstance(values, tuple):
                raise TypeError(
                    f"{field_name} must be a tuple."
                )

            for value in values:
                if not isinstance(value, str):
                    raise TypeError(
                        f"All elements of "
                        f"{field_name} must be strings."
                    )

                if not value.strip():
                    raise ValueError(
                        f"{field_name} cannot contain "
                        "blank strings."
                    )

        if (
            self.parent_dimension_id is not None
        ):
            if not isinstance(
                self.parent_dimension_id,
                str,
            ):
                raise TypeError(
                    "parent_dimension_id must be "
                    "a string or None."
                )

            if (
                not self.parent_dimension_id.strip()
            ):
                raise ValueError(
                    "parent_dimension_id cannot "
                    "be blank."
                )

        if (
            self.parent_dimension_id
            == self.dimension_id
        ):
            raise ValueError(
                "A Dimension cannot reference "
                "itself as its parent."
            )

        if (
            self.dimension_id
            in self.child_dimension_ids
        ):
            raise ValueError(
                "A Dimension cannot reference "
                "itself as a child."
            )

        if (
            self.parent_dimension_id
            in self.child_dimension_ids
            and self.parent_dimension_id
            is not None
        ):
            raise ValueError(
                "A parent dimension cannot also "
                "appear in child_dimension_ids."
            )

    def _validate_engineering_metadata(
        self,
    ) -> None:
        """
        Validate engineering metadata.
        """

        if not isinstance(
            self.engineering_domain,
            EngineeringDomain,
        ):
            raise TypeError(
                "engineering_domain must be an "
                "EngineeringDomain."
            )

        if (
            self.engineering_notes
            is not None
        ):
            if not isinstance(
                self.engineering_notes,
                str,
            ):
                raise TypeError(
                    "engineering_notes must be "
                    "a string or None."
                )

            if (
                not self.engineering_notes.strip()
            ):
                raise ValueError(
                    "engineering_notes cannot "
                    "be blank."
                )

    # ========================================================
    # Repository Metadata Validators
    # ========================================================

    def _validate_repository_metadata(
        self,
    ) -> None:
        """
        Validate repository metadata.
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

        if (
            self.status_note is not None
            and not isinstance(
                self.status_note,
                str,
            )
        ):
            raise TypeError(
                "status_note must be a string or None."
            )

        datetime_fields = (
            (
                "created_timestamp",
                self.created_timestamp,
            ),
            (
                "modified_timestamp",
                self.modified_timestamp,
            ),
            (
                "approved_timestamp",
                self.approved_timestamp,
            ),
        )

        for field_name, timestamp_value in datetime_fields:

            if (
                timestamp_value is not None
                and not isinstance(
                    timestamp_value,
                    datetime,
                )
            ):
                raise TypeError(
                    f"{field_name} must be a "
                    "datetime or None."
                )

        string_fields = (
            (
                "created_by",
                self.created_by,
            ),
            (
                "approved_by",
                self.approved_by,
            ),
        )

        for field_name, string_value in string_fields:

            if string_value is None:
                continue

            if not isinstance(
                string_value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be "
                    "a string or None."
                )

            if not string_value.strip():
                raise ValueError(
                    f"{field_name} cannot "
                    "be blank."
                )

    # ========================================================
    # Governance Metadata Validators
    # ========================================================

    def _validate_governance_metadata(
        self,
    ) -> None:
        """
        Validate governance metadata.
        """

        optional_strings = (
            (
                "verification_status",
                self.verification_status,
            ),
            (
                "approval_status",
                self.approval_status,
            ),
            (
                "approval_notes",
                self.approval_notes,
            ),
            (
                "review_cycle",
                self.review_cycle,
            ),
            (
                "lifecycle_stage",
                self.lifecycle_stage,
            ),
            (
                "replacement_dimension_id",
                self.replacement_dimension_id,
            ),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be "
                    "a string or None."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot "
                    "be blank."
                )

        if not isinstance(
            self.is_verified,
            bool,
        ):
            raise TypeError(
                "is_verified must be a bool."
            )

        if not isinstance(
            self.is_deprecated,
            bool,
        ):
            raise TypeError(
                "is_deprecated must be a bool."
            )

    # ========================================================
    # Future Symbolic Mathematics Validators
    # ========================================================

    def _validate_symbolic_metadata(
        self,
    ) -> None:
        """
        Validate symbolic mathematics metadata.
        """

        optional_strings = (
            (
                "symbolic_representation",
                self.symbolic_representation,
            ),
            (
                "canonical_symbol",
                self.canonical_symbol,
            ),
            (
                "symbolic_dimension_expression",
                self.symbolic_dimension_expression,
            ),
        )

        for field_name, value in optional_strings:

            if value is None:
                continue

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be "
                    "a string or None."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} cannot "
                    "be blank."
                )

        if not isinstance(
            self.symbolic_dimension_vector,
            tuple,
        ):
            raise TypeError(
                "symbolic_dimension_vector "
                "must be a tuple."
            )

        for exponent in self.symbolic_dimension_vector:

            if not isinstance(
                exponent,
                int,
            ):
                raise TypeError(
                    "symbolic_dimension_vector "
                    "must contain only integers."
                )

        if not isinstance(
            self.symbolic_metadata,
            Mapping,
        ):
            raise TypeError(
                "symbolic_metadata must be "
                "a Mapping."
            )

        if (
            self.dimension_vector
            is not None
        ):
            # Reserved for the future
            # DimensionVector implementation.
            pass

    # ========================================================
    # Serialization
    # ========================================================

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize the Dimension into a deterministic
        dictionary representation.

        Returns
        -------
        dict[str, object]
        """

        return {
            # ------------------------------------------------
            # Identity
            # ------------------------------------------------
            "dimension_id": self.dimension_id,
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------
            "category": self.category.value,
            "physical_quantity": (
                self.physical_quantity.value
            ),
            "status": self.status.value,

            # ------------------------------------------------
            # SI Exponents
            # ------------------------------------------------
            "length_exponent":
                self.length_exponent,
            "mass_exponent":
                self.mass_exponent,
            "time_exponent":
                self.time_exponent,
            "electric_current_exponent":
                self.electric_current_exponent,
            "temperature_exponent":
                self.temperature_exponent,
            "amount_of_substance_exponent":
                self.amount_of_substance_exponent,
            "luminous_intensity_exponent":
                self.luminous_intensity_exponent,

            # ------------------------------------------------
            # Canonical Representation
            # ------------------------------------------------
            "canonical_expression":
                self.canonical_expression,
            "is_dimensionless":
                self.is_dimensionless,
            "is_base_dimension":
                self.is_base_dimension,
            "is_derived_dimension":
                self.is_derived_dimension,

            # ------------------------------------------------
            # Engineering Metadata
            # ------------------------------------------------
            "engineering_domain":
                self.engineering_domain.value,
            "engineering_disciplines":
                list(
                    self.engineering_disciplines
                ),
            "applicable_regimes":
                list(
                    self.applicable_regimes
                ),
            "engineering_notes":
                self.engineering_notes,
            "aliases":
                list(self.aliases),
            "common_names":
                list(self.common_names),
            "search_keywords":
                list(
                    self.search_keywords
                ),

            # ------------------------------------------------
            # Knowledge Foundation
            # ------------------------------------------------
            "source_reference":
                (
                    None
                    if self.source_reference is None
                    else self.source_reference.to_dict()
                ),
            "source_document":
                (
                    None
                    if self.source_document is None
                    else self.source_document.to_dict()
                ),

            "related_equation_ids":
                list(
                    self.related_equation_ids
                ),
            "related_variable_ids":
                list(
                    self.related_variable_ids
                ),
            "related_constant_ids":
                list(
                    self.related_constant_ids
                ),
            "related_unit_ids":
                list(
                    self.related_unit_ids
                ),
            "parent_dimension_id":
                self.parent_dimension_id,
            "child_dimension_ids":
                list(
                    self.child_dimension_ids
                ),

            # ------------------------------------------------
            # Repository Metadata
            # ------------------------------------------------
            "version":
                self.version,
            "status_note":
                self.status_note,
            "tags":
                list(self.tags),

            "created_timestamp":
                (
                    None
                    if self.created_timestamp is None
                    else self.created_timestamp.isoformat()
                ),

            "modified_timestamp":
                (
                    None
                    if self.modified_timestamp is None
                    else self.modified_timestamp.isoformat()
                ),

            "created_by":
                self.created_by,

            "approved_by":
                self.approved_by,

            "approved_timestamp":
                (
                    None
                    if self.approved_timestamp is None
                    else self.approved_timestamp.isoformat()
                ),

            # ------------------------------------------------
            # Governance Metadata
            # ------------------------------------------------
            "verification_status":
                self.verification_status,
            "approval_status":
                self.approval_status,
            "approval_notes":
                self.approval_notes,
            "review_cycle":
                self.review_cycle,
            "lifecycle_stage":
                self.lifecycle_stage,
            "is_verified":
                self.is_verified,
            "is_deprecated":
                self.is_deprecated,
            "replacement_dimension_id":
                self.replacement_dimension_id,

            # ------------------------------------------------
            # Symbolic Mathematics
            # ------------------------------------------------
            "symbolic_representation":
                self.symbolic_representation,
            "canonical_symbol":
                self.canonical_symbol,
            "symbolic_dimension_expression":
                self.symbolic_dimension_expression,
            "symbolic_dimension_vector":
                list(
                    self.symbolic_dimension_vector
                ),
            "symbolic_metadata":
                dict(
                    self.symbolic_metadata
                ),

            # ------------------------------------------------
            # Future Extension
            # ------------------------------------------------
            "dimension_vector":
                self.dimension_vector,
        }
    
    # ========================================================
    # Deserialization Helpers
    # ========================================================

    @staticmethod
    def _deserialize_reference(
        data: object,
    ) -> Reference:
        """
        Deserialize a Reference object.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Reference data must be a dictionary."
            )

        return Reference.from_dict(data)

    @staticmethod
    def _deserialize_document(
        data: object,
    ) -> Document:
        """
        Deserialize a Document object.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "Document data must be a dictionary."
            )

        return Document.from_dict(data)

    @staticmethod
    def _deserialize_datetime(
        value: str | None,
    ) -> datetime | None:
        """
        Deserialize an ISO-8601 datetime.
        """

        if value is None:
            return None

        return datetime.fromisoformat(value)

    @staticmethod
    def _deserialize_string_sequence(
        data: object | None,
        field_name: str,
    ) -> tuple[str, ...]:
        if data is None:
            return ()

        if not isinstance(data, (list, tuple)):
            raise TypeError(
                f"{field_name} must be a list or tuple of strings."
            )

        values: list[str] = []
        for value in data:
            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must contain only strings."
                )
            values.append(value)

        return tuple(values)

    @staticmethod
    def _deserialize_int_sequence(
        data: object | None,
        field_name: str,
    ) -> tuple[int, ...]:
        if data is None:
            return ()

        if not isinstance(data, (list, tuple)):
            raise TypeError(
                f"{field_name} must be a list or tuple of integers."
            )

        values: list[int] = []
        for value in data:
            if not isinstance(value, int):
                raise TypeError(
                    f"{field_name} must contain only integers."
                )
            values.append(value)

        return tuple(values)

    @staticmethod
    def _deserialize_optional_string(
        data: object | None,
        field_name: str,
    ) -> str | None:
        if data is None:
            return None

        if not isinstance(data, str):
            raise TypeError(
                f"{field_name} must be a string."
            )

        return data

    @staticmethod
    def _deserialize_string_mapping(
        data: object | None,
        field_name: str,
    ) -> dict[str, object]:
        if data is None:
            return {}

        if not isinstance(data, dict):
            raise TypeError(
                f"{field_name} must be a dictionary."
            )

        for key in data:
            if not isinstance(key, str):
                raise TypeError(
                    f"{field_name} keys must be strings."
                )

        return dict(data)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Dimension":
        """
        Reconstruct a Dimension from its serialized
        dictionary representation.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary."
            )

        source_reference = (
            None
            if data.get("source_reference") is None
            else cls._deserialize_reference(
                data["source_reference"]
            )
        )

        source_document = (
            None
            if data.get("source_document") is None
            else cls._deserialize_document(
                data["source_document"]
            )
        )

        created_timestamp = cls._deserialize_datetime(
            cls._deserialize_optional_string(
                data.get("created_timestamp"),
                "created_timestamp",
            )
        )

        modified_timestamp = cls._deserialize_datetime(
            cls._deserialize_optional_string(
                data.get("modified_timestamp"),
                "modified_timestamp",
            )
        )

        approved_timestamp = cls._deserialize_datetime(
            cls._deserialize_optional_string(
                data.get("approved_timestamp"),
                "approved_timestamp",
            )
        )

        raw_length_exponent = data.get("length_exponent")
        if not isinstance(raw_length_exponent, int):
            raise TypeError(
                "length_exponent must be an integer."
            )

        raw_mass_exponent = data.get("mass_exponent")
        if not isinstance(raw_mass_exponent, int):
            raise TypeError(
                "mass_exponent must be an integer."
            )

        raw_time_exponent = data.get("time_exponent")
        if not isinstance(raw_time_exponent, int):
            raise TypeError(
                "time_exponent must be an integer."
            )

        raw_electric_current_exponent = data.get(
            "electric_current_exponent"
        )
        if not isinstance(
            raw_electric_current_exponent,
            int,
        ):
            raise TypeError(
                "electric_current_exponent must be an integer."
            )

        raw_temperature_exponent = data.get("temperature_exponent")
        if not isinstance(raw_temperature_exponent, int):
            raise TypeError(
                "temperature_exponent must be an integer."
            )

        raw_amount_of_substance_exponent = data.get(
            "amount_of_substance_exponent"
        )
        if not isinstance(
            raw_amount_of_substance_exponent,
            int,
        ):
            raise TypeError(
                "amount_of_substance_exponent must be an integer."
            )

        raw_luminous_intensity_exponent = data.get(
            "luminous_intensity_exponent"
        )
        if not isinstance(
            raw_luminous_intensity_exponent,
            int,
        ):
            raise TypeError(
                "luminous_intensity_exponent must be an integer."
            )

        engineering_disciplines = cls._deserialize_string_sequence(
            data.get("engineering_disciplines"),
            "engineering_disciplines",
        )

        applicable_regimes = cls._deserialize_string_sequence(
            data.get("applicable_regimes"),
            "applicable_regimes",
        )

        aliases = cls._deserialize_string_sequence(
            data.get("aliases"),
            "aliases",
        )

        common_names = cls._deserialize_string_sequence(
            data.get("common_names"),
            "common_names",
        )

        search_keywords = cls._deserialize_string_sequence(
            data.get("search_keywords", []),
            "search_keywords",
        )

        related_equation_ids = cls._deserialize_string_sequence(
            data.get("related_equation_ids", []),
            "related_equation_ids",
        )

        related_variable_ids = cls._deserialize_string_sequence(
            data.get("related_variable_ids", []),
            "related_variable_ids",
        )

        related_constant_ids = cls._deserialize_string_sequence(
            data.get("related_constant_ids", []),
            "related_constant_ids",
        )

        related_unit_ids = cls._deserialize_string_sequence(
            data.get("related_unit_ids", []),
            "related_unit_ids",
        )

        return cls(

            # ------------------------------------------------
            # Identity
            # ------------------------------------------------

            dimension_id=str(data["dimension_id"]),
            name=str(data["name"]),
            symbol=str(data["symbol"]),
            description=str(data["description"]),

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------

            category=DimensionCategory(
                str(data["category"])
            ),

            physical_quantity=PhysicalQuantity(
                str(data["physical_quantity"])
            ),

            status=DimensionStatus(
                str(data["status"])
            ),

            # ------------------------------------------------
            # SI Exponents
            # ------------------------------------------------

            length_exponent=raw_length_exponent,
            mass_exponent=raw_mass_exponent,

            time_exponent=raw_time_exponent,
            electric_current_exponent=raw_electric_current_exponent,

            temperature_exponent=raw_temperature_exponent,

            amount_of_substance_exponent=raw_amount_of_substance_exponent,

            luminous_intensity_exponent=raw_luminous_intensity_exponent,

            # ------------------------------------------------
            # Canonical Representation
            # ------------------------------------------------

            canonical_expression=str(
                data["canonical_expression"]
            ),

            is_dimensionless=bool(
                data["is_dimensionless"]
            ),

            is_base_dimension=bool(
                data["is_base_dimension"]
            ),

            is_derived_dimension=bool(
                data["is_derived_dimension"]
            ),

            # ------------------------------------------------
            # Engineering Metadata
            # ------------------------------------------------

            engineering_domain=EngineeringDomain(
                str(data["engineering_domain"])
            ),

            engineering_disciplines=engineering_disciplines,

            applicable_regimes=applicable_regimes,

            engineering_notes=cls._deserialize_optional_string(
                data.get("engineering_notes"),
                "engineering_notes",
            ),

            aliases=aliases,

            common_names=common_names,

            search_keywords=search_keywords,

            # ------------------------------------------------
            # Knowledge Foundation
            # ------------------------------------------------

            source_reference=source_reference,

            source_document=source_document,

            related_equation_ids=related_equation_ids,

            related_variable_ids=related_variable_ids,

            related_constant_ids=related_constant_ids,

            related_unit_ids=related_unit_ids,

            parent_dimension_id=cls._deserialize_optional_string(
                data.get("parent_dimension_id"),
                "parent_dimension_id",
            ),

            child_dimension_ids=cls._deserialize_string_sequence(
                data.get("child_dimension_ids", []),
                "child_dimension_ids",
            ),

            # ------------------------------------------------
            # Repository
            # ------------------------------------------------

            version=str(data["version"]),

            status_note=cls._deserialize_optional_string(
                data.get("status_note"),
                "status_note",
            ),

            tags=cls._deserialize_string_sequence(
                data.get("tags", []),
                "tags",
            ),

            created_timestamp=created_timestamp,

            modified_timestamp=modified_timestamp,

            created_by=cls._deserialize_optional_string(
                data.get("created_by"),
                "created_by",
            ),

            approved_by=cls._deserialize_optional_string(
                data.get("approved_by"),
                "approved_by",
            ),

            approved_timestamp=approved_timestamp,

            # ------------------------------------------------
            # Governance
            # ------------------------------------------------

            verification_status=cls._deserialize_optional_string(
                data.get("verification_status"),
                "verification_status",
            ),

            approval_status=cls._deserialize_optional_string(
                data.get("approval_status"),
                "approval_status",
            ),

            approval_notes=cls._deserialize_optional_string(
                data.get("approval_notes"),
                "approval_notes",
            ),

            review_cycle=cls._deserialize_optional_string(
                data.get("review_cycle"),
                "review_cycle",
            ),

            lifecycle_stage=cls._deserialize_optional_string(
                data.get("lifecycle_stage"),
                "lifecycle_stage",
            ),

            is_verified=bool(
                data["is_verified"]
            ),

            is_deprecated=bool(
                data["is_deprecated"]
            ),

            replacement_dimension_id=cls._deserialize_optional_string(
                data.get("replacement_dimension_id"),
                "replacement_dimension_id",
            ),

            # ------------------------------------------------
            # Symbolic Mathematics
            # ------------------------------------------------

            symbolic_representation=cls._deserialize_optional_string(
                data.get("symbolic_representation"),
                "symbolic_representation",
            ),

            canonical_symbol=cls._deserialize_optional_string(
                data.get("canonical_symbol"),
                "canonical_symbol",
            ),

            symbolic_dimension_expression=cls._deserialize_optional_string(
                data.get("symbolic_dimension_expression"),
                "symbolic_dimension_expression",
            ),

            symbolic_dimension_vector=cls._deserialize_int_sequence(
                data.get("symbolic_dimension_vector", []),
                "symbolic_dimension_vector",
            ),

            symbolic_metadata=cls._deserialize_string_mapping(
                data.get("symbolic_metadata", {}),
                "symbolic_metadata",
            ),

            # ------------------------------------------------
            # Future Extension
            # ------------------------------------------------

            dimension_vector=data.get(
                "dimension_vector"
            ),
        )

    # ========================================================
    # Object Semantics
    # ========================================================

    def __iter__(
        self,
    ) -> Iterator[tuple[str, object]]:
        """
        Iterate over serialized key/value pairs.

        Returns
        -------
        Iterator[tuple[str, object]]
            Iterator over deterministic serialized
            key/value pairs.
        """

        yield from self.to_dict().items()

    def __len__(
        self,
    ) -> int:
        """
        Return the number of serialized fields.

        Returns
        -------
        int
        """

        return len(self.to_dict())

    def copy(
        self,
    ) -> "Dimension":
        """
        Create an identical immutable copy.

        Returns
        -------
        Dimension
        """

        return self.from_dict(
            self.to_dict()
        )

    def serialize(
        self,
    ) -> dict[str, object]:
        """
        Serialize this Dimension.

        This is an alias for ``to_dict()``.

        Returns
        -------
        dict[str, object]
        """

        return self.to_dict()

    @classmethod
    def deserialize(
        cls,
        payload: dict[str, object],
    ) -> "Dimension":
        """
        Deserialize a Dimension.

        Parameters
        ----------
        payload : dict[str, object]

        Returns
        -------
        Dimension
        """

        return cls.from_dict(
            payload
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

        Parameters
        ----------
        alias : str

        Returns
        -------
        bool
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

        Parameters
        ----------
        keyword : str

        Returns
        -------
        bool
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

        Returns
        -------
        bool
        """

        return self.source_reference is not None

    def has_document(
        self,
    ) -> bool:
        """
        Determine whether a Document exists.

        Returns
        -------
        bool
        """

        return self.source_document is not None

    def is_base(
        self,
    ) -> bool:
        """
        Determine whether this is a base dimension.

        Returns
        -------
        bool
        """

        return self.is_base_dimension

    def is_derived(
        self,
    ) -> bool:
        """
        Determine whether this is a derived dimension.

        Returns
        -------
        bool
        """

        return self.is_derived_dimension

    def is_dimensionless_quantity(
        self,
    ) -> bool:
        """
        Determine whether the Dimension is
        dimensionless.

        Returns
        -------
        bool
        """

        return self.is_dimensionless

    # ========================================================
    # Analysis Methods
    # ========================================================

    def base_dimension_count(
        self,
    ) -> int:
        """
        Return the number of non-zero SI base
        dimension exponents.

        Returns
        -------
        int
        """

        exponents = (
            self.length_exponent,
            self.mass_exponent,
            self.time_exponent,
            self.electric_current_exponent,
            self.temperature_exponent,
            self.amount_of_substance_exponent,
            self.luminous_intensity_exponent,
        )

        return sum(
            exponent != 0
            for exponent in exponents
        )

    def nonzero_exponent_count(
        self,
    ) -> int:
        """
        Return the number of non-zero exponents.

        Returns
        -------
        int
        """

        return self.base_dimension_count()

    def relationship_count(
        self,
    ) -> int:
        """
        Return the total number of relationships to
        other Knowledge Foundation entities.

        Returns
        -------
        int
        """

        count = 0

        count += len(self.related_equation_ids)
        count += len(self.related_variable_ids)
        count += len(self.related_constant_ids)
        count += len(self.related_unit_ids)
        count += len(self.child_dimension_ids)

        if self.parent_dimension_id is not None:
            count += 1

        return count

    def engineering_discipline_count(
        self,
    ) -> int:
        """
        Return the number of engineering disciplines.

        Returns
        -------
        int
        """

        return len(
            self.engineering_disciplines
        )

    def applicable_regime_count(
        self,
    ) -> int:
        """
        Return the number of applicable engineering
        regimes.

        Returns
        -------
        int
        """

        return len(
            self.applicable_regimes
        )

    def knowledge_tag_count(
        self,
    ) -> int:
        """
        Return the number of repository tags.

        Returns
        -------
        int
        """

        return len(self.tags)

    def alias_count(
        self,
    ) -> int:
        """
        Return the number of aliases.

        Returns
        -------
        int
        """

        return len(self.aliases)

    def common_name_count(
        self,
    ) -> int:
        """
        Return the number of common names.

        Returns
        -------
        int
        """

        return len(
            self.common_names
        )

    def keyword_count(
        self,
    ) -> int:
        """
        Return the number of search keywords.

        Returns
        -------
        int
        """

        return len(
            self.search_keywords
        )

    def export_identifier_count(
        self,
    ) -> int:
        """
        Return the number of identifiers exported
        with this Dimension.

        Returns
        -------
        int
        """

        count = 1  # dimension_id

        if self.parent_dimension_id is not None:
            count += 1

        count += len(
            self.child_dimension_ids
        )

        return count

    def exponent_vector(
        self,
    ) -> tuple[int, int, int, int, int, int, int]:
        """
        Return the SI exponent vector.

        Returns
        -------
        tuple[int, int, int, int, int, int, int]
        """

        return (
            self.length_exponent,
            self.mass_exponent,
            self.time_exponent,
            self.electric_current_exponent,
            self.temperature_exponent,
            self.amount_of_substance_exponent,
            self.luminous_intensity_exponent,
        )                   