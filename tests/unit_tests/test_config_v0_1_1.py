"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_config_v0_1_1
Author: COSMOS Development Team
Version: 0.1.0

Purpose:
    Unit tests for core.config_v0_1_1.

Description:
    Verifies configuration loading, validation,
    serialization, immutability, directory creation,
    environment handling, and configuration integrity.
"""

from __future__ import annotations

# Standard Library

from dataclasses import FrozenInstanceError
from pathlib import Path

# Third Party

import pytest

# COSMOS Core

from core.config_v0_1_1 import (
    CONFIG,
    CosmosConfig,
    Environment,
    create_required_directories,
    get_project_root,
    load_config,
    validate_config,
)


# ============================================================================
# Configuration Loading
# ============================================================================


def test_load_config_returns_cosmos_config() -> None:
    """
    Verify load_config returns CosmosConfig.
    """

    config = load_config()

    assert isinstance(
        config,
        CosmosConfig,
    )


def test_global_config_exists() -> None:
    """
    Verify CONFIG exists.
    """

    assert isinstance(
        CONFIG,
        CosmosConfig,
    )


# ============================================================================
# Environment
# ============================================================================


def test_environment_enum_values() -> None:
    """
    Verify environment enum.
    """

    assert (
        Environment.DEVELOPMENT.value
        == "development"
    )

    assert (
        Environment.TESTING.value
        == "testing"
    )

    assert (
        Environment.PRODUCTION.value
        == "production"
    )


def test_environment_type() -> None:
    """
    Verify environment type.
    """

    assert isinstance(
        CONFIG.environment,
        Environment,
    )


# ============================================================================
# Metadata
# ============================================================================


def test_metadata_exists() -> None:
    """
    Verify metadata section.
    """

    assert (
        CONFIG.metadata.app_name
        != ""
    )

    assert (
        CONFIG.metadata.app_version
        != ""
    )

    assert (
        CONFIG.metadata.config_version
        != ""
    )


# ============================================================================
# Project Root
# ============================================================================


def test_project_root() -> None:
    """
    Verify project root.
    """

    root = get_project_root()

    assert isinstance(
        root,
        Path,
    )

    assert root.exists()


# ============================================================================
# Directories
# ============================================================================


def test_directory_configuration_exists() -> None:
    """
    Verify directory settings.
    """

    directories = (
        CONFIG.directories
    )

    assert (
        directories.project_root
        is not None
    )

    assert (
        directories.logs_dir
        is not None
    )

    assert (
        directories.cache_dir
        is not None
    )

    assert (
        directories.reports_dir
        is not None
    )


def test_create_required_directories() -> None:
    """
    Verify runtime directories.
    """

    create_required_directories(
        CONFIG
    )

    assert (
        CONFIG.directories.logs_dir
        .exists()
    )

    assert (
        CONFIG.directories.cache_dir
        .exists()
    )

    assert (
        CONFIG.directories.reports_dir
        .exists()
    )

    assert (
        CONFIG.directories.databases_dir
        .exists()
    )


# ============================================================================
# Validation
# ============================================================================


def test_validate_config() -> None:
    """
    Verify validation passes.
    """

    validate_config(CONFIG)


# ============================================================================
# Solver Configuration
# ============================================================================


def test_solver_configuration() -> None:
    """
    Verify solver settings.
    """

    assert (
        CONFIG.solver.max_iterations
        > 0
    )

    assert (
        CONFIG.solver.relative_tolerance
        > 0.0
    )

    assert (
        CONFIG.solver.absolute_tolerance
        > 0.0
    )

    assert (
        CONFIG.solver.solver_timeout
        > 0.0
    )


# ============================================================================
# Numerical Precision
# ============================================================================


def test_precision_configuration() -> None:
    """
    Verify precision settings.
    """

    assert (
        CONFIG.precision
        is not None
    )


# ============================================================================
# Unit System
# ============================================================================


def test_unit_system() -> None:
    """
    Verify unit system.
    """

    assert (
        CONFIG.units.default_unit_system
        == "SI"
    )


# ============================================================================
# Serialization
# ============================================================================


def test_to_dict() -> None:
    """
    Verify dictionary export.
    """

    data = CONFIG.to_dict()

    assert isinstance(
        data,
        dict,
    )


def test_to_json() -> None:
    """
    Verify JSON export.
    """

    json_text = (
        CONFIG.to_json()
    )

    assert isinstance(
        json_text,
        str,
    )

    assert len(
        json_text
    ) > 0


# ============================================================================
# Configuration Hash
# ============================================================================


def test_config_hash_exists() -> None:
    """
    Verify configuration hash.
    """

    assert isinstance(
        CONFIG.config_hash,
        str,
    )

    assert (
        len(
            CONFIG.config_hash
        )
        > 0
    )


# ============================================================================
# Immutability
# ============================================================================


def test_metadata_is_immutable() -> None:
    """
    Verify frozen dataclass.
    """

    with pytest.raises(
        FrozenInstanceError
    ):
        setattr(
            CONFIG.metadata,
            "app_name",
            "INVALID",
        )


# ============================================================================
# Resource Limits
# ============================================================================


def test_resource_limits() -> None:
    """
    Verify resource settings.
    """

    assert (
        CONFIG.resources.max_cpu_cores
        > 0
    )

    assert (
        CONFIG.resources.max_memory_gb
        > 0
    )


# ============================================================================
# Major Configuration Groups
# ============================================================================


def test_configuration_groups_exist() -> None:
    """
    Verify all major groups.
    """

    assert CONFIG.metadata
    assert CONFIG.runtime
    assert CONFIG.directories
    assert CONFIG.logging
    assert CONFIG.validation
    assert CONFIG.solver
    assert CONFIG.precision
    assert CONFIG.units

    assert CONFIG.cea
    assert CONFIG.cfd
    assert CONFIG.physics
    assert CONFIG.optimization
    assert CONFIG.machine_learning

    assert CONFIG.gui
    assert CONFIG.database
    assert CONFIG.materials_database

    assert CONFIG.cache
    assert CONFIG.project
    assert CONFIG.simulation
    assert CONFIG.export

    assert CONFIG.resources
    assert CONFIG.security
    assert CONFIG.backup
    assert CONFIG.audit

    assert CONFIG.plugins
    assert CONFIG.api
    assert CONFIG.testing


# ============================================================================
# Deterministic Hash
# ============================================================================


def test_configuration_hash_is_deterministic() -> None:
    """
    Verify stable hash generation.
    """

    config_a = load_config()
    config_b = load_config()

    assert (
        config_a.config_hash
        ==
        config_b.config_hash
    )