"""
COSMOS Rocket Propulsion Platform

Module: physics.thermochemistry.propellants
Author: COSMOS Development Team
Version: 0.2.0

Purpose:
    Canonical propellant registry and database interface.

Description:
    Provides immutable propellant definitions, validation,
    serialization, registry management, and database loading
    infrastructure for all propellants used throughout COSMOS.

    This module serves as the single source of truth for
    propellant definitions.

    Propellant records are loaded from external databases and
    are intentionally not hardcoded into the source code.
"""

from __future__ import annotations

# ============================================================================
# Standard Library
# ============================================================================

import json
import re

from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any, Final

# ============================================================================
# COSMOS Core
# ============================================================================

from core.logger import get_logger

# ============================================================================
# Public API
# ============================================================================

__all__ = (
    "Phase",
    "PropellantType",
    "PropellantError",
    "PropellantValidationError",
    "PropellantNotFoundError",
    "DuplicatePropellantError",
)

# ============================================================================
# Module Constants
# ============================================================================

LOGGER: Final = get_logger(__name__)

DEFAULT_DATABASE_FILENAME: Final[str] = (
    "propellants_master.json"
)

DEFAULT_DATABASE_DIRECTORY: Final[str] = (
    "databases"
)

MIN_MOLECULAR_WEIGHT: Final[float] = 0.0
MIN_DENSITY: Final[float] = 0.0
MIN_PRESSURE: Final[float] = 0.0
MIN_TEMPERATURE: Final[float] = 0.0

ALIAS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9_\-\s]+$"
)

# ============================================================================
# Exceptions
# ============================================================================


class PropellantError(Exception):
    """
    Base exception for all propellant-related failures.
    """


class PropellantValidationError(
    PropellantError,
):
    """
    Raised when a propellant definition
    fails validation.
    """


class PropellantNotFoundError(
    PropellantError,
):
    """
    Raised when a requested propellant
    does not exist in the registry.
    """


class DuplicatePropellantError(
    PropellantError,
):
    """
    Raised when duplicate propellant
    names or aliases are detected.
    """


# ============================================================================
# Enumerations
# ============================================================================


class Phase(str, Enum):
    """
    Physical phase of a propellant.

    Values
    ------
    SOLID
    LIQUID
    GAS
    SUPERCRITICAL
    """

    SOLID = "SOLID"
    LIQUID = "LIQUID"
    GAS = "GAS"
    SUPERCRITICAL = "SUPERCRITICAL"


class PropellantType(str, Enum):
    """
    Functional classification of a propellant.

    Values
    ------
    FUEL
    OXIDIZER
    PRESSURANT
    INERT
    """

    FUEL = "FUEL"
    OXIDIZER = "OXIDIZER"
    PRESSURANT = "PRESSURANT"
    INERT = "INERT"


# ============================================================================
# Validation Utilities
# ============================================================================


def _validate_non_empty_string(
    value: str,
    field_name: str,
) -> None:
    """
    Validate non-empty string.

    Parameters
    ----------
    value : str
        Value to validate.

    field_name : str
        Field name.

    Raises
    ------
    PropellantValidationError
    """

    if not isinstance(
        value,
        str,
    ):
        raise PropellantValidationError(
            f"{field_name} must be a string."
        )

    if not value.strip():
        raise PropellantValidationError(
            f"{field_name} cannot be empty."
        )


def _validate_positive_float(
    value: float,
    field_name: str,
) -> None:
    """
    Validate positive float.

    Parameters
    ----------
    value : float
        Value to validate.

    field_name : str
        Field name.

    Raises
    ------
    PropellantValidationError
    """

    if value <= 0.0:
        raise PropellantValidationError(
            f"{field_name} must be positive."
        )


def _validate_non_negative_float(
    value: float,
    field_name: str,
) -> None:
    """
    Validate non-negative float.

    Parameters
    ----------
    value : float
        Value to validate.

    field_name : str
        Field name.

    Raises
    ------
    PropellantValidationError
    """

    if value < 0.0:
        raise PropellantValidationError(
            f"{field_name} cannot be negative."
        )


def _validate_aliases(
    aliases: tuple[str, ...],
) -> None:
    """
    Validate alias collection.

    Parameters
    ----------
    aliases : tuple[str, ...]

    Raises
    ------
    PropellantValidationError
    """

    normalized: set[str] = set()

    for alias in aliases:

        _validate_non_empty_string(
            alias,
            "alias",
        )

        if not ALIAS_PATTERN.match(
            alias,
        ):
            raise PropellantValidationError(
                f"Invalid alias: {alias}"
            )

        alias_key = alias.casefold()

        if alias_key in normalized:
            raise PropellantValidationError(
                f"Duplicate alias: {alias}"
            )

        normalized.add(
            alias_key,
        )


def _validate_elements(
    elements: dict[str, int],
) -> None:
    """
    Validate elemental composition.

    Parameters
    ----------
    elements : dict[str, int]

    Raises
    ------
    PropellantValidationError
    """

    if not isinstance(
        elements,
        dict,
    ):
        raise PropellantValidationError(
            "elements must be a dictionary."
        )

    if not elements:
        raise PropellantValidationError(
            "elements cannot be empty."
        )

    for symbol, count in elements.items():

        _validate_non_empty_string(
            symbol,
            "element symbol",
        )

        if not isinstance(
            count,
            int,
        ):
            raise PropellantValidationError(
                "element count must be integer."
            )

        if count <= 0:
            raise PropellantValidationError(
                "element count must be positive."
            )


def _normalize_key(
    value: str,
) -> str:
    """
    Normalize lookup key.

    Parameters
    ----------
    value : str

    Returns
    -------
    str
    """

    return value.strip().casefold()


# ============================================================================
# Registry Infrastructure
# ============================================================================

_REGISTRY_LOCK: Final[RLock] = RLock()

# Populated from external database only.
_PROPELLANT_REGISTRY: dict[str, Propellant] = {}

_ALIAS_REGISTRY: dict[str, str] = {}

LOGGER.debug(
    "Propellant registry infrastructure initialized."
)
# ============================================================================
# Standard Library
# ============================================================================

from dataclasses import asdict
from dataclasses import dataclass

# ============================================================================
# Propellant Data Model
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class Propellant:
    """
    Immutable propellant definition.

    Represents a fully validated propellant record
    loaded from an approved COSMOS database.

    All units shall remain SI units.

    Parameters
    ----------
    name : str
        Canonical propellant name.

    short_name : str
        Short identifier.

    formula : str
        Chemical formula.

    molecular_weight : float
        Molecular weight [kg/kmol].

    phase : Phase
        Physical phase.

    propellant_type : PropellantType
        Functional classification.

    cea_species_name : str
        Species name used by NASA CEA.

    aliases : tuple[str, ...]
        Alternate lookup names.

    density : float
        Density [kg/m³].

    density_temperature : float
        Density reference temperature [K].

    density_pressure : float
        Density reference pressure [Pa].

    storage_temperature : float
        Recommended storage temperature [K].

    storage_pressure : float
        Recommended storage pressure [Pa].

    boiling_point : float
        Boiling point [K].

    freezing_point : float
        Freezing point [K].

    critical_temperature : float
        Critical temperature [K].

    critical_pressure : float
        Critical pressure [Pa].

    elements : dict[str, int]
        Elemental composition.

    source : str
        Data source.

    reference : str
        Reference document.

    reference_date : str
        Source publication date.

    data_quality_level : str
        Data quality classification.

    version : str
        Database record version.

    last_verified : str
        Last verification date.

    notes : str
        Additional metadata.
    """

    name: str
    short_name: str
    formula: str

    molecular_weight: float

    phase: Phase
    propellant_type: PropellantType

    cea_species_name: str

    aliases: tuple[str, ...]

    density: float
    density_temperature: float
    density_pressure: float

    storage_temperature: float
    storage_pressure: float

    boiling_point: float
    freezing_point: float

    critical_temperature: float
    critical_pressure: float

    elements: dict[str, int]

    source: str
    reference: str

    reference_date: str
    data_quality_level: str
    version: str
    last_verified: str

    notes: str = ""

    def __post_init__(
        self,
    ) -> None:
        """
        Validate propellant record.

        Raises
        ------
        PropellantValidationError
        """

        _validate_non_empty_string(
            self.name,
            "name",
        )

        _validate_non_empty_string(
            self.short_name,
            "short_name",
        )

        _validate_non_empty_string(
            self.formula,
            "formula",
        )

        _validate_non_empty_string(
            self.cea_species_name,
            "cea_species_name",
        )

        _validate_non_empty_string(
            self.source,
            "source",
        )

        _validate_non_empty_string(
            self.reference,
            "reference",
        )

        if not isinstance(
            self.phase,
            Phase,
        ):
            raise PropellantValidationError(
                "phase must be Phase enum."
            )

        if not isinstance(
            self.propellant_type,
            PropellantType,
        ):
            raise PropellantValidationError(
                "propellant_type must be "
                "PropellantType enum."
            )

        _validate_positive_float(
            self.molecular_weight,
            "molecular_weight",
        )

        _validate_positive_float(
            self.density,
            "density",
        )

        _validate_non_negative_float(
            self.density_temperature,
            "density_temperature",
        )

        _validate_non_negative_float(
            self.density_pressure,
            "density_pressure",
        )

        _validate_non_negative_float(
            self.storage_temperature,
            "storage_temperature",
        )

        _validate_non_negative_float(
            self.storage_pressure,
            "storage_pressure",
        )

        _validate_non_negative_float(
            self.boiling_point,
            "boiling_point",
        )

        _validate_non_negative_float(
            self.freezing_point,
            "freezing_point",
        )

        _validate_non_negative_float(
            self.critical_temperature,
            "critical_temperature",
        )

        _validate_non_negative_float(
            self.critical_pressure,
            "critical_pressure",
        )

        _validate_aliases(
            self.aliases,
        )

        _validate_elements(
            self.elements,
        )

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Convert propellant to dictionary.

        Returns
        -------
        dict[str, object]
        """

        data = asdict(
            self,
        )

        data["phase"] = (
            self.phase.value
        )

        data["propellant_type"] = (
            self.propellant_type.value
        )

        return data

    @classmethod
    def from_dict(
        cls,
        data: dict[str, object],
    ) -> "Propellant":
        """
        Construct propellant from dictionary.

        Parameters
        ----------
        data : dict[str, object]

        Returns
        -------
        Propellant
        """

        # Extract and validate molecular weight separately to ensure
        # proper error reporting and correct syntax.
        mw = data.get("molecular_weight")

        if not isinstance(mw, (int, float)):
            raise PropellantValidationError(
                "molecular_weight must be a number."
            )

        aliases = data.get("aliases")

        if not isinstance(aliases, (list, tuple)):
            raise PropellantValidationError(
                "aliases must be a list or tuple of strings."
            )

        # Validate density separately to satisfy static type checkers
        density = data.get("density")

        if not isinstance(density, (int, float)):
            raise PropellantValidationError(
                "density must be a number."
            )

        # Validate density_temperature separately to satisfy static type checkers
        density_temperature = data.get("density_temperature")

        if not isinstance(density_temperature, (int, float)):
            raise PropellantValidationError(
                "density_temperature must be a number."
            )

        density_pressure = data.get("density_pressure")

        if not isinstance(density_pressure, (int, float)):
            raise PropellantValidationError(
                "density_pressure must be a number."
            )

        storage_temperature = data.get("storage_temperature")

        if not isinstance(storage_temperature, (int, float)):
            raise PropellantValidationError(
                "storage_temperature must be a number."
            )

        storage_pressure = data.get("storage_pressure")

        if not isinstance(storage_pressure, (int, float)):
            raise PropellantValidationError(
                "storage_pressure must be a number."
            )

        boiling_point = data.get("boiling_point")

        if not isinstance(boiling_point, (int, float)):
            raise PropellantValidationError(
                "boiling_point must be a number."
            )

        freezing_point = data.get("freezing_point")

        if not isinstance(freezing_point, (int, float)):
            raise PropellantValidationError(
                "freezing_point must be a number."
            )

        critical_temperature = data.get("critical_temperature")

        if not isinstance(critical_temperature, (int, float)):
            raise PropellantValidationError(
                "critical_temperature must be a number."
            )

        critical_pressure = data.get("critical_pressure")

        if not isinstance(critical_pressure, (int, float)):
            raise PropellantValidationError(
                "critical_pressure must be a number."
            )

        elements_raw = data.get("elements")

        if not isinstance(elements_raw, dict):
            raise PropellantValidationError(
                "elements must be a dictionary."
            )

        elements: dict[str, int] = {}

        for key, value in elements_raw.items():
            if not isinstance(key, str):
                raise PropellantValidationError(
                    "Invalid element symbol."
                )

            if not isinstance(value, int):
                raise PropellantValidationError(
                    "Invalid element count."
                )

            elements[key] = value

        return cls(
            name=str(data["name"]),
            short_name=str(data["short_name"]),
            formula=str(data["formula"]),
            molecular_weight=float(mw),
            phase=Phase(str(data["phase"])),
            propellant_type=PropellantType(
                str(
                    data["propellant_type"]
                )
            ),
            cea_species_name=str(
                data["cea_species_name"]
            ),
            aliases=tuple(aliases),
            density=float(density),
            density_temperature=float(density_temperature),
            density_pressure=float(density_pressure),
            storage_temperature=float(storage_temperature),
            storage_pressure=float(storage_pressure),
            boiling_point=float(boiling_point),
            freezing_point=float(freezing_point),
            critical_temperature=float(critical_temperature),
            critical_pressure=float(critical_pressure),
            source=str(
                data["source"]
            ),
            reference=str(
                data["reference"]
            ),
            reference_date=str(
                data["reference_date"]
            ),
            data_quality_level=str(
                data[
                    "data_quality_level"
                ]
            ),
            version=str(
                data["version"]
            ),
            last_verified=str(
                data["last_verified"]
            ),
            notes=str(
                data.get(
                    "notes",
                    "",
                )
            ),
            elements=elements
        )

    def to_json(
        self,
        *,
        indent: int = 4,
    ) -> str:
        """
        Serialize propellant to JSON.

        Parameters
        ----------
        indent : int
            JSON indentation.

        Returns
        -------
        str
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

    @classmethod
    def from_json(
        cls,
        json_text: str,
    ) -> "Propellant":
        """
        Construct propellant from JSON.

        Parameters
        ----------
        json_text : str

        Returns
        -------
        Propellant
        """

        try:

            data = json.loads(
                json_text,
            )

        except json.JSONDecodeError as exc:

            raise PropellantValidationError(
                "Invalid JSON record."
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise PropellantValidationError(
                "JSON root must be object."
            )

        return cls.from_dict(
            data,
        )


LOGGER.debug(
    "Propellant dataclass loaded."
)
# ============================================================================
# Registry Framework
# ============================================================================


def register_propellant(
    propellant: Propellant,
) -> None:
    """
    Register a propellant.

    Parameters
    ----------
    propellant : Propellant
        Propellant instance.

    Raises
    ------
    DuplicatePropellantError
        If the propellant already exists.

    PropellantValidationError
        If the supplied object is invalid.
    """

    if not isinstance(
        propellant,
        Propellant,
    ):
        raise PropellantValidationError(
            "register_propellant() requires "
            "a Propellant instance."
        )

    key = _normalize_key(
        propellant.name,
    )

    with _REGISTRY_LOCK:

        if key in _PROPELLANT_REGISTRY:
            raise DuplicatePropellantError(
                f"Propellant already exists: "
                f"{propellant.name}"
            )

        for alias in propellant.aliases:

            alias_key = _normalize_key(
                alias,
            )

            if alias_key in _ALIAS_REGISTRY:
                raise DuplicatePropellantError(
                    "Alias collision detected: "
                    f"{alias}"
                )

            if alias_key in _PROPELLANT_REGISTRY:
                raise DuplicatePropellantError(
                    "Alias conflicts with "
                    "existing propellant name: "
                    f"{alias}"
                )

        _PROPELLANT_REGISTRY[
            key
        ] = propellant

        for alias in propellant.aliases:

            alias_key = _normalize_key(
                alias,
            )

            _ALIAS_REGISTRY[
                alias_key
            ] = key

    LOGGER.debug(
        "Registered propellant '%s'.",
        propellant.name,
    )


def get_propellant(
    name: str,
) -> Propellant:
    """
    Retrieve propellant by name.

    Parameters
    ----------
    name : str
        Canonical propellant name.

    Returns
    -------
    Propellant

    Raises
    ------
    PropellantNotFoundError
    """

    key = _normalize_key(
        name,
    )

    try:

        propellant = (
            _PROPELLANT_REGISTRY[
                key
            ]
        )

    except KeyError as exc:

        raise PropellantNotFoundError(
            f"Propellant not found: "
            f"{name}"
        ) from exc

    return propellant


def get_propellant_by_alias(
    alias: str,
) -> Propellant:
    """
    Retrieve propellant by alias.

    Parameters
    ----------
    alias : str

    Returns
    -------
    Propellant

    Raises
    ------
    PropellantNotFoundError
    """

    alias_key = _normalize_key(
        alias,
    )

    try:

        canonical_key = (
            _ALIAS_REGISTRY[
                alias_key
            ]
        )

    except KeyError as exc:

        raise PropellantNotFoundError(
            f"Alias not found: "
            f"{alias}"
        ) from exc

    return get_propellant(
        canonical_key,
    )


def exists(
    name: str,
) -> bool:
    """
    Check whether a propellant exists.

    Parameters
    ----------
    name : str

    Returns
    -------
    bool
    """

    key = _normalize_key(
        name,
    )

    return (
        key in _PROPELLANT_REGISTRY
    )


def list_propellants(
) -> tuple[Propellant, ...]:
    """
    List all registered propellants.

    Returns
    -------
    tuple[Propellant, ...]
    """

    return tuple(
        sorted(
            _PROPELLANT_REGISTRY.values(),
            key=lambda p: p.name,
        )
    )


def list_fuels(
) -> tuple[Propellant, ...]:
    """
    List all fuels.

    Returns
    -------
    tuple[Propellant, ...]
    """

    return tuple(
        propellant
        for propellant
        in list_propellants()
        if (
            propellant.propellant_type
            is PropellantType.FUEL
        )
    )


def list_oxidizers(
) -> tuple[Propellant, ...]:
    """
    List all oxidizers.

    Returns
    -------
    tuple[Propellant, ...]
    """

    return tuple(
        propellant
        for propellant
        in list_propellants()
        if (
            propellant.propellant_type
            is PropellantType.OXIDIZER
        )
    )


def list_pressurants(
) -> tuple[Propellant, ...]:
    """
    List all pressurants.

    Returns
    -------
    tuple[Propellant, ...]
    """

    return tuple(
        propellant
        for propellant
        in list_propellants()
        if (
            propellant.propellant_type
            is PropellantType.PRESSURANT
        )
    )


def list_inerts(
) -> tuple[Propellant, ...]:
    """
    List all inert propellants.

    Returns
    -------
    tuple[Propellant, ...]
    """

    return tuple(
        propellant
        for propellant
        in list_propellants()
        if (
            propellant.propellant_type
            is PropellantType.INERT
        )
    )


def registry_size(
) -> int:
    """
    Return registry size.

    Returns
    -------
    int
    """

    return len(
        _PROPELLANT_REGISTRY
    )


def clear_registry(
) -> None:
    """
    Clear registry.

    Intended primarily for
    testing and database reloads.

    Returns
    -------
    None
    """

    with _REGISTRY_LOCK:

        _PROPELLANT_REGISTRY.clear()

        _ALIAS_REGISTRY.clear()

    LOGGER.debug(
        "Propellant registry cleared."
    )


LOGGER.debug(
    "Propellant registry framework loaded."
)
# ============================================================================
# Database Loading Framework
# ============================================================================

DATABASE_SCHEMA_VERSION: Final[str] = "1.0"

REQUIRED_DATABASE_FIELDS: Final[frozenset[str]] = (
    frozenset(
        {
            "name",
            "short_name",
            "formula",
            "molecular_weight",
            "phase",
            "propellant_type",
            "cea_species_name",
            "aliases",
            "density",
            "density_temperature",
            "density_pressure",
            "storage_temperature",
            "storage_pressure",
            "boiling_point",
            "freezing_point",
            "critical_temperature",
            "critical_pressure",
            "elements",
            "source",
            "reference",
            "reference_date",
            "data_quality_level",
            "version",
            "last_verified",
            "notes",
        }
    )
)


def _validate_database_record(
    record: dict[str, object],
) -> None:
    """
    Validate raw database record.

    Parameters
    ----------
    record : dict[str, object]

    Raises
    ------
    PropellantValidationError
    """

    missing_fields = (
        REQUIRED_DATABASE_FIELDS
        - set(record.keys())
    )

    if missing_fields:

        raise PropellantValidationError(
            "Missing required fields: "
            f"{sorted(missing_fields)}"
        )

    try:

        Propellant.from_dict(
            record,
        )

    except Exception as exc:

        raise PropellantValidationError(
            "Invalid propellant "
            f"record: "
            f"{record.get('name', '<unknown>')}"
        ) from exc


def _load_json_file(
    database_path: Path,
) -> list[dict[str, object]]:
    """
    Load JSON database file.

    Parameters
    ----------
    database_path : Path

    Returns
    -------
    list[dict[str, object]]

    Raises
    ------
    PropellantValidationError
    """

    if not database_path.exists():

        raise PropellantValidationError(
            "Database file does not exist: "
            f"{database_path}"
        )

    try:

        with database_path.open(
            mode="r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file,
            )

    except json.JSONDecodeError as exc:

        raise PropellantValidationError(
            "Invalid JSON database."
        ) from exc

    except OSError as exc:

        raise PropellantValidationError(
            "Unable to read database: "
            f"{database_path}"
        ) from exc

    if not isinstance(
        data,
        list,
    ):
        raise PropellantValidationError(
            "Database root must be "
            "a list of propellant records."
        )

    return data


def load_json_database(
    database_path: Path,
) -> int:
    """
    Load propellants from JSON database.

    Parameters
    ----------
    database_path : Path

    Returns
    -------
    int
        Number of loaded propellants.

    Raises
    ------
    PropellantValidationError
    DuplicatePropellantError
    """

    LOGGER.info(
        "Loading propellant database: %s",
        database_path,
    )

    records = _load_json_file(
        database_path,
    )

    loaded_count = 0

    for record in records:

        if not isinstance(
            record,
            dict,
        ):
            raise PropellantValidationError(
                "Each record must be "
                "a dictionary."
            )

        _validate_database_record(
            record,
        )

        propellant = (
            Propellant.from_dict(
                record,
            )
        )

        register_propellant(
            propellant,
        )

        loaded_count += 1

    LOGGER.info(
        "Loaded %d propellant records.",
        loaded_count,
    )

    return loaded_count


def load_database(
    database_path: Path | None = None,
) -> int:
    """
    Load propellant database.

    Parameters
    ----------
    database_path : Path | None

    Returns
    -------
    int
        Number of loaded records.
    """

    if database_path is None:

        database_path = (
            Path.cwd()
            / DEFAULT_DATABASE_DIRECTORY
            / DEFAULT_DATABASE_FILENAME
        )

    return load_json_database(
        database_path,
    )


def reload_database(
    database_path: Path | None = None,
) -> int:
    """
    Reload propellant database.

    Parameters
    ----------
    database_path : Path | None

    Returns
    -------
    int
        Number of loaded records.
    """

    LOGGER.info(
        "Reloading propellant database."
    )

    clear_registry()

    return load_database(
        database_path,
    )


# ============================================================================
# Future Database Backends
# ============================================================================


def load_yaml_database(
    database_path: Path,
) -> int:
    """
    Future YAML backend.

    Parameters
    ----------
    database_path : Path

    Raises
    ------
    NotImplementedError
    """

    raise NotImplementedError(
        "YAML backend not yet implemented."
    )


def load_sqlite_database(
    database_path: Path,
) -> int:
    """
    Future SQLite backend.

    Parameters
    ----------
    database_path : Path

    Raises
    ------
    NotImplementedError
    """

    raise NotImplementedError(
        "SQLite backend not yet implemented."
    )


# ============================================================================
# Registry Initialization
# ============================================================================


def initialize_registry(
) -> None:
    """
    Initialize registry.

    Phase 0.2 Step 1 intentionally
    does not auto-load propellant
    records.

    The registry remains empty until
    a database is explicitly loaded.

    Returns
    -------
    None
    """

    LOGGER.info(
        "Propellant registry initialized."
    )

    LOGGER.info(
        "No propellant database loaded."
    )


initialize_registry()

LOGGER.debug(
    "Database loading framework loaded."
)
# ============================================================================
# Registry Statistics
# ============================================================================


def registry_statistics(
) -> dict[str, int]:
    """
    Return registry statistics.

    Returns
    -------
    dict[str, int]
        Registry summary.
    """

    return {
        "total": registry_size(),
        "fuels": len(
            list_fuels(),
        ),
        "oxidizers": len(
            list_oxidizers(),
        ),
        "pressurants": len(
            list_pressurants(),
        ),
        "inerts": len(
            list_inerts(),
        ),
        "aliases": len(
            _ALIAS_REGISTRY,
        ),
    }


# ============================================================================
# Database Utilities
# ============================================================================


def default_database_path(
) -> Path:
    """
    Return default propellant database path.

    Returns
    -------
    Path
        Default database location.
    """

    return (
        Path.cwd()
        / DEFAULT_DATABASE_DIRECTORY
        / DEFAULT_DATABASE_FILENAME
    )


def database_exists(
    database_path: Path | None = None,
) -> bool:
    """
    Check whether database exists.

    Parameters
    ----------
    database_path : Path | None

    Returns
    -------
    bool
    """

    if database_path is None:

        database_path = (
            default_database_path()
        )

    return database_path.exists()


# ============================================================================
# Registry Query Utilities
# ============================================================================


def get_all_names(
) -> tuple[str, ...]:
    """
    Return all canonical names.

    Returns
    -------
    tuple[str, ...]
    """

    return tuple(
        propellant.name
        for propellant
        in list_propellants()
    )


def get_all_aliases(
) -> tuple[str, ...]:
    """
    Return all aliases.

    Returns
    -------
    tuple[str, ...]
    """

    return tuple(
        sorted(
            _ALIAS_REGISTRY.keys(),
        )
    )


def is_registry_empty(
) -> bool:
    """
    Check whether registry is empty.

    Returns
    -------
    bool
    """

    return registry_size() == 0


# ============================================================================
# Export Public API
# ============================================================================

__all__ = (
    # Data Model
    "Propellant",

    # Registry
    "register_propellant",
    "get_propellant",
    "get_propellant_by_alias",
    "exists",
    "list_propellants",
    "list_fuels",
    "list_oxidizers",
    "list_pressurants",
    "list_inerts",
    "registry_size",
    "clear_registry",

    # Database
    "load_database",
    "reload_database",
    "load_json_database",
    "load_yaml_database",
    "load_sqlite_database",

    # Utilities
    "registry_statistics",
    "default_database_path",
    "database_exists",
    "get_all_names",
    "get_all_aliases",
    "is_registry_empty",
)

# ============================================================================
# Module Validation
# ============================================================================

LOGGER.info(
    "COSMOS propellant registry module loaded."
)

LOGGER.info(
    "Database-driven architecture enabled."
)

LOGGER.info(
    "Registry size: %d",
    registry_size(),
)

LOGGER.info(
    "Default database path: %s",
    default_database_path(),
)

if is_registry_empty():

    LOGGER.info(
        "Registry currently empty."
    )

    LOGGER.info(
        "Awaiting external database load."
    )

LOGGER.debug(
    "Phase 0.2 Step 1 implementation complete."
)