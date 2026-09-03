"""
COSMOS Rocket Propulsion Platform

Module: core.exceptions
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Define the shared COSMOS exception hierarchy.

Description:
    Provides domain-specific exception types for consistent error handling
    across COSMOS. All application exceptions derive from :class:`CosmosError`
    so callers may catch either a precise failure or any COSMOS failure.

Examples
--------
Raise a validation failure while preserving its original cause:

>>> try:
...     float("invalid")
... except ValueError as exc:
...     error = InvalidInputError("Invalid chamber pressure.")
...     error.__cause__ = exc
>>> str(error)
'Invalid chamber pressure.'
"""

from __future__ import annotations

__all__ = (
    "CFDError",
    "ConfigurationError",
    "ContractError",
    "CoreError",
    "CosmosError",
    "DatabaseError",
    "DimensionError",
    "GeometryError",
    "GUIError",
    "InvalidInputError",
    "RegistryError",
    "SerializationError",
    "SolverConvergenceError",
    "SolverError",
    "UnitError",
    "ValidationError",
)


class CoreError(Exception):
    """Base class for domain-independent Core layer failures."""


class CosmosError(CoreError):
    """Base class for every application-defined COSMOS exception."""


class ConfigurationError(CosmosError):
    """Indicate invalid or inconsistent Core configuration."""


class ValidationError(CosmosError):
    """Indicate that data failed a COSMOS validation requirement."""


class InvalidInputError(ValidationError):
    """Indicate that an input value or input combination is invalid."""


class UnitError(CosmosError):
    """Indicate a unit definition, conversion, or compatibility failure."""


class DimensionError(CosmosError):
    """Indicate a dimensional analysis or compatibility failure."""


class SerializationError(CosmosError):
    """Indicate deterministic serialization or deserialization failure."""


class ContractError(CosmosError):
    """Indicate violation of a Core interface contract."""


class RegistryError(CosmosError):
    """Indicate failure in a Core registry operation."""


class GeometryError(CosmosError):
    """Indicate that geometry is invalid or cannot be generated."""


class SolverError(CosmosError):
    """Indicate that a numerical or engineering solver failed."""


class SolverConvergenceError(SolverError):
    """Indicate that a solver did not satisfy its convergence criteria."""


class DatabaseError(CosmosError):
    """Indicate that a COSMOS database operation failed."""


class CFDError(CosmosError):
    """Indicate that a CFD setup, execution, or result operation failed."""


class GUIError(CosmosError):
    """Indicate that a COSMOS graphical interface operation failed."""
