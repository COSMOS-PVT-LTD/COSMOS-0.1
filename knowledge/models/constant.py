"""
COSMOS Knowledge Foundation

Module
------
knowledge.models.constant

Purpose
-------
Defines the immutable Constant model used throughout the
COSMOS Knowledge Foundation.

A Constant represents a validated engineering constant used
by the physics engines, optimization framework, numerical
solvers, AI knowledge systems, and engineering repositories.

The Constant model is the canonical representation of all
engineering constants within COSMOS.

Design Goals
------------
* Immutable
* Thread-safe
* Fully typed
* Fully validated
* Deterministic
* Repository-ready
* AI-ready
* Future symbolic mathematics compatible

This module intentionally contains no numerical evaluation,
unit conversion, symbolic algebra, or repository logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final, cast, Iterable
from datetime import datetime

from knowledge.models.document import Document
from knowledge.models.reference import Reference
from knowledge.models.variable import EngineeringDomain


# ==========================================================
# Enumerations
# ==========================================================


class ConstantType(Enum):
    """
    Classification of engineering constants.
    """

    PHYSICAL = "PHYSICAL"
    THERMODYNAMIC = "THERMODYNAMIC"
    MATERIAL = "MATERIAL"
    CHEMICAL = "CHEMICAL"
    NUMERICAL = "NUMERICAL"
    EMPIRICAL = "EMPIRICAL"
    ASTRONOMICAL = "ASTRONOMICAL"
    MATHEMATICAL = "MATHEMATICAL"
    UNIVERSAL = "UNIVERSAL"
    USER_DEFINED = "USER_DEFINED"


class ConstantStatus(Enum):
    """
    Lifecycle status of a Constant.
    """

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    OBSOLETE = "OBSOLETE"


class PreferredNumericType(Enum):
    """
    Preferred numerical representation used by
    scientific computing backends.
    """

    FLOAT32 = "FLOAT32"
    FLOAT64 = "FLOAT64"
    DECIMAL = "DECIMAL"
    FRACTION = "FRACTION"
    SYMBOLIC = "SYMBOLIC"


# ==========================================================
# Module Constants
# ==========================================================

DEFAULT_SERIALIZATION_VERSION: Final[str] = "1.0"

DEFAULT_REPOSITORY_NAMESPACE: Final[str] = (
    "COSMOS_KNOWLEDGE_FOUNDATION"
)

# ==========================================================
# Constant Model
# ==========================================================


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Constant:
    """
    Immutable engineering constant.

    A Constant represents a validated engineering quantity
    whose value does not change during numerical evaluation.

    The Constant model is the canonical representation of
    engineering constants throughout COSMOS.

    The object is intentionally immutable to guarantee
    deterministic behaviour and future thread safety.
    """

    # ======================================================
    # Identity
    # ======================================================

    constant_id: str
    """
    Globally unique identifier.
    """

    name: str
    """
    Human-readable constant name.
    """

    symbol: str
    """
    Engineering symbol.

    Examples
    --------
    R
    g
    c
    σ
    """

    description: str
    """
    Engineering description.
    """

    constant_type: ConstantType
    """
    Classification of the engineering constant.
    """

    constant_version: str = "1.0"
    """
    Version of this constant definition.
    """

    # ======================================================
    # Numerical Information
    # ======================================================

    value: float | int | bool | str | None = None
    """
    Numerical value of the constant.
    """

    default_value: float | int | bool | str | None = None
    """
    Default value.
    """

    minimum_value: float | None = None
    """
    Minimum permissible value.
    """

    maximum_value: float | None = None
    """
    Maximum permissible value.
    """

    precision: float | None = None
    """
    Numerical precision.
    """

    uncertainty: float | None = None
    """
    Absolute measurement uncertainty.
    """

    relative_uncertainty: float | None = None
    """
    Relative measurement uncertainty.
    """

    significant_figures: int | None = None
    """
    Number of significant figures.
    """

    exact_value: bool = False
    """
    Indicates whether the value is exact.
    """

    is_fundamental: bool = False
    """
    True if this is a fundamental physical constant.
    """

    # ======================================================
    # Unit Information
    # ======================================================

    si_unit: str
    """
    Canonical SI unit.
    """

    display_unit: str | None = None
    """
    Preferred display unit.
    """

    dimension: str
    """
    Engineering dimension.

    Examples
    --------
    Pressure
    Energy
    Force
    Temperature
    """

    # ======================================================
    # Base SI Dimensions
    # ======================================================

    kg: int = 0
    """
    Kilogram exponent.
    """

    m: int = 0
    """
    Metre exponent.
    """

    s: int = 0
    """
    Second exponent.
    """

    A: int = 0
    """
    Ampere exponent.
    """

    K: int = 0
    """
    Kelvin exponent.
    """

    mol: int = 0
    """
    Mole exponent.
    """

    cd: int = 0
    """
    Candela exponent.
    """

    # ======================================================
    # Engineering Metadata
    # ======================================================

    engineering_domain: EngineeringDomain = EngineeringDomain.GENERAL
    """
    Primary engineering domain.
    """

    subsystem: str | None = None
    """
    Applicable subsystem.
    """

    discipline: str | None = None
    """
    Engineering discipline.
    """

    physical_meaning: str | None = None
    """
    Physical interpretation of the constant.
    """

    engineering_notes: str | None = None
    """
    Engineering notes.
    """

    applicable_system: str | None = None
    """
    Applicable engineering system.
    """

    # ======================================================
    # Engineering Applicability
    # ======================================================

    applicable_regimes: tuple[str, ...] = ()
    """
    Applicable operating regimes.
    """

    temperature_limits: tuple[float, float] | None = None
    """
    Valid temperature range.
    """

    pressure_limits: tuple[float, float] | None = None
    """
    Valid pressure range.
    """

    mach_limits: tuple[float, float] | None = None
    """
    Valid Mach-number range.
    """

    reynolds_limits: tuple[float, float] | None = None
    """
    Valid Reynolds-number range.
    """

    # ======================================================
    # Provenance
    # ======================================================

    source_reference: Reference | None = None
    """
    Primary engineering reference.
    """

    source_document: Document | None = None
    """
    Source document.
    """

    equation_ids: tuple[str, ...] = ()
    """
    Related equation identifiers.
    """

    # ======================================================
    # Scientific Metadata
    # ======================================================

    codata_version: str | None = None
    """
    CODATA release.
    """

    si_definition_year: int | None = None
    """
    SI definition year.
    """

    nist_identifier: str | None = None
    """
    NIST identifier.
    """

    iso_reference: str | None = None
    """
    ISO reference.
    """

    measurement_reference: Reference | None = None
    """
    Measurement reference.
    """

    # ======================================================
    # Computational Metadata
    # ======================================================

    preferred_numeric_type: PreferredNumericType = (
        PreferredNumericType.FLOAT64
    )

    supports_float32: bool = True
    supports_float64: bool = True
    supports_decimal: bool = False
    supports_symbolic: bool = False

    # ======================================================
    # AI Metadata
    # ======================================================

    aliases: tuple[str, ...] = ()
    """
    Alternative names.
    """

    common_names: tuple[str, ...] = ()
    """
    Common engineering names.
    """

    search_keywords: tuple[str, ...] = ()
    """
    Search keywords.
    """

    normalized_name: str | None = None
    """
    Normalized name.
    """

    normalized_symbol: str | None = None
    """
    Normalized symbol.
    """

    abbreviations: tuple[str, ...] = ()
    """
    Accepted abbreviations.
    """

    legacy_names: tuple[str, ...] = ()
    """
    Historical names.
    """

    # ======================================================
    # Knowledge Foundation Metadata
    # ======================================================

    knowledge_tags: tuple[str, ...] = ()
    ontology_category: str | None = None
    knowledge_level: str | None = None

    related_constants: tuple[str, ...] = ()
    related_equations: tuple[str, ...] = ()

    # ======================================================
    # Repository Metadata
    # ======================================================

    repository_key: str | None = None

    repository_namespace: str = (
        DEFAULT_REPOSITORY_NAMESPACE
    )

    repository_version: str = (
        DEFAULT_SERIALIZATION_VERSION
    )

    # ======================================================
    # Lifecycle & Governance
    # ======================================================

    status: ConstantStatus = ConstantStatus.DRAFT

    validation_state: str | None = None
    verification_level: str | None = None
    review_status: str | None = None

    created_by: str | None = None
    approved_by: str | None = None
    reviewed_by: str | None = None

    created_timestamp: datetime | None = None
    approved_timestamp: datetime | None = None

    revision_notes: str | None = None

    deprecated_since: str | None = None
    replacement_constant: str | None = None
    deprecation_reason: str | None = None

    # ======================================================
    # Future Symbolic Mathematics
    # ======================================================

    sympy_symbol: str | None = None
    canonical_symbol: str | None = None
    latex_symbol: str | None = None
    unicode_symbol: str | None = None

    # ======================================================
    # AI / Knowledge Graph Integration
    # ======================================================

    embedding_id: str | None = None
    semantic_category: str | None = None
    llm_description: str | None = None

    # ======================================================
    # Performance Metadata
    # ======================================================

    cacheable: bool = True
    serialization_version: str = (
        DEFAULT_SERIALIZATION_VERSION
    )

    # ======================================================
    # Interoperability
    # ======================================================

    export_name: str | None = None

    export_aliases: tuple[str, ...] = ()

    external_identifiers: tuple[str, ...] = ()

    # ======================================================
    # Quality Metrics
    # ======================================================

    verification_status: str | None = None
    validation_status: str | None = None
    confidence_level: float | None = None

    # ======================================================
    # Construction
    # ======================================================

    def __post_init__(self) -> None:
        """Validate the constant after construction."""

        self.validate()

    # ======================================================
    # Validation
    # ======================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the complete Constant object.

        Validation is delegated to specialized private
        validator methods to keep responsibilities
        separated and the implementation maintainable.

        Raises
        ------
        ValueError
            If any validation rule fails.
        """

        self._validate_constant_id()
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

        self._validate_scientific_metadata()

        self._validate_repository_metadata()

        self._validate_lifecycle()

        self._validate_future_metadata()

    # ======================================================
    # Core Validators
    # ======================================================

    def _validate_constant_id(self) -> None:
        if not isinstance(
            self.constant_id,
            str,
        ):
            raise TypeError(
                "constant_id must be a string."
            )

        if not self.constant_id.strip():
            raise ValueError(
                "constant_id cannot be blank."
            )

    def _validate_name(
        self,
    ) -> None:
        """
        Validate the constant name.

        Raises
        ------
        ValueError
            If the name is invalid.
        """

        if not isinstance(
            self.name,
            str,
        ):
            raise TypeError(
                "name must be a string."
            )
        print(f"DEBUG NAME = {repr(self.name)}")

        if not self.name.strip():
            raise ValueError(
                "name cannot be blank."
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

        if not isinstance(self.symbol, str):
            raise TypeError(
                "symbol must be a string."
            )
        print(f"DEBUG SYMBOL = {repr(self.symbol)}")

        if not self.symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )

    def _validate_value(
        self,
    ) -> None:
        """
        Validate the numerical value.

        Raises
        ------
        TypeError
            If the value type is unsupported.
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
                "value has an unsupported type."
            )

        if isinstance(
            self.value,
            str,
        ) and not self.value.strip():
            raise ValueError(
                "value cannot be an empty string."
            )

    def _validate_units(
        self,
    ) -> None:
        """
        Validate unit metadata.

        Raises
        ------
        ValueError
            If unit information is invalid.
        """

        if not isinstance(
            self.si_unit,
            str,
        ):
            raise TypeError(
                "si_unit must be a string."
            )

        if not self.si_unit.strip():
            raise ValueError(
                "si_unit cannot be empty."
            )

        if (
            self.display_unit is not None
            and not isinstance(
                self.display_unit,
                str,
            )
        ):
            raise TypeError(
                "display_unit must be a string."
            )

        if (
            isinstance(
                self.display_unit,
                str,
            )
            and not self.display_unit.strip()
        ):
            raise ValueError(
                "display_unit cannot be empty."
            )

        if not isinstance(
            self.dimension,
            str,
        ):
            raise TypeError(
                "dimension must be a string."
            )

        if not self.dimension.strip():
            raise ValueError(
                "dimension cannot be empty."
            )

    def _validate_bounds(
        self,
    ) -> None:
        """
        Validate numerical bounds.

        Raises
        ------
        ValueError
            If minimum_value exceeds maximum_value.
        """

        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.minimum_value
            > self.maximum_value
        ):
            raise ValueError(
                "minimum_value cannot be greater "
                "than maximum_value."
            )

        if (
            self.precision is not None
            and self.precision <= 0.0
        ):
            raise ValueError(
                "precision must be greater than zero."
            )

        if (
            self.uncertainty is not None
            and self.uncertainty < 0.0
        ):
            raise ValueError(
                "uncertainty cannot be negative."
            )

        if (
            self.relative_uncertainty is not None
            and self.relative_uncertainty < 0.0
        ):
            raise ValueError(
                "relative_uncertainty cannot be "
                "negative."
            )

        if (
            self.significant_figures is not None
            and self.significant_figures <= 0
        ):
            raise ValueError(
                "significant_figures must be "
                "greater than zero."
            )

    # ======================================================
    # Metadata Validators
    # ======================================================

    def _validate_reference(
        self,
    ) -> None:
        """
        Validate the source reference.

        Raises
        ------
        TypeError
            If the reference is invalid.
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
                "instance or None."
            )

        if (
            self.measurement_reference is not None
            and not isinstance(
                self.measurement_reference,
                Reference,
            )
        ):
            raise TypeError(
                "measurement_reference must be a "
                "Reference instance or None."
            )

    def _validate_document(
        self,
    ) -> None:
        """
        Validate the source document.

        Raises
        ------
        TypeError
            If the document is invalid.
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
                "instance or None."
            )

    def _validate_aliases(
        self,
    ) -> None:
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
                    "aliases cannot contain "
                    "empty strings."
                )

    def _validate_common_names(
        self,
    ) -> None:
        """
        Validate common engineering names.

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
                    "Each common name must "
                    "be a string."
                )

            if not name.strip():
                raise ValueError(
                    "common_names cannot "
                    "contain empty strings."
                )

    def _validate_search_keywords(
        self,
    ) -> None:
        """
        Validate search keywords.

        Raises
        ------
        TypeError
            If keywords are invalid.
        """

        if not isinstance(
            self.search_keywords,
            tuple,
        ):
            raise TypeError(
                "search_keywords must be a tuple."
            )

        for keyword in self.search_keywords:
            if not isinstance(
                keyword,
                str,
            ):
                raise TypeError(
                    "Each search keyword "
                    "must be a string."
                )

            if not keyword.strip():
                raise ValueError(
                    "search_keywords cannot "
                    "contain empty strings."
                )

    def _validate_engineering_metadata(
        self,
    ) -> None:
        """
        Validate engineering metadata.

        Raises
        ------
        TypeError
            If metadata is invalid.
        """

        if not isinstance(
            self.engineering_domain,
            EngineeringDomain,
        ):
            raise TypeError(
                "engineering_domain must be an "
                "EngineeringDomain."
            )

        text_fields = (
            ("subsystem", self.subsystem),
            ("discipline", self.discipline),
            (
                "physical_meaning",
                self.physical_meaning,
            ),
            (
                "engineering_notes",
                self.engineering_notes,
            ),
            (
                "applicable_system",
                self.applicable_system,
            ),
            (
                "ontology_category",
                self.ontology_category,
            ),
            (
                "knowledge_level",
                self.knowledge_level,
            ),
        )

        for field_name, text_value in text_fields:
            if text_value is None:
                continue

            if not isinstance(
                text_value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be "
                    "a string."
                )

            if not text_value.strip():
                raise ValueError(
                    f"{field_name} cannot "
                    "be empty."
                )

        tuple_fields = (
            (
                "applicable_regimes",
                self.applicable_regimes,
            ),
            (
                "knowledge_tags",
                self.knowledge_tags,
            ),
            (
                "related_constants",
                self.related_constants,
            ),
            (
                "related_equations",
                self.related_equations,
            ),
            (
                "equation_ids",
                self.equation_ids,
            ),
        )

        for field_name, values in tuple_fields:
            if not isinstance(
                values,
                tuple,
            ):
                raise TypeError(
                    f"{field_name} must be "
                    "a tuple."
                )

            for item in values:
                if not isinstance(
                    item,
                    str,
                ):
                    raise TypeError(
                        f"Each item in "
                        f"{field_name} "
                        "must be a string."
                    )

                if not item.strip():
                    raise ValueError(
                        f"{field_name} cannot "
                        "contain empty strings."
                    )

    # ======================================================
    # Scientific Metadata Validators
    # ======================================================

    def _validate_scientific_metadata(
        self,
    ) -> None:
        """
        Validate scientific metadata.

        Raises
        ------
        TypeError
            If metadata types are invalid.

        ValueError
            If metadata values are invalid.
        """

        if (
            self.codata_version is not None
            and not isinstance(
                self.codata_version,
                str,
            )
        ):
            raise TypeError(
                "codata_version must be a string."
            )

        if (
            self.si_definition_year is not None
            and not isinstance(
                self.si_definition_year,
                int,
            )
        ):
            raise TypeError(
                "si_definition_year must be an integer."
            )

        if (
            self.si_definition_year is not None
            and self.si_definition_year <= 0
        ):
            raise ValueError(
                "si_definition_year must be positive."
            )

        text_fields = (
            ("nist_identifier", self.nist_identifier),
            ("iso_reference", self.iso_reference),
        )

        for field_name, text_value in text_fields:
            if text_value is None:
                continue

            if not isinstance(text_value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not text_value.strip():
                raise ValueError(
                    f"{field_name} cannot be blank."
                )

    # ======================================================
    # Repository Metadata Validators
    # ======================================================

    def _validate_repository_metadata(
        self,
    ) -> None:
        """
        Validate repository metadata.
        """

        text_fields = (
            ("repository_key", self.repository_key),
            (
                "repository_namespace",
                self.repository_namespace,
            ),
            (
                "repository_version",
                self.repository_version,
            ),
            (
                "serialization_version",
                self.serialization_version,
            ),
        )

        for field_name, text_value in text_fields:
            if text_value is None:
                continue

            if not isinstance(text_value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not text_value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

    # ======================================================
    # Lifecycle Validators
    # ======================================================

    def _validate_lifecycle(
        self,
    ) -> None:
        """
        Validate lifecycle and governance metadata.
        """

        if not isinstance(
            self.status,
            ConstantStatus,
        ):
            raise TypeError(
                "status must be a ConstantStatus."
            )

        text_fields = (
            ("validation_state", self.validation_state),
            ("verification_level", self.verification_level),
            ("review_status", self.review_status),
            ("created_by", self.created_by),
            ("approved_by", self.approved_by),
            ("reviewed_by", self.reviewed_by),
            ("revision_notes", self.revision_notes),
            ("deprecated_since", self.deprecated_since),
            (
                "replacement_constant",
                self.replacement_constant,
            ),
            (
                "deprecation_reason",
                self.deprecation_reason,
            ),
        )

        for field_name, text_value in text_fields:
            if text_value is None:
                continue

            if not isinstance(text_value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not text_value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

        timestamp_fields = (
            (
                "created_timestamp",
                self.created_timestamp,
            ),
            (
                "approved_timestamp",
                self.approved_timestamp,
            ),
        )

        for field_name, timestamp in timestamp_fields:
            if timestamp is None:
                continue

            if not isinstance(
                timestamp,
                datetime,
            ):
                raise TypeError(
                    f"{field_name} must be a datetime."
                )

    # ======================================================
    # Future Metadata Validators
    # ======================================================

    def _validate_future_metadata(
        self,
    ) -> None:
        """
        Validate future integration metadata.
        """

        text_fields = (
            ("sympy_symbol", self.sympy_symbol),
            ("canonical_symbol", self.canonical_symbol),
            ("latex_symbol", self.latex_symbol),
            ("unicode_symbol", self.unicode_symbol),
            ("embedding_id", self.embedding_id),
            (
                "semantic_category",
                self.semantic_category,
            ),
            (
                "llm_description",
                self.llm_description,
            ),
            ("export_name", self.export_name),
            (
                "verification_status",
                self.verification_status,
            ),
            (
                "validation_status",
                self.validation_status,
            ),
        )

        for field_name, text_value in text_fields:
            if text_value is None:
                continue

            if not isinstance(text_value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not text_value.strip():
                raise ValueError(
                    f"{field_name} cannot be empty."
                )

        tuple_fields = (
            (
                "export_aliases",
                self.export_aliases,
            ),
            (
                "external_identifiers",
                self.external_identifiers,
            ),
        )

        for field_name, values in tuple_fields:
            if not isinstance(
                values,
                tuple,
            ):
                raise TypeError(
                    f"{field_name} must be a tuple."
                )

            for item in values:
                if not isinstance(
                    item,
                    str,
                ):
                    raise TypeError(
                        f"Each item in "
                        f"{field_name} "
                        "must be a string."
                    )

                if not item.strip():
                    raise ValueError(
                        f"{field_name} cannot "
                        "contain empty strings."
                    )

        if (
            self.confidence_level is not None
            and not isinstance(
                self.confidence_level,
                (int, float),
            )
        ):
            raise TypeError(
                "confidence_level must be numeric."
            )

        if (
            self.confidence_level is not None
            and not (
                0.0 <= self.confidence_level <= 1.0
            )
        ):
            raise ValueError(
                "confidence_level must be between "
                "0.0 and 1.0."
            )

    # ======================================================
    # Serialization
    # ======================================================

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Serialize the Constant into a deterministic dictionary.

        Returns
        -------
        dict[str, object]
            Serializable representation of this Constant.
        """

        return {
            # --------------------------------------------------
            # Identity
            # --------------------------------------------------
            "constant_id": self.constant_id,
            "name": self.name,
            "symbol": self.symbol,
            "description": self.description,
            "constant_type": self.constant_type.name,
            "constant_version": self.constant_version,

            # --------------------------------------------------
            # Numerical Information
            # --------------------------------------------------
            "value": self.value,
            "default_value": self.default_value,
            "minimum_value": self.minimum_value,
            "maximum_value": self.maximum_value,
            "precision": self.precision,
            "uncertainty": self.uncertainty,
            "relative_uncertainty": self.relative_uncertainty,
            "significant_figures": self.significant_figures,
            "exact_value": self.exact_value,
            "is_fundamental": self.is_fundamental,

            # --------------------------------------------------
            # Units
            # --------------------------------------------------
            "si_unit": self.si_unit,
            "display_unit": self.display_unit,
            "dimension": self.dimension,
            "kg": self.kg,
            "m": self.m,
            "s": self.s,
            "A": self.A,
            "K": self.K,
            "mol": self.mol,
            "cd": self.cd,

            # --------------------------------------------------
            # Engineering Metadata
            # --------------------------------------------------
            "engineering_domain": self.engineering_domain.name,
            "subsystem": self.subsystem,
            "discipline": self.discipline,
            "physical_meaning": self.physical_meaning,
            "engineering_notes": self.engineering_notes,
            "applicable_system": self.applicable_system,

            "applicable_regimes": list(
                self.applicable_regimes
            ),
            "temperature_limits": self.temperature_limits,
            "pressure_limits": self.pressure_limits,
            "mach_limits": self.mach_limits,
            "reynolds_limits": self.reynolds_limits,

            # --------------------------------------------------
            # Provenance
            # --------------------------------------------------
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

            "equation_ids": list(
                self.equation_ids
            ),

            # --------------------------------------------------
            # Scientific Metadata
            # --------------------------------------------------
            "codata_version": self.codata_version,
            "si_definition_year": self.si_definition_year,
            "nist_identifier": self.nist_identifier,
            "iso_reference": self.iso_reference,

            "measurement_reference": (
                None
                if self.measurement_reference is None
                else self.measurement_reference.to_dict()
            ),

            # --------------------------------------------------
            # Computational Metadata
            # --------------------------------------------------
            "preferred_numeric_type":
                self.preferred_numeric_type.name,

            "supports_float32":
                self.supports_float32,

            "supports_float64":
                self.supports_float64,

            "supports_decimal":
                self.supports_decimal,

            "supports_symbolic":
                self.supports_symbolic,

            # --------------------------------------------------
            # AI Metadata
            # --------------------------------------------------
            "aliases": list(self.aliases),
            "common_names": list(self.common_names),
            "search_keywords": list(
                self.search_keywords
            ),
            "normalized_name":
                self.normalized_name,
            "normalized_symbol":
                self.normalized_symbol,
            "abbreviations":
                list(self.abbreviations),
            "legacy_names":
                list(self.legacy_names),

            # --------------------------------------------------
            # Knowledge Foundation
            # --------------------------------------------------
            "knowledge_tags":
                list(self.knowledge_tags),

            "ontology_category":
                self.ontology_category,

            "knowledge_level":
                self.knowledge_level,

            "related_constants":
                list(self.related_constants),

            "related_equations":
                list(self.related_equations),

            # --------------------------------------------------
            # Repository
            # --------------------------------------------------
            "repository_key":
                self.repository_key,

            "repository_namespace":
                self.repository_namespace,

            "repository_version":
                self.repository_version,

            # --------------------------------------------------
            # Lifecycle
            # --------------------------------------------------
            "status":
                self.status.name,

            "validation_state":
                self.validation_state,

            "verification_level":
                self.verification_level,

            "review_status":
                self.review_status,

            "created_by":
                self.created_by,

            "approved_by":
                self.approved_by,

            "reviewed_by":
                self.reviewed_by,

            "created_timestamp":
                None
                if self.created_timestamp is None
                else self.created_timestamp.isoformat(),

            "approved_timestamp":
                None
                if self.approved_timestamp is None
                else self.approved_timestamp.isoformat(),

            "revision_notes":
                self.revision_notes,

            "deprecated_since":
                self.deprecated_since,

            "replacement_constant":
                self.replacement_constant,

            "deprecation_reason":
                self.deprecation_reason,

            # --------------------------------------------------
            # Future Metadata
            # --------------------------------------------------
            "sympy_symbol":
                self.sympy_symbol,

            "canonical_symbol":
                self.canonical_symbol,

            "latex_symbol":
                self.latex_symbol,

            "unicode_symbol":
                self.unicode_symbol,

            "embedding_id":
                self.embedding_id,

            "semantic_category":
                self.semantic_category,

            "llm_description":
                self.llm_description,

            "cacheable":
                self.cacheable,

            "serialization_version":
                self.serialization_version,

            "export_name":
                self.export_name,

            "export_aliases":
                list(self.export_aliases),

            "external_identifiers":
                list(
                    self.external_identifiers
                ),

            "verification_status":
                self.verification_status,

            "validation_status":
                self.validation_status,

            "confidence_level":
                self.confidence_level,
        }

    # ======================================================
    # Deserialization
    # ======================================================
    
    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Constant":
        """
        Reconstruct a Constant from its serialized
        dictionary representation.

        Parameters
        ----------
        data : dict[str, object]

        Returns
        -------
        Constant

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

        source_reference = (
            None
            if data.get("source_reference") is None
            else cls._deserialize_reference(
                data.get("source_reference")
            )
        )

        source_document = (
            None
            if data.get("source_document") is None
            else cls._deserialize_document( 
                data.get("source_document")
            )
        )

        measurement_reference = (
            None
            if data.get(
                "measurement_reference"
            ) is None
            else cls._deserialize_reference(
                data.get("measurement_reference")
            )
        )

        created_timestamp = (
            None
            if data.get("created_timestamp") is None
            else cls._deserialize_datetime(
                # Ensure the value passed is a string (or None). Some callers
                # may provide non-str types; coerce to str to satisfy the
                # type expectation of _deserialize_datetime.
                str(data.get("created_timestamp"))
            )
        )

        approved_timestamp = (
            None
            if data.get(
                "approved_timestamp"
            ) is None
            else cls._deserialize_datetime(
                # Ensure the value passed is a string (or None). Some callers
                # may provide non-str types; coerce to str to satisfy the
                # type expectation of _deserialize_datetime.
                str(data.get("approved_timestamp"))
            )
        )
        # Coerce identity fields to strings

        raw_constant_id = data["constant_id"]

        if not isinstance(raw_constant_id, str):
            raise TypeError(
                "constant_id must be a string."
            )

        constant_id = raw_constant_id

        raw_name = data["name"]
        if not isinstance(raw_name, str):
            raise TypeError(
                "name must be a string."
            )
        name = raw_name
        if not raw_name.strip():
            raise ValueError(
                "name cannot be blank."
            )
        name=name

        raw_symbol = data["symbol"]
        if not isinstance(raw_symbol, str):
            raise TypeError(
                "symbol must be a string."
            )
        symbol = raw_symbol
        if not symbol.strip():
            raise ValueError(
                "symbol cannot be blank."
            )
        symbol=symbol

        raw_description = data["description"]
        if not isinstance(raw_description, str):
            raise TypeError(
                "description must be a string."
            )
        description = raw_description
        if not description.strip():
            raise ValueError(
                "description cannot be blank."
            )
        description = description

        raw_value = data.get("value")
        if raw_value is None:
            value = None
        elif isinstance(raw_value, (float, int, bool, str)):
            value = raw_value
        else:
            value = None

        raw_default_value = data.get("default_value")
        if raw_default_value is None:
            default_value = None
        elif isinstance(raw_default_value, (float, int, bool, str)):
            default_value = raw_default_value
        else:
            default_value = None

        raw_minimum_value = data.get("minimum_value")
        if raw_minimum_value is None:
            minimum_value = None
        elif isinstance(raw_minimum_value, float):
            minimum_value = raw_minimum_value
        else:
            minimum_value = None

        raw_maximum_value = data.get("maximum_value")
        if raw_maximum_value is None:
            maximum_value = None
        elif isinstance(raw_maximum_value, float):
            maximum_value = raw_maximum_value
        else:
            maximum_value = None

        raw_precision = data.get("precision")
        if raw_precision is None:
            precision = None
        elif isinstance(raw_precision, float):
            precision = raw_precision
        else:
            precision = None

        raw_uncertainty = data.get("uncertainty")
        if raw_uncertainty is None:
            uncertainty = None
        elif isinstance(raw_uncertainty, float):
            uncertainty = raw_uncertainty
        else:
            uncertainty = None

        raw_relative_uncertainty = data.get("relative_uncertainty")
        if raw_relative_uncertainty is None:
            relative_uncertainty = None
        elif isinstance(raw_relative_uncertainty, float):
            relative_uncertainty = raw_relative_uncertainty
        else:
            relative_uncertainty = None

        raw_significant_figures = data.get("significant_figures")
        if raw_significant_figures is None:
            significant_figures = None
        elif isinstance(raw_significant_figures, int):
            significant_figures = raw_significant_figures
        else:
            significant_figures = None

        raw_exact_value = data.get("exact_value")
        if raw_exact_value is None:
            exact_value = False
        elif isinstance(raw_exact_value, bool):
            exact_value = raw_exact_value
        else:
            exact_value = False

        raw_is_fundamental = data.get("is_fundamental")
        if raw_is_fundamental is None:
            is_fundamental = False
        elif isinstance(raw_is_fundamental, bool):
            is_fundamental = raw_is_fundamental
        else:
            is_fundamental = False

        raw_applicable_regimes = data.get("applicable_regimes")
        applicable_regimes = tuple(raw_applicable_regimes) if isinstance(raw_applicable_regimes, (list, tuple)) else ()

        raw_temperature_limits = data.get("temperature_limits")
        temperature_limits = None if raw_temperature_limits is None else tuple(raw_temperature_limits) if isinstance(raw_temperature_limits, (list, tuple)) else None

        raw_pressure_limits = data.get("pressure_limits")
        pressure_limits = None if raw_pressure_limits is None else tuple(raw_pressure_limits) if isinstance(raw_pressure_limits, (list, tuple)) else None

        raw_mach_limits = data.get("mach_limits")
        mach_limits = None if raw_mach_limits is None else tuple(raw_mach_limits) if isinstance(raw_mach_limits, (list, tuple)) else None

        raw_reynolds_limits = data.get("reynolds_limits")
        reynolds_limits = None if raw_reynolds_limits is None else tuple(raw_reynolds_limits) if isinstance(raw_reynolds_limits, (list, tuple)) else None

        raw_equation_ids = data.get("equation_ids")
        equation_ids = tuple(raw_equation_ids) if isinstance(raw_equation_ids, (list, tuple)) else ()

        try:
            # Ensure the key used for enum lookup is a string to satisfy typing
            constant_type = ConstantType(data["constant_type"])
        except Exception as exc:
            raise ValueError("Invalid ConstantType.") from exc
        print("RETURN NAME:", repr(name))
        print("RETURN SYMBOL:", repr(symbol))
        print("RETURN ID:", repr(constant_id))

        return cls(

            # --------------------------------------------------
            # Identity
            # --------------------------------------------------

            constant_id=constant_id,
            name=name,
            symbol=symbol,
            description=description,
            constant_type=constant_type,

            # --------------------------------------------------
            # Numerical Information
            # --------------------------------------------------

            value=value,

            default_value=default_value,

            minimum_value=minimum_value,

            maximum_value=maximum_value,

            precision=precision,

            uncertainty=uncertainty,

            relative_uncertainty=relative_uncertainty,

            significant_figures=significant_figures,

            exact_value=exact_value,

            is_fundamental=is_fundamental,

            # --------------------------------------------------
            # Units
            # --------------------------------------------------

            si_unit=str(data["si_unit"]),

            display_unit=(lambda v: str(v) if v is not None else None)(data.get("display_unit")),

            dimension=(str(data["dimension"])),

            kg=int(str(data.get("kg", 0))),
            m=int(str(data.get("m", 0))),
            s=int(str(data.get("s", 0))),
            A=int(str(data.get("A", 0))),
            K=int(str(data.get("K", 0))),
            mol=int(str(data.get("mol", 0))),
            cd=int(str(data.get("cd", 0))),

            # --------------------------------------------------
            # Engineering Metadata
            # --------------------------------------------------

            engineering_domain=EngineeringDomain[
                str(
                data.get(
                    "engineering_domain",
                    "GENERAL",
                ))
            ],

            subsystem=(lambda v: str(v) if v is not None else None)(data.get("subsystem")),

            discipline=(lambda v: str(v) if v is not None else None)(data.get("discipline")),

            physical_meaning=(lambda v: str(v) if v is not None else None)(data.get("physical_meaning")),

            engineering_notes=(lambda v: str(v) if v is not None else None)(data.get("engineering_notes")),

            applicable_system=(lambda v: str(v) if v is not None else None)(data.get("applicable_system")),

            applicable_regimes=applicable_regimes,

            temperature_limits=temperature_limits,

            pressure_limits=pressure_limits,

            mach_limits=mach_limits,

            reynolds_limits=reynolds_limits,

            # --------------------------------------------------
            # Provenance
            # --------------------------------------------------

            source_reference=source_reference,

            source_document=source_document,

            equation_ids=equation_ids,

            # --------------------------------------------------
            # Scientific Metadata
            # --------------------------------------------------

            codata_version=(lambda v: str(v) if v is not None else None)(
                data.get(
                    "codata_version"
                )
            ),

            si_definition_year=(lambda v: int(str(v)) if v is not None else None)(
                data.get(
                    "si_definition_year"
                )
            ),

            nist_identifier=(lambda v: str(v) if v is not None else None)(
                data.get(
                    "nist_identifier"
                )
            ),

            iso_reference=(lambda v: str(v) if v is not None else None)(
                data.get(
                    "iso_reference"
                )
            ),

            measurement_reference=(
                measurement_reference
            ),

            # --------------------------------------------------
            # Computational Metadata
            # --------------------------------------------------

            preferred_numeric_type=(
                PreferredNumericType[
                    str(
                        data.get(
                            "preferred_numeric_type",
                            "FLOAT64",
                        )
                    )
                ]
            ),

            supports_float32=bool(
                data.get(
                    "supports_float32",
                    True,
                )
            ),

            supports_float64=bool(
                data.get(
                    "supports_float64",
                    True,
                )
            ),

            supports_decimal=bool(
                data.get(
                    "supports_decimal",
                    False,
                )
            ),

            supports_symbolic=bool(
                data.get(
                    "supports_symbolic",
                    False,
                )
            ),

            # --------------------------------------------------
            # AI Metadata
            # --------------------------------------------------

            aliases=tuple(
                cast(Iterable, data.get(
                    "aliases",
                    [],
                ))
            ),

            common_names=tuple(
                cast(Iterable, data.get(
                    "common_names",
                    [],
                ))
            ),

            search_keywords=tuple(
                cast(Iterable, data.get(
                    "search_keywords",
                    [],
                ))
            ),

            normalized_name=(lambda v: str(v) if v is not None else None)(
                data.get(
                    "normalized_name"
                )
            ),

            normalized_symbol=(lambda v: str(v) if v is not None else None)(
                data.get(
                    "normalized_symbol"
                )
            ),

            abbreviations=tuple(
                cast(Iterable, data.get(
                    "abbreviations",
                    [],
                ))
            ),

            legacy_names=tuple(
                cast(Iterable, data.get(
                    "legacy_names",
                    [],
                ))
            ),

            # --------------------------------------------------
            # Knowledge Foundation
            # --------------------------------------------------

            knowledge_tags=tuple(
                cast(Iterable, data.get(
                    "knowledge_tags",
                    [],
                ))
            ),

            ontology_category=cast(str | None, data.get(
                "ontology_category"
            )),

            knowledge_level=cast(str | None, data.get(
                "knowledge_level"
            )),

            related_constants=tuple(
                cast(Iterable, data.get(
                    "related_constants",
                    [],
                ))
            ),

            related_equations=tuple(
                cast(Iterable, data.get(
                    "related_equations",
                    [],
                ))
            ),

            # --------------------------------------------------
            # Repository
            # --------------------------------------------------

            repository_key=cast(str | None, data.get(
                "repository_key"
            )),

            repository_namespace=str(
                data.get(
                    "repository_namespace",
                    DEFAULT_REPOSITORY_NAMESPACE,
                )
            ),

            repository_version=str(
                data.get(
                    "repository_version",
                    DEFAULT_SERIALIZATION_VERSION,
                )
            ),

            # --------------------------------------------------
            # Lifecycle
            # --------------------------------------------------

            status=ConstantStatus[
                cast(str, data.get(
                    "status",
                    "DRAFT",
                ))
            ],

            validation_state=cast(str | None, data.get(
                "validation_state"
            )),

            verification_level=cast(str | None, data.get(
                "verification_level"
            )),

            review_status=cast(str | None, data.get(
                "review_status"
            )),

            created_by=cast(str | None, data.get(
                "created_by"
            )),

            approved_by=cast(str | None, data.get(
                "approved_by"
            )),

            reviewed_by=cast(str | None, data.get(
                "reviewed_by"
            )),

            created_timestamp=created_timestamp,

            approved_timestamp=approved_timestamp,

            revision_notes=cast(str | None, data.get(
                "revision_notes"
            )),

            deprecated_since=cast(str | None, data.get(
                "deprecated_since"
            )),

            replacement_constant=cast(str | None, data.get(
                "replacement_constant"
            )),

            deprecation_reason=cast(str | None, data.get(
                "deprecation_reason"
            )),

            # --------------------------------------------------
            # Future Metadata
            # --------------------------------------------------

            sympy_symbol=cast(str | None, data.get(
                "sympy_symbol"
            )),

            canonical_symbol=cast(str | None, data.get(
                "canonical_symbol"
            )),

            latex_symbol=cast(str | None, data.get(
                "latex_symbol"
            )),

            unicode_symbol=cast(str | None, data.get(
                "unicode_symbol"
            )),

            embedding_id=cast(str | None, data.get(
                "embedding_id"
            )),

            semantic_category=cast(str | None, data.get(
                "semantic_category"
            )),

            llm_description=cast(str | None, data.get(
                "llm_description"
            )),

            cacheable=bool(
                data.get(
                    "cacheable",
                    True,
                )
            ),

            serialization_version=str(
                data.get(
                    "serialization_version",
                    DEFAULT_SERIALIZATION_VERSION,
                )
            ),

            export_name=cast(str | None, data.get(
                "export_name"
            )),

            export_aliases=tuple(
                cast(Iterable, data.get(
                    "export_aliases",
                    [],
                ))
            ),

            external_identifiers=tuple(
                cast(Iterable, data.get(
                    "external_identifiers",
                    [],
                ))
            ),

            verification_status=cast(str | None, data.get(
                "verification_status"
            )),

            validation_status=cast(str | None, data.get(
                "validation_status"
            )),

            confidence_level=(
                lambda v: float(cast(str | int | float, v)) if v is not None else None
            )(
                data.get(
                    "confidence_level"
                )
            ),
        )

    # ======================================================
    # Serialization Helpers
    # ======================================================

    @staticmethod
    def _serialize_datetime(
        value: datetime | None,
    ) -> str | None:
        """
        Serialize a datetime object to an ISO-8601 string.

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
        Deserialize an ISO-8601 string into a datetime.

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
        Serialize a Reference object.
        """

        if reference is None:
            return None

        return reference.to_dict()

    @staticmethod
    def _serialize_document(
        document: Document | None,
    ) -> dict[str, object] | None:
        """
        Serialize a Document object.
        """

        if document is None:
            return None

        return document.to_dict()

    @staticmethod
    def _deserialize_reference(
        payload: object,
    ) -> Reference | None:
        """
        Deserialize a Reference object.
        """

        if payload is None:
            return None

        if not isinstance(payload, dict):
            raise TypeError(
                "Reference payload must be a dictionary."
            )
        return Reference.from_dict(payload)

    @staticmethod
    def _deserialize_document(
        payload: object,
    ) -> Document | None:
        """
        Deserialize a Document object.
        """

        if payload is None:
            return None

        if not isinstance(payload, dict):
            raise TypeError(
                "Document payload must be a dictionary."
            )

        return Document.from_dict(payload)

    @staticmethod
    def _tuple_from_iterable(
        value: object,
    ) -> tuple[str, ...]:
        """
        Convert a serialized iterable into an immutable tuple.
        """

        if value is None:
            return ()

        if not isinstance(
            value,
            (list, tuple),
        ):
            raise TypeError(
                "Expected a list or tuple."
            )

        return tuple(str(item) for item in value)
    
    # ======================================================
    # Query & Analysis Methods
    # ======================================================

    def has_value(
        self,
    ) -> bool:
        """
        Return True if the constant has an assigned value.
        """

        return self.value is not None

    def is_numeric(
        self,
    ) -> bool:
        """
        Return True if the constant stores a numeric value.
        """

        return isinstance(
            self.value,
            (int, float),
        ) and not isinstance(
            self.value,
            bool,
        )

    def is_fundamental_constant(
        self,
    ) -> bool:
        """
        Return True if this is a fundamental physical constant.
        """

        return self.is_fundamental

    def uses_si_units(
        self,
    ) -> bool:
        """
        Return True if the display unit matches the SI unit
        or no display unit has been specified.
        """

        if self.display_unit is None:
            return True

        return (
            self.display_unit.strip()
            == self.si_unit.strip()
        )

    def is_dimensionless(
        self,
    ) -> bool:
        """
        Return True if all SI base-dimension exponents are zero.
        """

        return (
            self.kg == 0
            and self.m == 0
            and self.s == 0
            and self.A == 0
            and self.K == 0
            and self.mol == 0
            and self.cd == 0
        )

    def is_exact(
        self,
    ) -> bool:
        """
        Return True if the constant is defined as exact.
        """

        return self.exact_value

    def matches_alias(
        self,
        alias: str,
    ) -> bool:
        """
        Return True if the supplied alias matches one of the
        registered aliases (case-insensitive).

        Parameters
        ----------
        alias : str

        Returns
        -------
        bool
        """

        if not isinstance(alias, str):
            raise TypeError(
                "alias must be a string."
            )

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
        Return True if the supplied keyword matches one of the
        registered search keywords (case-insensitive).

        Parameters
        ----------
        keyword : str

        Returns
        -------
        bool
        """

        if not isinstance(keyword, str):
            raise TypeError(
                "keyword must be a string."
            )

        normalized = keyword.strip().casefold()

        return any(
            item.casefold() == normalized
            for item in self.search_keywords
        )

    def display_name(
        self,
    ) -> str:
        """
        Return the preferred display name.

        Returns
        -------
        str
        """

        if self.symbol.strip():
            return f"{self.name} ({self.symbol})"

        return self.name

    def has_reference(
        self,
    ) -> bool:
        """
        Return True if a source reference is attached.

        Returns
        -------
        bool
        """

        return self.source_reference is not None

    def has_document(
        self,
    ) -> bool:
        """
        Return True if a source document is attached.

        Returns
        -------
        bool
        """

        return self.source_document is not None

    def related_equation_count(
        self,
    ) -> int:
        """
        Return the number of related equations.

        Returns
        -------
        int
        """

        return len(self.related_equations)

    def applicable_regime_count(
        self,
    ) -> int:
        """
        Return the number of applicable operating regimes.

        Returns
        -------
        int
        """

        return len(self.applicable_regimes)

    def knowledge_tag_count(
        self,
    ) -> int:
        """
        Return the number of knowledge tags.

        Returns
        -------
        int
        """

        return len(self.knowledge_tags)

    def export_identifier_count(
        self,
    ) -> int:
        """
        Return the number of external identifiers.

        Returns
        -------
        int
        """

        return len(self.external_identifiers) 


