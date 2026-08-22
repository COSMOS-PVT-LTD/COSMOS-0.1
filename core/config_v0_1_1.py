"""
COSMOS Rocket Propulsion Platform

Module: core.config
Author: COSMOS Development Team
Version: 0.1.1

Purpose
-------
Centralized configuration management for COSMOS.

Description
-----------
Provides immutable application configuration,
configuration validation, environment overrides,
resource management, serialization, audit support,
and startup initialization services.

This module is the single authoritative source
for application configuration.

Notes
-----
Configuration creation and validation occur here.

Runtime access and lifecycle management belong in:

    core.settings

References
----------
COSMOS_MASTER_SPEC.md
COSMOS_ARCHITECTURE_SPEC.md
COSMOS_CODING_STANDARD.md
COSMOS_DATABASE_SPEC.md
COSMOS_GUI_SPEC.md
COSMOS_FILE_SPEC.md
"""

from __future__ import annotations

# ============================================================================
# Standard Library
# ============================================================================

import hashlib
import json
import logging
import os

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from typing import cast

from enum import Enum

from pathlib import Path

from threading import RLock

from typing import Final
from typing import Mapping

# ============================================================================
# COSMOS Core
# ============================================================================

from core.exceptions import CosmosError
from core.exceptions import InvalidInputError

# ============================================================================
# Public Exports
# ============================================================================

__all__ = (
    "Environment",
    "UnitSystem",
    "Theme",
    "LogLevel",
    "FlowModel",
    "HeatTransferModel",
    "ApplicationMetadataConfig",
    "RuntimeConfig",
    "DirectoryConfig",
    "LoggingConfig",
    "ValidationConfig",
    "SolverConfig",
    "PrecisionConfig",
    "UnitSystemConfig",
    "CEAConfig",
    "CFDConfig",
    "PhysicsConfig",
    "OptimizationConfig",
    "MachineLearningConfig",
    "GUIConfig",
    "DatabaseConfig",
    "MaterialsDatabaseConfig",
    "CacheConfig",
    "ProjectConfig",
    "SimulationConfig",
    "ExportConfig",
    "ResourceConfig",
    "SecurityConfig",
    "BackupConfig",
    "AuditConfig",
    "PluginConfig",
    "APIConfig",
    "TestingConfig",
    "CosmosConfig",
)

# ============================================================================
# Module Constants
# ============================================================================

DEFAULT_CONFIG_VERSION: Final[str] = "0.1.1"

DEFAULT_APP_NAME: Final[str] = "COSMOS"

DEFAULT_COMPANY_NAME: Final[str] = "COSMOS Aerospace"

SUPPORTED_THEMES: Final[tuple[str, ...]] = (
    "dark",
    "light",
)

_SUPPORTED_LOG_LEVELS: Final[tuple[str, ...]] = (
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
)

# ============================================================================
# Configuration Exceptions
# ============================================================================


class ConfigurationError(CosmosError):
    """
    Base configuration exception.
    """


class ConfigurationValidationError(
    ConfigurationError,
):
    """
    Raised when configuration validation fails.
    """


class ConfigurationInitializationError(
    ConfigurationError,
):
    """
    Raised when configuration initialization fails.
    """


class EnvironmentOverrideError(
    ConfigurationError,
):
    """
    Raised when an environment variable
    cannot be parsed correctly.
    """


# ============================================================================
# Enumerations
# ============================================================================


class Environment(str, Enum):
    """
    Supported runtime environments.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class UnitSystem(str, Enum):
    """
    Supported unit systems.
    """

    SI = "SI"


class Theme(str, Enum):
    """
    GUI themes.
    """

    DARK = "dark"
    LIGHT = "light"


class LogLevel(str, Enum):
    """
    Logging levels.
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FlowModel(str, Enum):
    """
    Default flow models.
    """

    IDEAL_GAS = "ideal_gas"


class HeatTransferModel(str, Enum):
    """
    Default heat transfer models.
    """

    BARTZ = "bartz"


# ============================================================================
# Configuration Groups
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class ApplicationMetadataConfig:
    """
    Application metadata.
    """

    app_name: str
    app_version: str
    config_version: str
    company_name: str
    build_date: str


@dataclass(
    slots=True,
    frozen=True,
)
class RuntimeConfig:
    """
    Runtime settings.
    """

    debug: bool
    verbose: bool
    safe_mode: bool
    test_mode: bool


@dataclass(
    slots=True,
    frozen=True,
)
class DirectoryConfig:
    """
    Directory configuration.
    """

    project_root: Path

    logs_dir: Path
    cache_dir: Path
    reports_dir: Path

    databases_dir: Path

    simulations_dir: Path

    exports_dir: Path

    audit_dir: Path

    backup_dir: Path


@dataclass(
    slots=True,
    frozen=True,
)
class LoggingConfig:
    """
    Logging configuration.
    """

    log_level: LogLevel

    max_log_file_size_mb: int

    backup_log_count: int


@dataclass(
    slots=True,
    frozen=True,
)
class ValidationConfig:
    """
    Validation configuration.
    """

    strict_validation: bool

    startup_validation: bool


@dataclass(
    slots=True,
    frozen=True,
)
class SolverConfig:
    """
    Numerical solver settings.
    """

    max_iterations: int

    relative_tolerance: float

    absolute_tolerance: float

    solver_timeout: float


@dataclass(
    slots=True,
    frozen=True,
)
class PrecisionConfig:
    """
    Numerical precision settings.
    """

    floating_point_precision: int

    rounding_digits: int


@dataclass(
    slots=True,
    frozen=True,
)
class UnitSystemConfig:
    """
    Unit system configuration.
    """

    default_unit_system: UnitSystem


@dataclass(
    slots=True,
    frozen=True,
)
class CEAConfig:
    """
    NASA CEA configuration.
    """

    cea_cache_dir: Path

    cea_timeout: float

    cea_max_retries: int


@dataclass(
    slots=True,
    frozen=True,
)
class CFDConfig:
    """
    CFD configuration.
    """

    cfd_enabled: bool

    cfd_case_dir: Path

    cfd_default_solver: str

    cfd_max_iterations: int

    cfd_residual_target: float


@dataclass(
    slots=True,
    frozen=True,
)
class PhysicsConfig:
    """
    Physics engine defaults.
    """

    default_flow_model: FlowModel

    default_heat_transfer_model: (
        HeatTransferModel
    )


@dataclass(
    slots=True,
    frozen=True,
)
class OptimizationConfig:
    """
    Optimization configuration.
    """

    optimizer_timeout: float

    genetic_population: int

    max_generations: int


@dataclass(
    slots=True,
    frozen=True,
)
class MachineLearningConfig:
    """
    Machine-learning configuration.
    """

    ml_enabled: bool

    model_dir: Path

    gpu_enabled: bool


@dataclass(
    slots=True,
    frozen=True,
)
class GUIConfig:
    """
    GUI configuration.
    """

    theme: Theme

    window_width: int

    window_height: int

    font_size: int


# ============================================================================
# Additional Configuration Groups
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class DatabaseConfig:
    """
    Primary database configuration.
    """

    database_path: Path

    database_timeout: float


@dataclass(
    slots=True,
    frozen=True,
)
class MaterialsDatabaseConfig:
    """
    Materials database configuration.
    """

    materials_database_path: Path

    materials_database_version: str


@dataclass(
    slots=True,
    frozen=True,
)
class CacheConfig:
    """
    Cache configuration.
    """

    cache_enabled: bool

    cache_max_size_gb: float

    cache_expiration_days: int


@dataclass(
    slots=True,
    frozen=True,
)
class ProjectConfig:
    """
    Project configuration.
    """

    project_extension: str

    auto_project_backup: bool


@dataclass(
    slots=True,
    frozen=True,
)
class SimulationConfig:
    """
    Simulation configuration.
    """

    simulation_timeout: float

    save_intermediate_results: bool


@dataclass(
    slots=True,
    frozen=True,
)
class ExportConfig:
    """
    Export configuration.
    """

    pdf_export_enabled: bool

    csv_export_enabled: bool

    json_export_enabled: bool

    excel_export_enabled: bool


@dataclass(
    slots=True,
    frozen=True,
)
class ResourceConfig:
    """
    System resource limits.
    """

    max_cpu_cores: int

    max_memory_gb: float

    multiprocessing_enabled: bool


@dataclass(
    slots=True,
    frozen=True,
)
class SecurityConfig:
    """
    Security configuration.
    """

    enable_checksums: bool

    enable_crash_dumps: bool

    enable_recovery: bool


@dataclass(
    slots=True,
    frozen=True,
)
class BackupConfig:
    """
    Backup configuration.
    """

    backup_enabled: bool

    backup_interval_hours: int

    max_backups: int


@dataclass(
    slots=True,
    frozen=True,
)
class AuditConfig:
    """
    Audit configuration.
    """

    audit_enabled: bool

    audit_retention_days: int


@dataclass(
    slots=True,
    frozen=True,
)
class PluginConfig:
    """
    Plugin configuration.
    """

    plugins_enabled: bool

    plugins_dir: Path


@dataclass(
    slots=True,
    frozen=True,
)
class APIConfig:
    """
    API configuration.
    """

    api_enabled: bool

    api_port: int

    api_timeout: float


@dataclass(
    slots=True,
    frozen=True,
)
class TestingConfig:
    """
    Testing configuration.
    """

    mock_mode: bool

    test_data_dir: Path


# ============================================================================
# Root Configuration Object
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class CosmosConfig:
    """
    Master COSMOS configuration.

    This object contains every validated
    configuration group used by COSMOS.
    """

    metadata: ApplicationMetadataConfig

    runtime: RuntimeConfig

    environment: Environment

    directories: DirectoryConfig

    logging: LoggingConfig

    validation: ValidationConfig

    solver: SolverConfig

    precision: PrecisionConfig

    units: UnitSystemConfig

    cea: CEAConfig

    cfd: CFDConfig

    physics: PhysicsConfig

    optimization: OptimizationConfig

    machine_learning: MachineLearningConfig

    gui: GUIConfig

    database: DatabaseConfig

    materials_database: (
        MaterialsDatabaseConfig
    )

    cache: CacheConfig

    project: ProjectConfig

    simulation: SimulationConfig

    export: ExportConfig

    resources: ResourceConfig

    security: SecurityConfig

    backup: BackupConfig

    audit: AuditConfig

    plugins: PluginConfig

    api: APIConfig

    testing: TestingConfig

    config_hash: str = field(
        default="",
        compare=False,
    )

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Convert configuration to dictionary.

        Returns
        -------
        dict[str, object]
            Serialized configuration.
        """

        data = asdict(self)

        return cast(
    dict[str, object],
    _convert_paths(data),
)

    def to_json(
        self,
        indent: int = 4,
    ) -> str:
        """
        Export configuration to JSON.

        Parameters
        ----------
        indent : int
            JSON indentation level.

        Returns
        -------
        str
            JSON representation.
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )


# ============================================================================
# Internal Utility Functions
# ============================================================================


def _convert_paths(
    value: object,
) -> object:
    """
    Recursively convert Path objects
    into strings.

    Parameters
    ----------
    value : object
        Object to process.

    Returns
    -------
    object
        Serialized object.
    """

    if isinstance(
        value,
        Path,
    ):
        return str(value)

    if isinstance(
        value,
        dict,
    ):
        return {
            key: _convert_paths(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            _convert_paths(item)
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return tuple(
            _convert_paths(item)
            for item in value
        )

    return value


def _calculate_config_hash(
    data: Mapping[str, object],
) -> str:
    """
    Calculate deterministic SHA256
    configuration hash.

    Parameters
    ----------
    data : Mapping[str, object]
        Configuration dictionary.

    Returns
    -------
    str
        SHA256 hash.
    """

    payload = json.dumps(
        _convert_paths(
            dict(data)
        ),
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================================
# Module Synchronization
# ============================================================================

_CONFIG_LOCK: Final[RLock] = RLock()

LOGGER: Final[
    logging.Logger
] = logging.getLogger(
    __name__
)

# ============================================================================
# Environment Variable Parsing
# ============================================================================


def _get_env_bool(
    name: str,
    default: bool,
) -> bool:
    """
    Read boolean environment variable.

    Parameters
    ----------
    name : str
        Environment variable name.

    default : bool
        Default value.

    Returns
    -------
    bool
        Parsed boolean value.
    """

    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return True

    if normalized in {
        "0",
        "false",
        "no",
        "off",
    }:
        return False

    raise EnvironmentOverrideError(
        f"Invalid boolean value for "
        f"{name}: {value}"
    )


def _get_env_int(
    name: str,
    default: int,
) -> int:
    """
    Read integer environment variable.
    """

    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value)

    except ValueError as exc:
        raise EnvironmentOverrideError(
            f"Invalid integer value for "
            f"{name}: {value}"
        ) from exc


def _get_env_float(
    name: str,
    default: float,
) -> float:
    """
    Read floating point environment variable.
    """

    value = os.getenv(name)

    if value is None:
        return default

    try:
        return float(value)

    except ValueError as exc:
        raise EnvironmentOverrideError(
            f"Invalid float value for "
            f"{name}: {value}"
        ) from exc


def _get_env_str(
    name: str,
    default: str,
) -> str:
    """
    Read string environment variable.
    """

    return os.getenv(
        name,
        default,
    )


def _get_env_path(
    name: str,
    default: Path,
) -> Path:
    """
    Read path environment variable.
    """

    value = os.getenv(name)

    if value is None:
        return default

    return Path(value)


# ============================================================================
# Environment Enum Helpers
# ============================================================================


def _get_environment() -> Environment:
    """
    Read runtime environment.

    Returns
    -------
    Environment
        Active environment.
    """

    value = os.getenv(
        "COSMOS_ENVIRONMENT",
        Environment.DEVELOPMENT.value,
    )

    try:
        return Environment(value)

    except ValueError as exc:
        raise ConfigurationValidationError(
            f"Unsupported environment: "
            f"{value}"
        ) from exc


def _get_log_level() -> LogLevel:
    """
    Read configured log level.
    """

    value = os.getenv(
        "COSMOS_LOG_LEVEL",
        LogLevel.INFO.value,
    ).upper()

    try:
        return LogLevel(value)

    except ValueError as exc:
        raise ConfigurationValidationError(
            f"Invalid log level: {value}"
        ) from exc


# ============================================================================
# Validation Helpers
# ============================================================================


def _require_positive_int(
    value: int,
    name: str,
) -> None:
    """
    Require positive integer.
    """

    if value <= 0:
        raise ConfigurationValidationError(
            f"{name} must be > 0."
        )


def _require_positive_float(
    value: float,
    name: str,
) -> None:
    """
    Require positive float.
    """

    if value <= 0.0:
        raise ConfigurationValidationError(
            f"{name} must be > 0."
        )


def _require_non_negative_float(
    value: float,
    name: str,
) -> None:
    """
    Require non-negative float.
    """

    if value < 0.0:
        raise ConfigurationValidationError(
            f"{name} must be >= 0."
        )


def _require_port(
    port: int,
) -> None:
    """
    Validate TCP/IP port.
    """

    if not (
        1 <= port <= 65535
    ):
        raise ConfigurationValidationError(
            f"Invalid port number: "
            f"{port}"
        )


def _require_existing_directory(
    path: Path,
    name: str,
) -> None:
    """
    Validate directory path.
    """

    if (
        path.exists()
        and not path.is_dir()
    ):
        raise ConfigurationValidationError(
            f"{name} is not a directory: "
            f"{path}"
        )


def _require_supported_theme(
    theme: Theme,
) -> None:
    """
    Validate GUI theme.
    """

    if theme.value not in SUPPORTED_THEMES:
        raise ConfigurationValidationError(
            f"Unsupported theme: "
            f"{theme}"
        )


def _require_supported_unit_system(
    unit_system: UnitSystem,
) -> None:
    """
    Validate unit system.
    """

    if unit_system is not UnitSystem.SI:
        raise ConfigurationValidationError(
            "Only SI units are supported."
        )


# ============================================================================
# Directory Utilities
# ============================================================================


def _create_directory(
    path: Path,
) -> None:
    """
    Create directory safely.

    Parameters
    ----------
    path : Path
        Directory path.
    """

    try:
        path.mkdir(
            parents=True,
            exist_ok=True,
        )

    except OSError as exc:
        raise ConfigurationInitializationError(
            f"Failed creating directory: "
            f"{path}"
        ) from exc


def _create_required_directories(
    directories: DirectoryConfig,
) -> None:
    """
    Create all required directories.
    """

    _create_directory(
        directories.logs_dir
    )

    _create_directory(
        directories.cache_dir
    )

    _create_directory(
        directories.reports_dir
    )

    _create_directory(
        directories.databases_dir
    )

    _create_directory(
        directories.simulations_dir
    )

    _create_directory(
        directories.exports_dir
    )

    _create_directory(
        directories.audit_dir
    )

    _create_directory(
        directories.backup_dir
    )


# ============================================================================
# Project Root Helper
# ============================================================================


def get_project_root() -> Path:
    """
    Return COSMOS project root.

    Returns
    -------
    Path
        Project root directory.
    """

    return Path.cwd()


# ============================================================================
# Default Resource Helpers
# ============================================================================


def _default_cpu_count() -> int:
    """
    Determine default CPU count.
    """

    cpu_count = os.cpu_count()

    if cpu_count is None:
        return 1

    return max(
        1,
        cpu_count,
    )


def _default_memory_limit_gb() -> float:
    """
    Default memory limit.

    Returns
    -------
    float
        Memory limit [GB].
    """

    return 8.0


# ============================================================================
# Configuration Validation Entry Point
# ============================================================================


def validate_config(
    config: CosmosConfig,
) -> None:
    """
    Validate complete configuration.

    Parameters
    ----------
    config : CosmosConfig
        Configuration object.
    """

    _require_positive_int(
        config.solver.max_iterations,
        "max_iterations",
    )

    _require_positive_float(
        config.solver.relative_tolerance,
        "relative_tolerance",
    )

    _require_positive_float(
        config.solver.absolute_tolerance,
        "absolute_tolerance",
    )

    _require_positive_float(
        config.solver.solver_timeout,
        "solver_timeout",
    )

    _require_positive_int(
        config.resources.max_cpu_cores,
        "max_cpu_cores",
    )

    _require_positive_float(
        config.resources.max_memory_gb,
        "max_memory_gb",
    )

    _require_port(
        config.api.api_port,
    )

    _require_supported_theme(
        config.gui.theme,
    )

    _require_supported_unit_system(
        config.units.default_unit_system,
    )

    _require_existing_directory(
        config.directories.project_root,
        "project_root",
    )

# ============================================================================
# Configuration Construction
# ============================================================================


def create_required_directories(
    config: CosmosConfig,
) -> None:
    """
    Create all required runtime directories.

    Parameters
    ----------
    config : CosmosConfig
        Configuration instance.
    """

    _create_required_directories(
        config.directories
    )


def _build_default_configuration(
) -> CosmosConfig:
    """
    Build default COSMOS configuration.

    Returns
    -------
    CosmosConfig
        Default configuration object.
    """

    project_root = get_project_root()

    logs_dir = project_root / "logs"

    cache_dir = project_root / "cache"

    reports_dir = (
        project_root / "reports"
    )

    databases_dir = (
        project_root / "databases"
    )

    simulations_dir = (
        project_root / "simulations"
    )

    exports_dir = (
        project_root / "exports"
    )

    audit_dir = (
        project_root / "audit"
    )

    backup_dir = (
        project_root / "backup"
    )

    cea_cache_dir = (
        cache_dir / "cea"
    )

    cfd_case_dir = (
        simulations_dir / "cfd"
    )

    model_dir = (
        project_root / "models"
    )

    plugins_dir = (
        project_root / "plugins"
    )

    test_data_dir = (
        project_root
        / "tests"
        / "data"
    )

    config = CosmosConfig(
        metadata=(
            ApplicationMetadataConfig(
                app_name=DEFAULT_APP_NAME,
                app_version="0.1.1",
                config_version=(
                    DEFAULT_CONFIG_VERSION
                ),
                company_name=(
                    DEFAULT_COMPANY_NAME
                ),
                build_date=(
                    "2026-06-23"
                ),
            )
        ),
        runtime=RuntimeConfig(
            debug=False,
            verbose=False,
            safe_mode=True,
            test_mode=False,
        ),
        environment=(
            Environment.DEVELOPMENT
        ),
        directories=DirectoryConfig(
            project_root=project_root,
            logs_dir=logs_dir,
            cache_dir=cache_dir,
            reports_dir=reports_dir,
            databases_dir=(
                databases_dir
            ),
            simulations_dir=(
                simulations_dir
            ),
            exports_dir=exports_dir,
            audit_dir=audit_dir,
            backup_dir=backup_dir,
        ),
        logging=LoggingConfig(
            log_level=LogLevel.INFO,
            max_log_file_size_mb=100,
            backup_log_count=10,
        ),
        validation=ValidationConfig(
            strict_validation=True,
            startup_validation=True,
        ),
        solver=SolverConfig(
            max_iterations=1000,
            relative_tolerance=1e-6,
            absolute_tolerance=1e-9,
            solver_timeout=300.0,
        ),
        precision=PrecisionConfig(
            floating_point_precision=64,
            rounding_digits=10,
        ),
        units=UnitSystemConfig(
            default_unit_system=(
                UnitSystem.SI
            )
        ),
        cea=CEAConfig(
            cea_cache_dir=(
                cea_cache_dir
            ),
            cea_timeout=60.0,
            cea_max_retries=3,
        ),
        cfd=CFDConfig(
            cfd_enabled=True,
            cfd_case_dir=(
                cfd_case_dir
            ),
            cfd_default_solver=(
                "OpenFOAM"
            ),
            cfd_max_iterations=5000,
            cfd_residual_target=(
                1.0e-6
            ),
        ),
        physics=PhysicsConfig(
            default_flow_model=(
                FlowModel.IDEAL_GAS
            ),
            default_heat_transfer_model=(
                HeatTransferModel.BARTZ
            ),
        ),
        optimization=(
            OptimizationConfig(
                optimizer_timeout=3600.0,
                genetic_population=100,
                max_generations=100,
            )
        ),
        machine_learning=(
            MachineLearningConfig(
                ml_enabled=False,
                model_dir=model_dir,
                gpu_enabled=False,
            )
        ),
        gui=GUIConfig(
            theme=Theme.DARK,
            window_width=1400,
            window_height=900,
            font_size=10,
        ),
        database=DatabaseConfig(
            database_path=(
                databases_dir
                / "cosmos.db"
            ),
            database_timeout=30.0,
        ),
        materials_database=(
            MaterialsDatabaseConfig(
                materials_database_path=(
                    databases_dir
                    / "materials.db"
                ),
                materials_database_version=(
                    "1.0"
                ),
            )
        ),
        cache=CacheConfig(
            cache_enabled=True,
            cache_max_size_gb=10.0,
            cache_expiration_days=30,
        ),
        project=ProjectConfig(
            project_extension=(
                ".cosmos"
            ),
            auto_project_backup=True,
        ),
        simulation=(
            SimulationConfig(
                simulation_timeout=7200.0,
                save_intermediate_results=True,
            )
        ),
        export=ExportConfig(
            pdf_export_enabled=True,
            csv_export_enabled=True,
            json_export_enabled=True,
            excel_export_enabled=True,
        ),
        resources=ResourceConfig(
            max_cpu_cores=(
                _default_cpu_count()
            ),
            max_memory_gb=(
                _default_memory_limit_gb()
            ),
            multiprocessing_enabled=True,
        ),
        security=SecurityConfig(
            enable_checksums=True,
            enable_crash_dumps=True,
            enable_recovery=True,
        ),
        backup=BackupConfig(
            backup_enabled=True,
            backup_interval_hours=24,
            max_backups=20,
        ),
        audit=AuditConfig(
            audit_enabled=True,
            audit_retention_days=365,
        ),
        plugins=PluginConfig(
            plugins_enabled=True,
            plugins_dir=plugins_dir,
        ),
        api=APIConfig(
            api_enabled=False,
            api_port=8080,
            api_timeout=30.0,
        ),
        testing=TestingConfig(
            mock_mode=False,
            test_data_dir=(
                test_data_dir
            ),
        ),
    )

    return config


# ============================================================================
# Environment Overrides
# ============================================================================


def _apply_environment_overrides(
    config: CosmosConfig,
) -> CosmosConfig:
    """
    Apply COSMOS_* environment
    variable overrides.

    Parameters
    ----------
    config : CosmosConfig
        Existing configuration.

    Returns
    -------
    CosmosConfig
        Updated configuration.
    """

    runtime = RuntimeConfig(
        debug=_get_env_bool(
            "COSMOS_DEBUG",
            config.runtime.debug,
        ),
        verbose=_get_env_bool(
            "COSMOS_VERBOSE",
            config.runtime.verbose,
        ),
        safe_mode=_get_env_bool(
            "COSMOS_SAFE_MODE",
            config.runtime.safe_mode,
        ),
        test_mode=_get_env_bool(
            "COSMOS_TEST_MODE",
            config.runtime.test_mode,
        ),
    )

    logging_config = (
        LoggingConfig(
            log_level=(
                _get_log_level()
            ),
            max_log_file_size_mb=(
                _get_env_int(
                    "COSMOS_MAX_LOG_FILE_SIZE_MB",
                    config.logging.max_log_file_size_mb,
                )
            ),
            backup_log_count=(
                _get_env_int(
                    "COSMOS_BACKUP_LOG_COUNT",
                    config.logging.backup_log_count,
                )
            ),
        )
    )

    solver = SolverConfig(
        max_iterations=(
            _get_env_int(
                "COSMOS_MAX_ITERATIONS",
                config.solver.max_iterations,
            )
        ),
        relative_tolerance=(
            _get_env_float(
                "COSMOS_RELATIVE_TOLERANCE",
                config.solver.relative_tolerance,
            )
        ),
        absolute_tolerance=(
            _get_env_float(
                "COSMOS_ABSOLUTE_TOLERANCE",
                config.solver.absolute_tolerance,
            )
        ),
        solver_timeout=(
            _get_env_float(
                "COSMOS_SOLVER_TIMEOUT",
                config.solver.solver_timeout,
            )
        ),
    )

    return CosmosConfig(
        metadata=config.metadata,
        runtime=runtime,
        environment=(
            _get_environment()
        ),
        directories=(
            config.directories
        ),
        logging=logging_config,
        validation=(
            config.validation
        ),
        solver=solver,
        precision=(
            config.precision
        ),
        units=config.units,
        cea=config.cea,
        cfd=config.cfd,
        physics=config.physics,
        optimization=(
            config.optimization
        ),
        machine_learning=(
            config.machine_learning
        ),
        gui=config.gui,
        database=(
            config.database
        ),
        materials_database=(
            config.materials_database
        ),
        cache=config.cache,
        project=config.project,
        simulation=(
            config.simulation
        ),
        export=config.export,
        resources=(
            config.resources
        ),
        security=(
            config.security
        ),
        backup=config.backup,
        audit=config.audit,
        plugins=config.plugins,
        api=config.api,
        testing=config.testing,
        config_hash="",
    )    
# ============================================================================
# Configuration Hash Management
# ============================================================================


def _attach_configuration_hash(
    config: CosmosConfig,
) -> CosmosConfig:
    """
    Attach deterministic configuration hash.

    Parameters
    ----------
    config : CosmosConfig
        Configuration object.

    Returns
    -------
    CosmosConfig
        Configuration with SHA256 hash.
    """

    payload = config.to_dict()

    payload.pop(
        "config_hash",
        None,
    )

    config_hash = _calculate_config_hash(
        payload
    )

    return replace(
        config,
        config_hash=config_hash,
    )


# ============================================================================
# Configuration Loader
# ============================================================================


def load_config() -> CosmosConfig:
    """
    Load, override, validate,
    initialize and return COSMOS
    configuration.

    Returns
    -------
    CosmosConfig
        Validated configuration.
    """

    LOGGER.info(
        "Loading COSMOS configuration."
    )

    config = (
        _build_default_configuration()
    )

    config = (
        _apply_environment_overrides(
            config
        )
    )

    validate_config(
        config
    )

    create_required_directories(
        config
    )

    config = (
        _attach_configuration_hash(
            config
        )
    )

    LOGGER.info(
        "COSMOS configuration loaded."
    )

    return config


# ============================================================================
# Export Utilities
# ============================================================================


def export_config(
    config: CosmosConfig,
    output_file: Path,
) -> None:
    """
    Export configuration to JSON.

    Parameters
    ----------
    config : CosmosConfig
        Configuration object.

    output_file : Path
        Output file path.
    """

    try:
        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            config.to_json(),
            encoding="utf-8",
        )

    except OSError as exc:
        raise ConfigurationError(
            f"Failed exporting "
            f"configuration to "
            f"{output_file}"
        ) from exc


# ============================================================================
# Compatibility Access API
# ============================================================================


def get_setting(
    key: str,
) -> object:
    """
    Compatibility accessor.

    Parameters
    ----------
    key : str
        Configuration key.

    Returns
    -------
    object
        Configuration value.

    Notes
    -----
    This API exists for
    backward compatibility.

    New code should access
    configuration through
    core.settings.
    """

    if not hasattr(
        CONFIG,
        key,
    ):
        raise InvalidInputError(
            f"Unknown configuration "
            f"attribute: {key}"
        )

    return getattr(
        CONFIG,
        key,
    )


# ============================================================================
# Shutdown Support
# ============================================================================


def shutdown_config() -> None:
    """
    Shutdown configuration
    subsystem.

    Notes
    -----
    Configuration is immutable.

    No resources require
    explicit cleanup at
    present.

    Function retained for
    future lifecycle
    compatibility.
    """

    LOGGER.info(
        "Configuration subsystem "
        "shutdown."
    )


# ============================================================================
# Module Initialization
# ============================================================================

try:

    with _CONFIG_LOCK:

        CONFIG: Final[
            CosmosConfig
        ] = load_config()

except Exception as exc:

    raise ConfigurationInitializationError(
        "Failed to initialize "
        "COSMOS configuration."
    ) from exc