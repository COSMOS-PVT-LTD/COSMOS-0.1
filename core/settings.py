"""
COSMOS Rocket Propulsion Platform

Module: core.settings
Author: COSMOS Development Team
Version: 0.1.1

Purpose
-------
Runtime settings authority for COSMOS.

Description
-----------
Provides a thread-safe immutable runtime
settings layer built on top of the validated
CosmosConfig produced by core.config_v0_1_1.

This module serves as the single global
access point for configuration throughout
the COSMOS platform.

Examples
--------
>>> from core.settings import settings
>>> settings.max_iterations
1000
"""

from __future__ import annotations

# ============================================================================
# Standard Library
# ============================================================================

import json

from dataclasses import dataclass

from datetime import datetime

from enum import Enum

from pathlib import Path

from typing import Final
from typing import Any

# ============================================================================
# COSMOS Core
# ============================================================================

from core.exceptions import CosmosError

from core.config_v0_1_1 import CosmosConfig
from core.config_v0_1_1 import Environment
from core.config_v0_1_1 import CONFIG

# ============================================================================
# Public Exports
# ============================================================================

__all__ = (
    "LifecycleState",
    "AuditMetadata",
    "RuntimeSettings",
    "SettingsError",
    "SettingsAlreadyInitializedError",
    "SettingsNotInitializedError",
    "SettingsShutdownError",
    "SettingsInjectionError",
    "initialize_settings",
    "get_settings",
    "shutdown_settings",
    "is_initialized",
    "get_configuration_hash",
    "get_app_version",
    "get_config_version",
    "get_environment",
    "to_dict",
    "to_json",
    "settings",
)

# ============================================================================
# Settings Exceptions
# ============================================================================


class SettingsError(
    CosmosError,
):
    """
    Base settings exception.
    """


class SettingsAlreadyInitializedError(
    SettingsError,
):
    """
    Raised when settings are
    initialized more than once.
    """


class SettingsNotInitializedError(
    SettingsError,
):
    """
    Raised when settings are
    accessed before initialization.
    """


class SettingsShutdownError(
    SettingsError,
):
    """
    Raised when settings are
    accessed after shutdown.
    """


class SettingsInjectionError(
    SettingsError,
):
    """
    Raised when test settings
    injection fails.
    """


# ============================================================================
# Lifecycle State
# ============================================================================


class LifecycleState(
    str,
    Enum,
):
    """
    Runtime settings lifecycle.
    """

    UNINITIALIZED = (
        "UNINITIALIZED"
    )

    INITIALIZING = (
        "INITIALIZING"
    )

    INITIALIZED = (
        "INITIALIZED"
    )

    SHUTDOWN = (
        "SHUTDOWN"
    )


# ============================================================================
# Audit Metadata
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class AuditMetadata:
    """
    Runtime audit metadata.
    """

    configuration_hash: str

    app_version: str

    config_version: str

    build_date: str

    environment: Environment

    initialized_at: str


# ============================================================================
# Runtime Settings Container
# ============================================================================


@dataclass(
    slots=True,
    frozen=True,
)
class RuntimeSettings:
    """
    Immutable runtime settings.

    Parameters
    ----------
    config : CosmosConfig
        Validated configuration.

    audit_metadata : AuditMetadata
        Runtime audit information.
    """

    config: CosmosConfig

    audit_metadata: AuditMetadata

    def to_dict(
        self,
    ) -> dict[str, object]:
        """
        Export settings to dictionary.

        Returns
        -------
        dict[str, object]
        """

        return {
            "config": (
                self.config.to_dict()
            ),
            "audit_metadata": {
                "configuration_hash":
                self.audit_metadata.configuration_hash,

                "app_version":
                self.audit_metadata.app_version,

                "config_version":
                self.audit_metadata.config_version,

                "build_date":
                self.audit_metadata.build_date,

                "environment":
                self.audit_metadata.environment.value,

                "initialized_at":
                self.audit_metadata.initialized_at,
            },
        }

    def to_json(
        self,
        indent: int = 4,
    ) -> str:
        """
        Export settings as JSON.
        """

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )


# ============================================================================
# Settings Proxy
# ============================================================================


class SettingsProxy:
    """
    Global runtime settings proxy.

    Allows:

    >>> settings.max_iterations

    instead of:

    >>> get_settings()
    >>> .config.solver.max_iterations
    """

    def __getattr__(
        self,
        name: str,
    ) -> Any:

        runtime_settings = (
            _SETTINGS_INSTANCE
        )

        if runtime_settings is None:
            raise (
                SettingsNotInitializedError(
                    "Settings have not "
                    "been initialized."
                )
            )

        config = runtime_settings.config

        #
        # Metadata
        #

        if hasattr(
            config.metadata,
            name,
        ):
            return getattr(
                config.metadata,
                name,
            )

        #
        # Runtime
        #

        if hasattr(
            config.runtime,
            name,
        ):
            return getattr(
                config.runtime,
                name,
            )

        #
        # Logging
        #

        if hasattr(
            config.logging,
            name,
        ):
            return getattr(
                config.logging,
                name,
            )

        #
        # Solver
        #

        if hasattr(
            config.solver,
            name,
        ):
            return getattr(
                config.solver,
                name,
            )

        #
        # Directories
        #

        if hasattr(
            config.directories,
            name,
        ):
            return getattr(
                config.directories,
                name,
            )

        #
        # Resources
        #

        if hasattr(
            config.resources,
            name,
        ):
            return getattr(
                config.resources,
                name,
            )

        #
        # Environment
        #

        if name == "environment":
             return config.environment

        raise AttributeError(
            f"Unknown settings "
            f"attribute: {name}"
        )


# ============================================================================
# Internal Runtime State
# ============================================================================

_SETTINGS_INSTANCE: (
    RuntimeSettings | None
) = None

settings: Final[
    SettingsProxy
] = SettingsProxy()

# ============================================================================
# Standard Library
# ============================================================================

from threading import RLock

# ============================================================================
# Internal Synchronization
# ============================================================================

_SETTINGS_LOCK: Final[RLock] = RLock()

_LIFECYCLE_STATE: LifecycleState = (
    LifecycleState.UNINITIALIZED
)

# ============================================================================
# Settings Manager
# ============================================================================


class SettingsManager:
    """
    Runtime settings authority.

    Responsibilities
    ----------------
    * Lifecycle management
    * Singleton enforcement
    * Thread-safe access
    * Audit metadata generation
    * Test injection support

    Notes
    -----
    Only one RuntimeSettings
    instance may exist at a time.
    """

    @staticmethod
    def lifecycle_state(
    ) -> LifecycleState:
        """
        Return current lifecycle state.

        Returns
        -------
        LifecycleState
        """

        return _LIFECYCLE_STATE

    @staticmethod
    def is_initialized(
    ) -> bool:
        """
        Check initialization state.

        Returns
        -------
        bool
        """

        return (
            _LIFECYCLE_STATE
            is LifecycleState.INITIALIZED
        )

    @staticmethod
    def build_audit_metadata(
        config: CosmosConfig,
    ) -> AuditMetadata:
        """
        Build runtime audit metadata.

        Parameters
        ----------
        config : CosmosConfig

        Returns
        -------
        AuditMetadata
        """

        return AuditMetadata(
            configuration_hash=(
                config.config_hash
            ),
            app_version=(
                config.metadata.app_version
            ),
            config_version=(
                config.metadata.config_version
            ),
            build_date=(
                config.metadata.build_date
            ),
            environment=(
                config.environment
            ),
            initialized_at=(
                datetime.utcnow()
                .isoformat()
            ),
        )

    @staticmethod
    def initialize(
        config: CosmosConfig,
    ) -> RuntimeSettings:
        """
        Initialize runtime settings.

        Parameters
        ----------
        config : CosmosConfig

        Returns
        -------
        RuntimeSettings

        Raises
        ------
        SettingsAlreadyInitializedError
        """

        global _SETTINGS_INSTANCE
        global _LIFECYCLE_STATE

        with _SETTINGS_LOCK:

            if (
                _LIFECYCLE_STATE
                is LifecycleState.INITIALIZED
            ):
                raise (
                    SettingsAlreadyInitializedError(
                        "Settings are "
                        "already initialized."
                    )
                )

            if (
                _LIFECYCLE_STATE
                is LifecycleState.INITIALIZING
            ):
                raise (
                    SettingsAlreadyInitializedError(
                        "Settings are "
                        "currently "
                        "initializing."
                    )
                )

            _LIFECYCLE_STATE = (
                LifecycleState.INITIALIZING
            )

            try:

                audit = (
                    SettingsManager
                    .build_audit_metadata(
                        config
                    )
                )

                runtime_settings = (
                    RuntimeSettings(
                        config=config,
                        audit_metadata=(
                            audit
                        ),
                    )
                )

                _SETTINGS_INSTANCE = (
                    runtime_settings
                )

                _LIFECYCLE_STATE = (
                    LifecycleState
                    .INITIALIZED
                )

                return runtime_settings

            except Exception:

                _SETTINGS_INSTANCE = None

                _LIFECYCLE_STATE = (
                    LifecycleState
                    .UNINITIALIZED
                )

                raise

    @staticmethod
    def get(
    ) -> RuntimeSettings:
        """
        Return active settings.

        Returns
        -------
        RuntimeSettings

        Raises
        ------
        SettingsNotInitializedError
        """

        if (
            _LIFECYCLE_STATE
            is LifecycleState.SHUTDOWN
        ):
            raise (
                SettingsShutdownError(
                    "Settings have "
                    "already been "
                    "shut down."
                )
            )

        if (
            _SETTINGS_INSTANCE
            is None
        ):
            raise (
                SettingsNotInitializedError(
                    "Settings are "
                    "not initialized."
                )
            )

        return _SETTINGS_INSTANCE

    @staticmethod
    def shutdown(
    ) -> None:
        """
        Shutdown runtime settings.

        Notes
        -----
        Clears singleton instance.
        """

        global _SETTINGS_INSTANCE
        global _LIFECYCLE_STATE

        with _SETTINGS_LOCK:

            if (
                _LIFECYCLE_STATE
                is LifecycleState.SHUTDOWN
            ):
                raise (
                    SettingsShutdownError(
                        "Settings are "
                        "already shut "
                        "down."
                    )
                )

            _SETTINGS_INSTANCE = None

            _LIFECYCLE_STATE = (
                LifecycleState.SHUTDOWN
            )

    @staticmethod
    def reset(
    ) -> None:
        """
        Internal test helper.

        Notes
        -----
        Not part of public API.
        """

        global _SETTINGS_INSTANCE
        global _LIFECYCLE_STATE

        with _SETTINGS_LOCK:

            _SETTINGS_INSTANCE = None

            _LIFECYCLE_STATE = (
                LifecycleState
                .UNINITIALIZED
            )

# ============================================================================
# Public Lifecycle API
# ============================================================================


def initialize_settings(
    config: CosmosConfig,
) -> RuntimeSettings:
    """
    Initialize runtime settings.

    Parameters
    ----------
    config : CosmosConfig
        Validated COSMOS configuration.

    Returns
    -------
    RuntimeSettings
        Initialized runtime settings.
    """

    return SettingsManager.initialize(
        config
    )


def get_settings(
) -> RuntimeSettings:
    """
    Return active runtime settings.

    Returns
    -------
    RuntimeSettings

    Raises
    ------
    SettingsNotInitializedError
    """

    return SettingsManager.get()


def shutdown_settings(
) -> None:
    """
    Shutdown settings subsystem.
    """

    SettingsManager.shutdown()


def is_initialized(
) -> bool:
    """
    Check initialization status.

    Returns
    -------
    bool
    """

    return (
        SettingsManager
        .is_initialized()
    )


# ============================================================================
# Runtime Metadata Access
# ============================================================================


def get_configuration_hash(
) -> str:
    """
    Return configuration hash.

    Returns
    -------
    str
    """

    return (
        get_settings()
        .audit_metadata
        .configuration_hash
    )


def get_app_version(
) -> str:
    """
    Return application version.

    Returns
    -------
    str
    """

    return (
        get_settings()
        .audit_metadata
        .app_version
    )


def get_config_version(
) -> str:
    """
    Return configuration version.

    Returns
    -------
    str
    """

    return (
        get_settings()
        .audit_metadata
        .config_version
    )


def get_environment(
) -> Environment:
    """
    Return active environment.

    Returns
    -------
    Environment
    """

    return (
        get_settings()
        .audit_metadata
        .environment
    )


# ============================================================================
# Convenience Runtime Access
# ============================================================================


def to_dict(
) -> dict[str, object]:
    """
    Export runtime settings.

    Returns
    -------
    dict[str, object]
    """

    return (
        get_settings()
        .to_dict()
    )


def to_json(
    indent: int = 4,
) -> str:
    """
    Export runtime settings.

    Parameters
    ----------
    indent : int

    Returns
    -------
    str
    """

    return (
        get_settings()
        .to_json(
            indent=indent
        )
    )


# ============================================================================
# Automatic Bootstrap
# ============================================================================

try:

    initialize_settings(
        CONFIG
    )

except SettingsAlreadyInitializedError:

    pass 

# ============================================================================
# Testing Utilities
# ============================================================================

from contextlib import contextmanager


def create_mock_settings(
) -> RuntimeSettings:
    """
    Create a fully valid mock settings object.

    Returns
    -------
    RuntimeSettings
        Mock runtime settings instance.

    Notes
    -----
    Intended for:

    * unit testing
    * integration testing
    * dependency injection
    """

    audit_metadata = AuditMetadata(
        configuration_hash=(
            CONFIG.config_hash
        ),
        app_version=(
            CONFIG.metadata.app_version
        ),
        config_version=(
            CONFIG.metadata.config_version
        ),
        build_date=(
            CONFIG.metadata.build_date
        ),
        environment=(
            CONFIG.environment
        ),
        initialized_at=(
            datetime.utcnow()
            .isoformat()
        ),
    )

    return RuntimeSettings(
        config=CONFIG,
        audit_metadata=(
            audit_metadata
        ),
    )


# ============================================================================
# Settings Injection
# ============================================================================


def inject_settings(
    runtime_settings: RuntimeSettings,
) -> None:
    """
    Inject runtime settings.

    Parameters
    ----------
    runtime_settings : RuntimeSettings

    Raises
    ------
    SettingsInjectionError
    """

    global _SETTINGS_INSTANCE
    global _LIFECYCLE_STATE

    if not isinstance(
        runtime_settings,
        RuntimeSettings,
    ):
        raise SettingsInjectionError(
            "Injected object must "
            "be RuntimeSettings."
        )

    with _SETTINGS_LOCK:

        _SETTINGS_INSTANCE = (
            runtime_settings
        )

        _LIFECYCLE_STATE = (
            LifecycleState
            .INITIALIZED
        )


@contextmanager
def temporary_settings(
    runtime_settings: RuntimeSettings,
):
    """
    Temporarily replace active settings.

    Parameters
    ----------
    runtime_settings : RuntimeSettings

    Examples
    --------
    >>> mock = create_mock_settings()
    >>> with temporary_settings(mock):
    ...     pass
    """

    global _SETTINGS_INSTANCE
    global _LIFECYCLE_STATE

    with _SETTINGS_LOCK:

        previous_settings = (
            _SETTINGS_INSTANCE
        )

        previous_state = (
            _LIFECYCLE_STATE
        )

        inject_settings(
            runtime_settings
        )

    try:

        yield runtime_settings

    finally:

        with _SETTINGS_LOCK:

            _SETTINGS_INSTANCE = (
                previous_settings
            )

            _LIFECYCLE_STATE = (
                previous_state
            )


# ============================================================================
# Internal Diagnostics
# ============================================================================


def get_lifecycle_state(
) -> LifecycleState:
    """
    Return current lifecycle state.

    Returns
    -------
    LifecycleState
    """

    return (
        SettingsManager
        .lifecycle_state()
    )


def get_audit_metadata(
) -> AuditMetadata:
    """
    Return audit metadata.

    Returns
    -------
    AuditMetadata
    """

    return (
        get_settings()
        .audit_metadata
    )


# ============================================================================
# Final Export Update
# ============================================================================

___all__ = (
    *__all__,
    "create_mock_settings",
    "inject_settings",
    "temporary_settings",
    "get_lifecycle_state",
    "get_audit_metadata",
)
# ============================================================================
# Runtime Validation
# ============================================================================


def validate_runtime_settings() -> None:
    """
    Validate runtime settings integrity.

    Raises
    ------
    SettingsNotInitializedError
        If settings are not initialized.

    SettingsError
        If runtime integrity checks fail.
    """

    runtime_settings = get_settings()

    if runtime_settings.config is None:
        raise SettingsError(
            "Runtime configuration is missing."
        )

    if not (
        runtime_settings
        .audit_metadata
        .configuration_hash
    ):
        raise SettingsError(
            "Configuration hash is missing."
        )

    if (
        _LIFECYCLE_STATE
        is not LifecycleState.INITIALIZED
    ):
        raise SettingsError(
            "Lifecycle state mismatch."
        )


# ============================================================================
# Runtime Diagnostics
# ============================================================================


def get_runtime_summary(
) -> dict[str, object]:
    """
    Return runtime diagnostics summary.

    Returns
    -------
    dict[str, object]
        Runtime information.
    """

    runtime_settings = get_settings()

    return {
        "initialized": (
            is_initialized()
        ),
        "lifecycle_state": (
            _LIFECYCLE_STATE.value
        ),
        "environment": (
            runtime_settings
            .audit_metadata
            .environment
            .value
        ),
        "app_version": (
            runtime_settings
            .audit_metadata
            .app_version
        ),
        "config_version": (
            runtime_settings
            .audit_metadata
            .config_version
        ),
        "configuration_hash": (
            runtime_settings
            .audit_metadata
            .configuration_hash
        ),
        "initialized_at": (
            runtime_settings
            .audit_metadata
            .initialized_at
        ),
    }


# ============================================================================
# Bootstrap Verification
# ============================================================================


def verify_bootstrap() -> bool:
    """
    Verify successful startup.

    Returns
    -------
    bool
        True if runtime settings
        are operational.
    """

    try:

        validate_runtime_settings()

        return True

    except SettingsError:

        return False



# ============================================================================
# Extended Proxy Coverage
# ============================================================================

#
# NOTE:
# Add the following block INSIDE
# SettingsProxy.__getattr__()
#
# Place it immediately before:
#
# raise AttributeError(...)
#
# ---------------------------------------------------------------------------
#
#        if hasattr(
#            config.cea,
#            name,
#        ):
#            return getattr(
#                config.cea,
#                name,
#            )
#
#        if hasattr(
#            config.cfd,
#            name,
#        ):
#            return getattr(
#                config.cfd,
#                name,
#            )
#
#        if hasattr(
#            config.physics,
#            name,
#        ):
#            return getattr(
#                config.physics,
#                name,
#            )
#
#        if hasattr(
#            config.optimization,
#            name,
#        ):
#            return getattr(
#                config.optimization,
#                name,
#            )
#
#        if hasattr(
#            config.machine_learning,
#            name,
#        ):
#            return getattr(
#                config.machine_learning,
#                name,
#            )
#
#        if hasattr(
#            config.gui,
#            name,
#        ):
#            return getattr(
#                config.gui,
#                name,
#            )
#
#        if hasattr(
#            config.database,
#            name,
#        ):
#            return getattr(
#                config.database,
#                name,
#            )
#
#        if hasattr(
#            config.materials_database,
#            name,
#        ):
#            return getattr(
#                config.materials_database,
#                name,
#            )
#
#        if hasattr(
#            config.cache,
#            name,
#        ):
#            return getattr(
#                config.cache,
#                name,
#            )
#
#        if hasattr(
#            config.project,
#            name,
#        ):
#            return getattr(
#                config.project,
#                name,
#            )
#
#        if hasattr(
#            config.simulation,
#            name,
#        ):
#            return getattr(
#                config.simulation,
#                name,
#            )
#
#        if hasattr(
#            config.export,
#            name,
#        ):
#            return getattr(
#                config.export,
#                name,
#            )
#
#        if hasattr(
#            config.security,
#            name,
#        ):
#            return getattr(
#                config.security,
#                name,
#            )
#
#        if hasattr(
#            config.backup,
#            name,
#        ):
#            return getattr(
#                config.backup,
#                name,
#            )
#
#        if hasattr(
#            config.audit,
#            name,
#        ):
#            return getattr(
#                config.audit,
#                name,
#            )
#
#        if hasattr(
#            config.plugins,
#            name,
#        ):
#            return getattr(
#                config.plugins,
#                name,
#            )
#
#        if hasattr(
#            config.api,
#            name,
#        ):
#            return getattr(
#                config.api,
#                name,
#            )
#
#        if hasattr(
#            config.testing,
#            name,
#        ):
#            return getattr(
#                config.testing,
#                name,
#            )
#
# ---------------------------------------------------------------------------


# ============================================================================
# Final Export Update
# ============================================================================

__all__ = (
    "LifecycleState",
    "AuditMetadata",
    "RuntimeSettings",
    "SettingsError",
    "SettingsAlreadyInitializedError",
    "SettingsNotInitializedError",
    "SettingsShutdownError",
    "SettingsInjectionError",
    "initialize_settings",
    "get_settings",
    "shutdown_settings",
    "is_initialized",
    "get_configuration_hash",
    "get_app_version",
    "get_config_version",
    "get_environment",
    "to_dict",
    "to_json",
    "settings",
    "validate_runtime_settings",
    "get_runtime_summary",
    "verify_bootstrap",
)


# ============================================================================
# Module Self Verification
# ============================================================================

validate_runtime_settings()