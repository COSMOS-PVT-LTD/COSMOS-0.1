"""
COSMOS Rocket Propulsion Platform

Module: tests.unit_tests.test_settings
Author: COSMOS Development Team
Version: 0.1.0

Purpose:
    Unit tests for core.settings.

Description:
    Verifies lifecycle management, singleton behavior,
    configuration export, audit metadata, bootstrap
    validation, and testing utilities.
"""

from __future__ import annotations

# Standard Library

import json

# Third Party

import pytest

# COSMOS Core

from core.config_v0_1_1 import CONFIG
from core.settings import (
    SettingsAlreadyInitializedError,
    SettingsShutdownError,
    create_mock_settings,
    get_app_version,
    get_config_version,
    get_configuration_hash,
    get_environment,
    get_settings,
    initialize_settings,
    inject_settings,
    is_initialized,
    shutdown_settings,
    to_dict,
    to_json,
    verify_bootstrap,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def reset_settings_state():
    """
    Ensure clean lifecycle state
    before and after each test.
    """

    try:
        shutdown_settings()
    except Exception:
        pass

    yield

    try:
        shutdown_settings()
    except Exception:
        pass


# ============================================================================
# Initialization Tests
# ============================================================================


def test_initialize_settings() -> None:
    """
    Verify settings initialization.
    """

    initialize_settings(CONFIG)

    assert is_initialized() is True


def test_get_settings_after_initialization() -> None:
    """
    Verify settings retrieval.
    """

    initialize_settings(CONFIG)

    settings = get_settings()

    assert settings is not None


def test_double_initialization_fails() -> None:
    """
    Verify duplicate initialization
    raises exception.
    """

    initialize_settings(CONFIG)

    with pytest.raises(
        SettingsAlreadyInitializedError
    ):
        initialize_settings(CONFIG)


# ============================================================================
# Shutdown Tests
# ============================================================================


def test_shutdown_settings() -> None:
    """
    Verify shutdown.
    """

    initialize_settings(CONFIG)

    shutdown_settings()

    assert is_initialized() is False


def test_access_after_shutdown_fails() -> None:
    """
    Verify access after shutdown.
    """

    initialize_settings(CONFIG)

    shutdown_settings()

    with pytest.raises(
        SettingsShutdownError
    ):
        get_settings()


# ============================================================================
# Audit Metadata Tests
# ============================================================================


def test_configuration_hash_exists() -> None:
    """
    Verify configuration hash.
    """

    initialize_settings(CONFIG)

    configuration_hash = (
        get_configuration_hash()
    )

    assert isinstance(
        configuration_hash,
        str,
    )

    assert len(
        configuration_hash
    ) > 0


def test_app_version_exists() -> None:
    """
    Verify application version.
    """

    initialize_settings(CONFIG)

    version = get_app_version()

    assert isinstance(
        version,
        str,
    )

    assert len(version) > 0


def test_config_version_exists() -> None:
    """
    Verify configuration version.
    """

    initialize_settings(CONFIG)

    version = get_config_version()

    assert isinstance(
        version,
        str,
    )

    assert len(version) > 0


def test_environment_exists() -> None:
    """
    Verify runtime environment.
    """

    initialize_settings(CONFIG)

    environment = (
        get_environment()
    )

    assert environment is not None


# ============================================================================
# Export Tests
# ============================================================================


def test_to_dict() -> None:
    """
    Verify dictionary export.
    """

    initialize_settings(CONFIG)

    data = to_dict()

    assert isinstance(
        data,
        dict,
    )


def test_to_json() -> None:
    """
    Verify JSON export.
    """

    initialize_settings(CONFIG)

    data = to_json()

    assert isinstance(
        data,
        str,
    )

    parsed = json.loads(data)

    assert isinstance(
        parsed,
        dict,
    )


# ============================================================================
# Mock Settings Tests
# ============================================================================


def test_create_mock_settings() -> None:
    """
    Verify mock settings creation.
    """

    settings = (
        create_mock_settings()
    )

    assert settings is not None


def test_inject_settings() -> None:
    """
    Verify settings injection.
    """

    mock_settings = (
        create_mock_settings()
    )

    inject_settings(
        mock_settings
    )

    active = get_settings()

    assert active is mock_settings


# ============================================================================
# Bootstrap Tests
# ============================================================================


def test_verify_bootstrap() -> None:
    """
    Verify bootstrap check.
    """

    initialize_settings(CONFIG)

    assert (
        verify_bootstrap()
        is True
    )


# ============================================================================
# Integration Tests
# ============================================================================


def test_runtime_settings_available() -> None:
    """
    Verify runtime settings
    contain configuration.
    """

    initialize_settings(CONFIG)

    settings = get_settings()

    assert (
        settings.config
        is not None
    )


def test_runtime_settings_export() -> None:
    """
    Verify export path.
    """

    initialize_settings(CONFIG)

    settings = get_settings()

    data = settings.to_dict()

    assert isinstance(
        data,
        dict,
    )


def test_runtime_json_export() -> None:
    """
    Verify JSON serialization.
    """

    initialize_settings(CONFIG)

    settings = get_settings()

    json_text = (
        settings.to_json()
    )

    assert isinstance(
        json_text,
        str,
    )