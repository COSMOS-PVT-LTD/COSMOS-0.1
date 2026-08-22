"""
COSMOS Knowledge Foundation

Module:
    knowledge.models.variable

Purpose:
    Defines the canonical immutable Variable model used throughout
    the COSMOS Knowledge Foundation.

Description:
    The Variable model represents an engineering quantity together
    with its numerical value, units, engineering metadata,
    provenance, solver metadata, and future AI metadata.

    Every engineering subsystem within COSMOS shall exchange
    Variable objects whenever engineering metadata must be preserved.

Responsibilities:
    - Represent engineering variables
    - Preserve engineering metadata
    - Preserve unit metadata
    - Preserve provenance
    - Support future validation
    - Support future serialization
    - Support future symbolic mathematics
    - Support future repository integration

Author:
    COSMOS Development Team

Version:
    0.1.0
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from knowledge.models.document import Document
from knowledge.models.reference import Reference


class VariableType(Enum):
    """
    Enumeration describing the underlying data type
    represented by a Variable.
    """

    FLOAT = "FLOAT"
    """Floating-point engineering quantity."""

    INTEGER = "INTEGER"
    """Integer engineering quantity."""

    BOOLEAN = "BOOLEAN"
    """Boolean engineering state."""

    STRING = "STRING"
    """Textual engineering value."""

    ENUM = "ENUM"
    """Enumerated engineering value."""


class VariableRole(Enum):
    """
    Enumeration describing the functional role of a
    Variable within engineering analyses and solvers.
    """

    INPUT = "INPUT"
    """Primary solver input."""

    OUTPUT = "OUTPUT"
    """Primary solver output."""

    DESIGN = "DESIGN"
    """Engineering design variable."""

    OPTIMIZATION = "OPTIMIZATION"
    """Optimization variable."""

    DERIVED = "DERIVED"
    """Computed engineering quantity."""

    STATE = "STATE"
    """System state variable."""

    CONSTRAINT = "CONSTRAINT"
    """Optimization or design constraint."""

    MEASURED = "MEASURED"
    """Measured or experimental quantity."""


class EngineeringDomain(Enum):
    """
    Engineering discipline associated with a Variable.
    """

    THERMODYNAMICS = "THERMODYNAMICS"
    """Thermodynamic analysis."""

    FLUID_MECHANICS = "FLUID_MECHANICS"
    """Fluid mechanics."""

    COMBUSTION = "COMBUSTION"
    """Combustion engineering."""

    HEAT_TRANSFER = "HEAT_TRANSFER"
    """Heat transfer."""

    CRYOGENICS = "CRYOGENICS"
    """Cryogenic engineering."""

    MATERIALS = "MATERIALS"
    """Materials engineering."""

    STRUCTURAL_MECHANICS = "STRUCTURAL_MECHANICS"
    """Structural mechanics."""

    CONTROLS = "CONTROLS"
    """Control systems."""

    OPTIMIZATION = "OPTIMIZATION"
    """Numerical optimization."""

    RELIABILITY = "RELIABILITY"
    """Reliability engineering."""

    CFD = "CFD"
    """Computational Fluid Dynamics."""

    OTHER = "OTHER"
    """Other engineering domain."""

    GENERAL = "GENERAL"
    """General engineering domain."""       


class VariableStatus(Enum):
    """
    Lifecycle status of an engineering Variable.
    """

    DRAFT = "DRAFT"
    """Variable is under development."""

    VERIFIED = "VERIFIED"
    """Variable has been technically verified."""

    APPROVED = "APPROVED"
    """Variable is approved for production use."""

    DEPRECATED = "DEPRECATED"
    """Variable is retained only for legacy compatibility."""

@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Variable:
    """
    Canonical immutable engineering Variable model.

    The Variable object represents a single engineering quantity
    together with its engineering metadata, numerical properties,
    units, provenance, and solver metadata.

    The Variable model is the standard representation of engineering
    quantities throughout the COSMOS Knowledge Foundation.

    Notes
    -----
    This phase defines only the immutable data structure.

    Validation, serialization, repository integration, symbolic
    mathematics, and business logic are implemented in later
    development phases.
    """

    # ==========================================================
    # Identity
    # ==========================================================

    variable_id: str
    """
    Globally unique identifier for the Variable.
    """

    name: str
    """
    Human-readable engineering variable name.

    Example
    -------
    Chamber Pressure
    """

    symbol: str
    """
    Mathematical symbol.

    Example
    -------
    Pc
    """

    description: str
    """
    Detailed engineering description of the Variable.
    """

    # ==========================================================
    # Numerical Information
    # ==========================================================

    variable_type: VariableType

    value: float | int | bool | str | None = None
    """
    Current engineering value.
    """

    default_value: float | int | bool | str | None = None
    """
    Default engineering value.
    """

    minimum_value: float | None = None
    """
    Minimum permitted engineering value.
    """

    maximum_value: float | None = None
    """
    Maximum permitted engineering value.
    """

    nominal_value: float | None = None
    """
    Nominal operating value.
    """

    # ==========================================================
    # Unit Information
    # ==========================================================

    si_unit: str
    """
    SI base or derived unit.

    Examples
    --------
    Pa
    K
    kg/s
    N
    """

    display_unit: str | None = None
    """
    Preferred display unit.

    Examples
    --------
    bar
    MPa
    psi
    """

    dimension: str
    """
    Physical dimension represented by the Variable.

    Examples
    --------
    Pressure
    Temperature
    Length
    Velocity
    Density
    Mass Flow Rate
    Thrust
    """

    # ==========================================================
    # Engineering Metadata
    # ==========================================================

    engineering_domain: EngineeringDomain
    """
    Primary engineering discipline associated with this Variable.
    """

    subsystem: str | None = None
    """
    Engineering subsystem.

    Examples
    --------
    Combustion Chamber
    Turbopump
    Injector
    Cooling Jacket
    """

    discipline: str | None = None
    """
    Engineering discipline within the subsystem.

    Examples
    --------
    Thermal
    Structural
    Fluid
    Controls
    """

    physical_meaning: str | None = None
    """
    Human-readable description of the physical significance
    of the Variable.
    """

    # ==========================================================
    # Validation Metadata
    # ==========================================================

    required: bool = True
    """
    Indicates whether this Variable is required.
    """

    read_only: bool = False
    """
    Indicates whether the Variable may be modified.
    """

    allow_negative: bool = True
    """
    Indicates whether negative values are permitted.
    """

    allow_zero: bool = True
    """
    Indicates whether zero is permitted.
    """

    finite_only: bool = True
    """
    Indicates whether only finite numerical values
    are considered valid.
    """

    # ==========================================================
    # Solver Metadata
    # ==========================================================

    variable_role: VariableRole = VariableRole.INPUT
    """
    Functional role of the Variable within engineering
    calculations and numerical solvers.
    """

    # ==========================================================
    # Provenance
    # ==========================================================

    source_reference: Reference | None = None
    """
    Engineering reference from which this Variable originates.
    """

    source_document: Document | None = None
    """
    Source engineering document containing this Variable.
    """

    equation_ids: tuple[str, ...] = ()
    """
    Identifiers of equations that reference this Variable.
    """

    # ==========================================================
    # AI Metadata
    # ==========================================================

    aliases: tuple[str, ...] = ()
    """
    Alternative engineering names.

    Examples
    --------
    Chamber Pressure
    Combustion Pressure
    Pc
    """

    common_names: tuple[str, ...] = ()
    """
    Commonly used names in aerospace literature.
    """

    search_keywords: tuple[str, ...] = ()
    """
    Keywords used for indexing and AI retrieval.
    """

    # ==========================================================
    # Lifecycle Metadata
    # ==========================================================

    status: VariableStatus = VariableStatus.DRAFT
    """
    Lifecycle status of the Variable.
    """

    def __post_init__(
        self,
    ) -> None:
        """
        Perform validation immediately after object construction.

        Notes
        -----
        A Variable object shall never exist in an invalid state.
        Construction fails immediately if any validation rule
        is violated.
        """

        self.validate()

    def validate(
        self,
    ) -> None:
        """
        Validate the Variable.

        This method performs complete validation of the Variable
        instance by delegating validation responsibilities to
        dedicated private validator methods.

        Raises
        ------
        ValueError
            If any validation rule is violated.

        TypeError
            If any field has an invalid type.
        """

        self._validate_variable_id()

        self._validate_name()

        self._validate_symbol()

        self._validate_value()

        self._validate_units()

        self._validate_bounds()

        self._validate_reference()

        self._validate_document()

        self._validate_aliases()

        self._validate_common_names()

        self._validate_search_keywords()

        self._validate_engineering_metadata()

    def _validate_variable_id(
        self,
    ) -> None:
        """
        Validate the variable identifier.

        Raises
        ------
        ValueError
            If the identifier is invalid.
        """

        if not self.variable_id.strip():
            raise ValueError(
                "variable_id must not be blank."
            )

    def _validate_name(
        self,
    ) -> None:
        """
        Validate the variable name.

        Raises
        ------
        ValueError
            If the name is invalid.
        """

        if not self.name.strip():
            raise ValueError(
                "name must not be blank."
            )

    def _validate_symbol(
        self,
    ) -> None:
        """
        Validate the engineering symbol.

        Raises
        ------
        ValueError
            If the symbol is invalid.
        """

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be blank."
            )

    def _validate_value(
        self,
    ) -> None:
        """
        Validate the numerical value.

        Raises
        ------
        TypeError
            If the value has an unsupported type.
        """

        if self.value is None:
            return

        if not isinstance(
            self.value,
            (
                float,
                int,
                bool,
                str,
            ),
        ):
            raise TypeError(
                "Unsupported value type."
            )

    def _validate_units(
        self,
    ) -> None:
        """
        Validate engineering units.

        Raises
        ------
        ValueError
            If unit definitions are invalid.
        """

        if not self.si_unit.strip():
            raise ValueError(
                "si_unit must not be blank."
            )

        if (
            self.display_unit
            is not None
            and not self.display_unit.strip()
        ):
            raise ValueError(
                "display_unit must not be blank."
            )

        if not self.dimension.strip():
            raise ValueError(
                "dimension must not be blank."
            )

    def _validate_bounds(
        self,
    ) -> None:
        """
        Validate numerical bounds.

        Raises
        ------
        ValueError
            If the numerical limits are inconsistent.
        """

        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.minimum_value
            > self.maximum_value
        ):
            raise ValueError(
                "minimum_value must not exceed "
                "maximum_value."
            )

        if (
            self.nominal_value is not None
            and self.minimum_value is not None
            and self.nominal_value
            < self.minimum_value
        ):
            raise ValueError(
                "nominal_value is below "
                "minimum_value."
            )

        if (
            self.nominal_value is not None
            and self.maximum_value is not None
            and self.nominal_value
            > self.maximum_value
        ):
            raise ValueError(
                "nominal_value exceeds "
                "maximum_value."
            )

    def _validate_reference(
        self,
    ) -> None:
        """
        Validate the source reference.

        Raises
        ------
        TypeError
            If the source reference has an invalid type.
        """

        if (
            self.source_reference
            is not None
            and not isinstance(
                self.source_reference,
                Reference,
            )
        ):
            raise TypeError(
                "source_reference must be a "
                "Reference instance."
            )

    def _validate_document(
        self,
    ) -> None:
        """
        Validate the source document.

        Raises
        ------
        TypeError
            If the source document has an invalid type.
        """

        if (
            self.source_document
            is not None
            and not isinstance(
                self.source_document,
                Document,
            )
        ):
            raise TypeError(
                "source_document must be a "
                "Document instance."
            )

    def _validate_aliases(
        self,
    ) -> None:
        """
        Validate aliases.

        Raises
        ------
        TypeError
            If aliases are malformed.
        """

        if not isinstance(
            self.aliases,
            tuple,
        ):
            raise TypeError(
                "aliases must be a tuple."
            )

        for alias in self.aliases:

            if not isinstance(
                alias,
                str,
            ):
                raise TypeError(
                    "Each alias must be a string."
                )

            if not alias.strip():
                raise ValueError(
                    "Alias entries must not "
                    "be blank."
                )

    def _validate_common_names(
        self,
    ) -> None:
        """
        Validate common names.

        Raises
        ------
        TypeError
            If common_names are malformed.
        """

        if not isinstance(
            self.common_names,
            tuple,
        ):
            raise TypeError(
                "common_names must be a tuple."
            )

        for name in self.common_names:

            if not isinstance(
                name,
                str,
            ):
                raise TypeError(
                    "Each common name must "
                    "be a string."
                )

            if not name.strip():
                raise ValueError(
                    "Common names must not "
                    "contain blank entries."
                )

    def _validate_search_keywords(
        self,
    ) -> None:
        """
        Validate search keywords.

        Raises
        ------
        TypeError
            If keywords are malformed.
        """

        if not isinstance(
            self.search_keywords,
            tuple,
        ):
            raise TypeError(
                "search_keywords must "
                "be a tuple."
            )

        for keyword in self.search_keywords:

            if not isinstance(
                keyword,
                str,
            ):
                raise TypeError(
                    "Each keyword must "
                    "be a string."
                )

            if not keyword.strip():
                raise ValueError(
                    "Search keywords must "
                    "not contain blank entries."
                )

    def _validate_engineering_metadata(
        self,
    ) -> None:
        """
        Validate engineering metadata.

        Raises
        ------
        TypeError
            If metadata fields are invalid.
        """

        if not isinstance(
            self.engineering_domain,
            EngineeringDomain,
        ):
            raise TypeError(
                "engineering_domain must "
                "be an EngineeringDomain."
            )

        metadata_fields = (
            (
                "subsystem",
                self.subsystem,
            ),
            (
                "discipline",
                self.discipline,
            ),
            (
                "physical_meaning",
                self.physical_meaning,
            ),
        )

        for field_name, value in metadata_fields:

            if (
                value is not None
                and not isinstance(
                    value,
                    str,
                )
            ):
                raise TypeError(
                    f"{field_name} must "
                    "be a string."
                )

            if (
                isinstance(
                    value,
                    str,
                )
                and not value.strip()
            ):
                raise ValueError(
                    f"{field_name} must "
                    "not be blank."
                )    

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize the Variable into a deterministic dictionary.

        Returns
        -------
        dict[str, object]
            JSON-serializable representation of the Variable.
        """

        return {
            # --------------------------------------------------
            # Identity
            # --------------------------------------------------
            "variable_id": self.variable_id,
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,

            # --------------------------------------------------
            # Numerical Information
            # --------------------------------------------------
            "variable_type": self.variable_type.value,
            "value": self.value,
            "default_value": self.default_value,
            "minimum_value": self.minimum_value,
            "maximum_value": self.maximum_value,
            "nominal_value": self.nominal_value,

            # --------------------------------------------------
            # Unit Information
            # --------------------------------------------------
            "si_unit": self.si_unit,
            "display_unit": self.display_unit,
            "dimension": self.dimension,

            # --------------------------------------------------
            # Engineering Metadata
            # --------------------------------------------------
            "engineering_domain":
                self.engineering_domain.value,
            "subsystem": self.subsystem,
            "discipline": self.discipline,
            "physical_meaning":
                self.physical_meaning,

            # --------------------------------------------------
            # Validation Metadata
            # --------------------------------------------------
            "required": self.required,
            "read_only": self.read_only,
            "allow_negative":
                self.allow_negative,
            "allow_zero":
                self.allow_zero,
            "finite_only":
                self.finite_only,

            # --------------------------------------------------
            # Solver Metadata
            # --------------------------------------------------
            "variable_role":
                self.variable_role.value,

            # --------------------------------------------------
            # Provenance
            # --------------------------------------------------
            "source_reference":
                (
                    self.source_reference.to_dict()
                    if self.source_reference
                    else None
                ),
            "source_document":
                (
                    self.source_document.to_dict()
                    if self.source_document
                    else None
                ),
            "equation_ids":
                list(self.equation_ids),

            # --------------------------------------------------
            # AI Metadata
            # --------------------------------------------------
            "aliases":
                list(self.aliases),
            "common_names":
                list(self.common_names),
            "search_keywords":
                list(self.search_keywords),

            # --------------------------------------------------
            # Lifecycle
            # --------------------------------------------------
            "status":
                self.status.value,
        }
    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Variable":
        """
        Construct a Variable from a serialized dictionary.

        Parameters
        ----------
        data : dict[str, object]
            Serialized Variable representation.

        Returns
        -------
        Variable

        Raises
        ------
        TypeError
            If ``data`` is not a dictionary.

        ValueError
            If required fields are missing.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary."
            )

        required_fields = (
            "variable_id",
            "name",
            "symbol",
            "description",
            "variable_type",
            "si_unit",
            "dimension",
            "engineering_domain",
        )

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                "Missing required fields: "
                + ", ".join(missing)
            )

        source_reference = None

        if data.get("source_reference") is not None:
            source_reference = Reference.from_dict(
                data["source_reference"]  # type: ignore[arg-type]
            )

        source_document = None

        if data.get("source_document") is not None:
            source_document = Document.from_dict(
                data["source_document"]  # type: ignore[arg-type]
            )

        return cls(
            # --------------------------------------------------
            # Identity
            # --------------------------------------------------
            variable_id=str(data["variable_id"]),
            name=str(data["name"]),
            symbol=str(data["symbol"]),
            description=str(data["description"]),

            # --------------------------------------------------
            # Numerical Information
            # --------------------------------------------------
            variable_type=VariableType(
                str(data["variable_type"])
            ),
            value=cast(
                float | int | bool | str | None,
                data.get("value"),
            ),
            default_value=cast(
                float | int | bool | str | None,
                data.get("default_value"),
            ),
            minimum_value=cast(
                float | None,
                data.get("minimum_value"),
            ),
            maximum_value=cast(
                float | None,
                data.get("maximum_value"),
            ),
            nominal_value=cast(
                float | None,
                data.get("nominal_value"),
            ),

            # --------------------------------------------------
            # Units
            # --------------------------------------------------
            si_unit=str(data["si_unit"]),
            display_unit=cast(
                str | None,
                data.get("display_unit"),
            ),
            dimension=str(data["dimension"]),

            # --------------------------------------------------
            # Engineering Metadata
            # --------------------------------------------------
            engineering_domain=EngineeringDomain(
                str(data["engineering_domain"])
            ),
            subsystem=cast(
                str | None,
                data.get("subsystem"),
            ),
            discipline=cast(
                str | None,
                data.get("discipline"),
            ),
            physical_meaning=cast(
                str | None,
                data.get("physical_meaning"),
            ),

            # --------------------------------------------------
            # Validation Metadata
            # --------------------------------------------------
            required=bool(
                data.get(
                    "required",
                    True,
                )
            ),
            read_only=bool(
                data.get(
                    "read_only",
                    False,
                )
            ),
            allow_negative=bool(
                data.get(
                    "allow_negative",
                    True,
                )
            ),
            allow_zero=bool(
                data.get(
                    "allow_zero",
                    True,
                )
            ),
            finite_only=bool(
                data.get(
                    "finite_only",
                    True,
                )
            ),

            # --------------------------------------------------
            # Solver Metadata
            # --------------------------------------------------
            variable_role=VariableRole(
                data.get(
                    "variable_role",
                    VariableRole.INPUT.value,
                )
            ),

            # --------------------------------------------------
            # Provenance
            # --------------------------------------------------
            source_reference=source_reference,
            source_document=source_document,
            equation_ids=tuple(
                cast(
                    tuple[str, ...] | list[str],
                    data.get(
                        "equation_ids",
                        (),
                    ),
                )
            ),

            # --------------------------------------------------
            # AI Metadata
            # --------------------------------------------------
            aliases=tuple(
                cast(
                    tuple[str, ...] | list[str],
                    data.get(
                        "aliases",
                        (),
                    ),
                )
            ),
            common_names=tuple(
                cast(
                    tuple[str, ...] | list[str],
                    data.get(
                        "common_names",
                        (),
                    ),
                )
            ),
            search_keywords=tuple(
                cast(
                    tuple[str, ...] | list[str],
                    data.get(
                        "search_keywords",
                        (),
                    ),
                )
            ),

            # --------------------------------------------------
            # Lifecycle
            # --------------------------------------------------
            status=VariableStatus(
                data.get(
                    "status",
                    VariableStatus.DRAFT.value,
                )
            ),
        )                                   
    def has_value(
        self,
    ) -> bool:
        """
        Determine whether the Variable currently
        has an assigned value.

        Returns
        -------
        bool
            True if a value has been assigned.
        """

        return self.value is not None

    def is_numeric(
        self,
    ) -> bool:
        """
        Determine whether this Variable represents
        a numeric engineering quantity.

        Returns
        -------
        bool
        """

        return self.variable_type in (
            VariableType.FLOAT,
            VariableType.INTEGER,
        )  
     
    def is_required(
        self,
    ) -> bool:
        """
        Determine whether this Variable is mandatory.

        Returns
        -------
        bool
        """

        return self.required 
    
    def is_input_variable(
        self,
    ) -> bool:
        """
        Determine whether the Variable is a solver input.

        Returns
        -------
        bool
        """

        return (
            self.variable_role
            is VariableRole.INPUT
        )
    
    def is_output_variable(
        self,
    ) -> bool:
        """
        Determine whether the Variable is a solver output.

        Returns
        -------
        bool
        """

        return (
            self.variable_role
            is VariableRole.OUTPUT
        )
    
    def uses_si_units(
        self,
    ) -> bool:
        """
        Determine whether the Variable is displayed
        using its SI unit.

        Returns
        -------
        bool
            True if the display unit is omitted or
            identical to the SI unit.
        """

        return (
            self.display_unit is None
            or self.display_unit == self.si_unit
        )
    
    def matches_alias(
        self,
        alias: str,
    ) -> bool:
        """
        Determine whether the supplied alias matches
        one of the Variable aliases.

        Parameters
        ----------
        alias : str

        Returns
        -------
        bool
        """

        normalized = alias.strip().casefold()

        return any(
            item.casefold() == normalized
            for item in self.aliases
        )
    
    def matches_keyword(
        self,
        keyword: str,
    ) -> bool:
        """
        Determine whether a search keyword is associated
        with this Variable.

        Parameters
        ----------
        keyword : str

        Returns
        -------
        bool
        """

        normalized = keyword.strip().casefold()

        return any(
            item.casefold() == normalized
            for item in self.search_keywords
        )
    
    def display_name(
        self,
    ) -> str:
        """
        Return a concise engineering display name.

        Returns
        -------
        str

        Examples
        --------
        Chamber Pressure (Pc)

        Temperature (T)

        Density (ρ)
        """

        symbol = self.symbol.strip()

        if symbol:
            return (
                f"{self.name} "
                f"({symbol})"
            )

        return self.name
    
