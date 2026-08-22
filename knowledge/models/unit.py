"""
COSMOS Knowledge Foundation

Module
------
unit.py

Purpose
-------
Defines the immutable Unit model used throughout the
COSMOS Knowledge Foundation.

A Unit represents the canonical engineering description
of a physical measurement unit. Every engineering
quantity, variable, constant, equation, physics solver,
optimization engine, and AI knowledge system shall
reference Unit objects rather than raw unit strings.

The Unit model provides:

* Canonical SI representation
* Engineering metadata
* Unit classification
* Conversion metadata
* Repository compatibility
* Future dimensional analysis support
* Future Pint integration
* Future symbolic mathematics compatibility

Design Goals
------------
* Immutable
* Thread-safe
* Fully typed
* Deterministic
* Repository-ready
* AI-ready
* Future unit conversion compatible

This module intentionally contains no numerical
conversion algorithms, symbolic mathematics, or
repository logic.
"""

from __future__ import annotations

from collections.abc import Iterator
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from knowledge.models.document import Document
from knowledge.models.reference import Reference

# ============================================================
# Enumerations
# ============================================================


class UnitSystem(Enum):
    """
    Supported engineering unit systems.
    """

    SI = "SI"
    CGS = "CGS"
    IMPERIAL = "IMPERIAL"
    US_CUSTOMARY = "US_CUSTOMARY"
    CUSTOM = "CUSTOM"


class UnitCategory(Enum):
    """
    Engineering classification of measurement units.
    """

    LENGTH = "LENGTH"
    MASS = "MASS"
    TIME = "TIME"
    TEMPERATURE = "TEMPERATURE"

    AREA = "AREA"
    VOLUME = "VOLUME"

    VELOCITY = "VELOCITY"
    ACCELERATION = "ACCELERATION"

    FORCE = "FORCE"
    PRESSURE = "PRESSURE"

    ENERGY = "ENERGY"
    POWER = "POWER"

    DENSITY = "DENSITY"
    MASS_FLOW_RATE = "MASS_FLOW_RATE"
    VOLUMETRIC_FLOW_RATE = "VOLUMETRIC_FLOW_RATE"

    ANGLE = "ANGLE"

    FREQUENCY = "FREQUENCY"

    HEAT_FLUX = "HEAT_FLUX"
    HEAT_TRANSFER_COEFFICIENT = (
        "HEAT_TRANSFER_COEFFICIENT"
    )

    VISCOSITY = "VISCOSITY"

    THERMAL_CONDUCTIVITY = (
        "THERMAL_CONDUCTIVITY"
    )

    SPECIFIC_HEAT = "SPECIFIC_HEAT"

    ENTROPY = "ENTROPY"
    ENTHALPY = "ENTHALPY"

    DIMENSIONLESS = "DIMENSIONLESS"

    OTHER = "OTHER"


class QuantityType(Enum):
    """
    Mathematical quantity classification.
    """

    SCALAR = "SCALAR"
    VECTOR = "VECTOR"
    TENSOR = "TENSOR"


class UnitStatus(Enum):
    """
    Lifecycle status of the unit definition.
    """

    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    EXPERIMENTAL = "EXPERIMENTAL"

from dataclasses import dataclass


# ============================================================
# Unit Model
# ============================================================


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Unit:
    """
    Canonical engineering unit representation.

    The Unit model defines the immutable representation
    of every engineering measurement unit used throughout
    COSMOS.

    A Unit object contains only metadata describing the
    engineering unit. It does not perform unit conversion,
    dimensional analysis, symbolic mathematics, or numerical
    computation.

    Future versions will integrate with:

    * Pint
    * SymPy
    * NASA CEA
    * RocketCEA
    * OpenMDAO
    * Knowledge Graph
    * AI Retrieval
    * Repository Layer

    Attributes
    ----------
    unit_id
        Globally unique identifier.

    name
        Human-readable unit name.

    symbol
        Standard engineering symbol.

    category
        Engineering classification of the unit.

    system
        Unit system definition.

    quantity_type
        Mathematical quantity classification.

    status
        Lifecycle status of the unit definition.
    """

    # ========================================================
    # Identity
    # ========================================================

    unit_id: str

    name: str

    symbol: str

    description: str

    # ========================================================
    # Classification
    # ========================================================

    category: UnitCategory

    system: UnitSystem

    quantity_type: QuantityType

    status: UnitStatus    

    # ========================================================
    # Engineering Metadata
    # ========================================================

    dimension: "object | None"

    is_si_base: bool

    is_dimensionless: bool

    is_exact: bool

    # ========================================================
    # Conversion Metadata
    # ========================================================

    scale_factor: float

    offset: float

    # ========================================================
    # Physical Quantity Metadata
    # ========================================================

    quantity_name: str

    quantity_description: str

    # ========================================================
    # Knowledge Metadata
    # ========================================================

    aliases: tuple[str, ...]

    common_names: tuple[str, ...]

    search_keywords: tuple[str, ...]

    # ========================================================
    # Provenance
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

    # ========================================================
    # Governance Metadata
    # ========================================================

    created_by: str | None

    approved_by: str | None

    approved_timestamp: datetime | None

    # ========================================================
    # Future Symbolic Mathematics Metadata
    # ========================================================

    symbolic_representation: str | None

    canonical_symbol: str | None

    # ========================================================
    # Construction Validation
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate the Unit immediately after construction.

        The Unit model follows fail-fast validation to ensure
        every instance is internally consistent before it can
        be used anywhere within the COSMOS Knowledge
        Foundation.

        Raises
        ------
        ValueError
            If any validation rule fails.

        TypeError
            If any field has an invalid type.
        """

        self.validate()

    def validate(self) -> None:
        """
        Validate the complete Unit object.

        Validation is delegated to specialized private
        validator methods in order to maintain a clean,
        modular, and extensible validation architecture.

        Raises
        ------
        ValueError
            If any validation rule fails.

        TypeError
            If any field has an invalid type.
        """

        # ----------------------------------------------------
        # Identity
        # ----------------------------------------------------

        self._validate_unit_id()
        self._validate_name()
        self._validate_symbol()

        # ----------------------------------------------------
        # Engineering
        # ----------------------------------------------------

        self._validate_conversion()
        self._validate_category()
        self._validate_system()

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        self._validate_reference()
        self._validate_document()

        # ----------------------------------------------------
        # Knowledge Metadata
        # ----------------------------------------------------

        self._validate_aliases()
        self._validate_common_names()
        self._validate_search_keywords()

        self._validate_metadata()

        # ----------------------------------------------------
        # Repository
        # ----------------------------------------------------

        self._validate_repository_metadata()

        # ----------------------------------------------------
        # Governance
        # ----------------------------------------------------

        self._validate_governance()

        # ----------------------------------------------------
        # Future Extensions
        # ----------------------------------------------------

        self._validate_future_metadata() 

    # ========================================================
    # Core Validators
    # ========================================================

    def _validate_unit_id(self) -> None:
        """
        Validate the unit identifier.

        Raises
        ------
        TypeError
            If the identifier is not a string.

        ValueError
            If the identifier is blank.
        """

        if not isinstance(self.unit_id, str):
            raise TypeError(
                "unit_id must be a string."
            )

        if not self.unit_id.strip():
            raise ValueError(
                "unit_id cannot be blank."
            )

    def _validate_name(self) -> None:
        """
        Validate the unit name.

        Raises
        ------
        TypeError
            If the name is not a string.

        ValueError
            If the name is blank.
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

        Raises
        ------
        TypeError
            If the symbol is not a string.

        ValueError
            If the symbol is blank.
        """

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

    def _validate_conversion(self) -> None:
        """
        Validate conversion metadata.

        Raises
        ------
        TypeError
            If conversion fields have invalid types.

        ValueError
            If scale_factor is zero.
        """

        if not isinstance(self.scale_factor, float):
            raise TypeError(
                "scale_factor must be a float."
            )

        if self.scale_factor == 0.0:
            raise ValueError(
                "scale_factor cannot be zero."
            )

        if not isinstance(self.offset, float):
            raise TypeError(
                "offset must be a float."
            )

    def _validate_category(self) -> None:
        """
        Validate the engineering category.

        Raises
        ------
        TypeError
            If category is not a UnitCategory.
        """

        if not isinstance(
            self.category,
            UnitCategory,
        ):
            raise TypeError(
                "category must be a UnitCategory."
            )

    def _validate_system(self) -> None:
        """
        Validate the unit system.

        Raises
        ------
        TypeError
            If system is not a UnitSystem.
        """

        if not isinstance(
            self.system,
            UnitSystem,
        ):
            raise TypeError(
                "system must be a UnitSystem."
            )
        
    # ========================================================
    # Metadata Validators
    # ========================================================

    def _validate_dimension(self) -> None:
        """
        Validate the engineering dimension.

        During Phase 0.5.4 the Dimension model has not yet
        been implemented. Therefore this validator only
        verifies that the field is either None or a valid
        placeholder object.

        Future versions shall validate against the canonical
        Dimension model.

        Raises
        ------
        TypeError
            If the dimension field has an invalid type.
        """

        if self.dimension is not None:
            # Placeholder validation until Dimension exists.
            pass

    def _validate_reference(self) -> None:
        """
        Validate the source reference.

        Raises
        ------
        TypeError
            If source_reference has an invalid type.
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

    def _validate_document(self) -> None:
        """
        Validate the source document.

        Raises
        ------
        TypeError
            If source_document has an invalid type.
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

    def _validate_aliases(self) -> None:
        """
        Validate aliases.

        Raises
        ------
        TypeError
            If aliases are invalid.
        """

        if not isinstance(
            self.aliases,
            tuple,
        ):
            raise TypeError(
                "aliases must be a tuple."
            )

        for alias in self.aliases:
            if not isinstance(alias, str):
                raise TypeError(
                    "Each alias must be a string."
                )

            if not alias.strip():
                raise ValueError(
                    "Alias entries cannot be blank."
                )

    def _validate_common_names(self) -> None:
        """
        Validate common names.

        Raises
        ------
        TypeError
            If common_names are invalid.
        """

        if not isinstance(
            self.common_names,
            tuple,
        ):
            raise TypeError(
                "common_names must be a tuple."
            )

        for name in self.common_names:
            if not isinstance(name, str):
                raise TypeError(
                    "Each common name must be a string."
                )

            if not name.strip():
                raise ValueError(
                    "Common name entries cannot be blank."
                )

    def _validate_search_keywords(self) -> None:
        """
        Validate search keywords.

        Raises
        ------
        TypeError
            If search_keywords are invalid.
        """

        if not isinstance(
            self.search_keywords,
            tuple,
        ):
            raise TypeError(
                "search_keywords must be a tuple."
            )

        for keyword in self.search_keywords:
            if not isinstance(keyword, str):
                raise TypeError(
                    "Each search keyword must be a string."
                )

            if not keyword.strip():
                raise ValueError(
                    "Search keyword entries cannot be blank."
                )

    def _validate_metadata(self) -> None:
        """
        Validate general engineering metadata.

        Raises
        ------
        TypeError
            If metadata fields have invalid types.
        """

        if not isinstance(
            self.quantity_name,
            str,
        ):
            raise TypeError(
                "quantity_name must be a string."
            )

        if not self.quantity_name.strip():
            raise ValueError(
                "quantity_name cannot be blank."
            )

        if not isinstance(
            self.quantity_description,
            str,
        ):
            raise TypeError(
                "quantity_description must be a string."
            )

        if not self.quantity_description.strip():
            raise ValueError(
                "quantity_description cannot be blank."
            )

    # ========================================================
    # Enterprise Validators
    # ========================================================

    def _validate_repository_metadata(self) -> None:
        """
        Validate repository-related metadata.

        Raises
        ------
        TypeError
            If repository metadata fields have invalid types.

        ValueError
            If required repository metadata is invalid.
        """

        if not isinstance(self.version, str):
            raise TypeError(
                "version must be a string."
            )

        if not self.version.strip():
            raise ValueError(
                "version cannot be blank."
            )

        if not isinstance(self.status_note, str):
            raise TypeError(
                "status_note must be a string."
            )

    def _validate_governance(self) -> None:
        """
        Validate governance metadata.

        Raises
        ------
        TypeError
            If governance metadata has invalid types.
        """

        if (
            self.created_by is not None
            and not isinstance(self.created_by, str)
        ):
            raise TypeError(
                "created_by must be a string or None."
            )

        if (
            self.approved_by is not None
            and not isinstance(self.approved_by, str)
        ):
            raise TypeError(
                "approved_by must be a string or None."
            )

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

    def _validate_future_metadata(self) -> None:
        """
        Validate future symbolic mathematics metadata.

        These fields are reserved for future integration
        with symbolic mathematics, knowledge graphs,
        AI retrieval systems, and engineering reasoning
        engines.

        Raises
        ------
        TypeError
            If future metadata fields have invalid types.
        """

        if (
            self.symbolic_representation is not None
            and not isinstance(
                self.symbolic_representation,
                str,
            )
        ):
            raise TypeError(
                "symbolic_representation must be a string or None."
            )

        if (
            self.canonical_symbol is not None
            and not isinstance(
                self.canonical_symbol,
                str,
            )
        ):
            raise TypeError(
                "canonical_symbol must be a string or None."
            )

    # ========================================================
    # Serialization
    # ========================================================

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the Unit into a deterministic dictionary.

        Returns
        -------
        dict[str, object]
            Serialized representation of the Unit.
        """

        return {
            # ------------------------------------------------
            # Identity
            # ------------------------------------------------
            "unit_id": self.unit_id,
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,

            # ------------------------------------------------
            # Classification
            # ------------------------------------------------
            "category": self.category.value,
            "system": self.system.value,
            "quantity_type": self.quantity_type.value,
            "status": self.status.value,

            # ------------------------------------------------
            # Engineering Metadata
            # ------------------------------------------------
            "dimension": None,
            "is_si_base": self.is_si_base,
            "is_dimensionless": self.is_dimensionless,
            "is_exact": self.is_exact,

            # ------------------------------------------------
            # Conversion
            # ------------------------------------------------
            "scale_factor": self.scale_factor,
            "offset": self.offset,

            # ------------------------------------------------
            # Physical Metadata
            # ------------------------------------------------
            "quantity_name": self.quantity_name,
            "quantity_description": self.quantity_description,

            # ------------------------------------------------
            # Knowledge Metadata
            # ------------------------------------------------
            "aliases": list(self.aliases),
            "common_names": list(self.common_names),
            "search_keywords": list(
                self.search_keywords
            ),

            # ------------------------------------------------
            # Provenance
            # ------------------------------------------------
            "source_reference": (
                None
                if self.source_reference is None
                else self.source_reference.to_dict()
            ),

            "source_document": (
                None
                if self.source_document is None
                else self.source_document.to_dict()
            ),

            # ------------------------------------------------
            # Repository Metadata
            # ------------------------------------------------
            "version": self.version,
            "status_note": self.status_note,

            "created_timestamp": (
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat()
            ),

            "modified_timestamp": (
                None
                if self.modified_timestamp is None
                else self.modified_timestamp.isoformat()
            ),

            # ------------------------------------------------
            # Governance
            # ------------------------------------------------
            "created_by": self.created_by,
            "approved_by": self.approved_by,

            "approved_timestamp": (
                None
                if self.approved_timestamp is None
                else self.approved_timestamp.isoformat()
            ),

            # ------------------------------------------------
            # Future Metadata
            # ------------------------------------------------
            "symbolic_representation":
                self.symbolic_representation,

            "canonical_symbol":
                self.canonical_symbol,
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

        Parameters
        ----------
        data : object

        Returns
        -------
        Reference
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

        Parameters
        ----------
        data : object

        Returns
        -------
        Document
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

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Unit":
        """
        Reconstruct a Unit from its serialized dictionary.

        Parameters
        ----------
        data : dict[str, object]
            Serialized Unit representation.

        Returns
        -------
        Unit

        Raises
        ------
        TypeError
            If data is not a dictionary.

        ValueError
            If required fields are missing or invalid.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary."
            )

        # ----------------------------------------------------
        # Provenance
        # ----------------------------------------------------

        source_reference = (
            None
            if data.get("source_reference") is None
            else cls._deserialize_reference(data["source_reference"])
        )

        source_document = (
            None
            if data.get("source_document") is None
            else cls._deserialize_document(data["source_document"])
        )

        # ----------------------------------------------------
        # Datetime reconstruction
        # ----------------------------------------------------

        created_timestamp = (
            None
            if data.get("created_timestamp") is None
            else cls._deserialize_datetime(str(data["created_timestamp"]))
        )

        modified_timestamp = (
            None
            if data.get("modified_timestamp") is None
            else cls._deserialize_datetime(str(data["modified_timestamp"]))
        )

        approved_timestamp = (
            None
            if data.get("approved_timestamp") is None
            else cls._deserialize_datetime(str(data["approved_timestamp"]))
        )

        # ----------------------------------------------------
        # Enum reconstruction
        # ----------------------------------------------------

        category = UnitCategory(
            str(data["category"])
        )

        system = UnitSystem(
            str(data["system"])
        )

        quantity_type = QuantityType(
            str(data["quantity_type"])
        )

        status = UnitStatus(
            str(data["status"])
        )

        # ----------------------------------------------------
        # Tuple reconstruction
        # ----------------------------------------------------

        def _coerce_to_tuple(field: str) -> tuple[str, ...]:
            raw = data.get(field, [])

            if raw is None:
                return tuple()

            if isinstance(raw, (list, tuple)):
                return tuple(str(x) for x in raw)

            raise TypeError(f"{field} must be a list or tuple of strings.")

        aliases = _coerce_to_tuple("aliases")
        common_names = _coerce_to_tuple("common_names")
        search_keywords = _coerce_to_tuple("search_keywords")

        # ----------------------------------------------------
        # Dimension placeholder
        # ----------------------------------------------------

        dimension = None

        # ----------------------------------------------------
        # Construction
        # ----------------------------------------------------

        return cls(
            # Identity
            unit_id=str(data["unit_id"]),
            name=str(data["name"]),
            symbol=str(data["symbol"]),
            description=str(data["description"]),

            # Classification
            category=category,
            system=system,
            quantity_type=quantity_type,
            status=status,

            # Engineering
            dimension=dimension,
            is_si_base=bool(
                data["is_si_base"]
            ),
            is_dimensionless=bool(
                data["is_dimensionless"]
            ),
            is_exact=bool(
                data["is_exact"]
            ),

            # Conversion
            scale_factor=float(
                str(data["scale_factor"])
            ),
            offset=float(
                str(data["offset"])
            ),

            # Physical metadata
            quantity_name=str(
                data["quantity_name"]
            ),
            quantity_description=str(
                data[
                    "quantity_description"
                ]
            ),

            # Knowledge metadata
            aliases=aliases,
            common_names=common_names,
            search_keywords=search_keywords,

            # Provenance
            source_reference=source_reference,
            source_document=source_document,

            # Repository
            version=str(
                data["version"]
            ),
            status_note=str(
                data["status_note"]
            ),
            created_timestamp=created_timestamp,
            modified_timestamp=modified_timestamp,

            # Governance
            created_by=(
                None
                if data.get("created_by") is None
                else str(
                    data["created_by"]
                )
            ),
            approved_by=(
                None
                if data.get("approved_by") is None
                else str(
                    data["approved_by"]
                )
            ),
            approved_timestamp=approved_timestamp,

            # Future metadata
            symbolic_representation=(
                None
                if data.get(
                    "symbolic_representation"
                ) is None
                else str(
                    data[
                        "symbolic_representation"
                    ]
                )
            ),
            canonical_symbol=(
                None
                if data.get(
                    "canonical_symbol"
                ) is None
                else str(
                    data[
                        "canonical_symbol"
                    ]
                )
            ),
        )
    
    # ========================================================
    # Query Methods
    # ========================================================

    def display_name(self) -> str:
        """
        Return a human-readable display name.

        Returns
        -------
        str
            Display string combining the unit name and symbol.

        Examples
        --------
        >>> unit.display_name()
        'Pascal (Pa)'
        """

        return f"{self.name} ({self.symbol})"

    def matches_alias(
        self,
        alias: str,
    ) -> bool:
        """
        Determine whether the supplied alias matches one of
        the registered aliases.

        Matching is case-insensitive and ignores leading and
        trailing whitespace.

        Parameters
        ----------
        alias : str
            Alias to search for.

        Returns
        -------
        bool
        """

        if not isinstance(alias, str):
            return False

        candidate = alias.strip().casefold()

        return any(
            candidate == existing.casefold()
            for existing in self.aliases
        )

    def matches_keyword(
        self,
        keyword: str,
    ) -> bool:
        """
        Determine whether a search keyword exists.

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
            candidate == existing.casefold()
            for existing in self.search_keywords
        )

    def has_reference(self) -> bool:
        """
        Determine whether a source reference exists.

        Returns
        -------
        bool
        """

        return self.source_reference is not None

    def has_document(self) -> bool:
        """
        Determine whether a source document exists.

        Returns
        -------
        bool
        """

        return self.source_document is not None

# ========================================================
# Object Semantics
# ========================================================

    def __iter__(
    self,
    ) -> Iterator[tuple[str, object]]:
        """
        Iterate over serialized key/value pairs.

        This provides deterministic ordering suitable
        for repository storage and future persistence
        backends.
        """

        yield from self.to_dict().items()

    def __len__(self) -> int:
        """
        Return the number of serialized fields.
        """

        return len(self.to_dict())

    def copy(self) -> "Unit":
        """
        Create an identical immutable copy.

        Returns
        -------
        Unit
        """

        return self.from_dict(
            self.to_dict()
        )

    def serialize(self) -> dict[str, object]:
        """
        Alias for to_dict().

        Returns
        -------
        dict[str, object]
        """

        return self.to_dict()

    @classmethod
    def deserialize(
        cls,
        payload: dict[str, object],
    ) -> "Unit":
        """
        Alias for from_dict().

        Parameters
        ----------
        payload : dict[str, object]

        Returns
        -------
        Unit
        """

        return cls.from_dict(payload)
