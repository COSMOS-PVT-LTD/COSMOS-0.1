"""
COSMOS Knowledge Foundation

Module:
    knowledge.source.exceptions

Purpose:
    Source-system layer exceptions for W1 capabilities.
"""

from __future__ import annotations

from knowledge.graph.exceptions import GraphError, GraphValidationError

__all__ = (
    "IntegrityError",
    "IntegrityMismatchError",
    "IntegrityValidationError",
    "LicenseMetadataError",
    "SourceSystemError",
    "VaultError",
    "VaultNotFoundError",
    "VaultValidationError",
)


class SourceSystemError(GraphError):
    """Base class for W1 source-system failures."""


class IntegrityValidationError(GraphValidationError, SourceSystemError):
    """Indicate that an integrity contract failed validation."""


class IntegrityError(SourceSystemError):
    """Indicate that an integrity operation failed."""


class IntegrityMismatchError(IntegrityError):
    """Indicate that content does not match the expected digest."""


class LicenseMetadataError(SourceSystemError):
    """Indicate that license/IP metadata is invalid."""


class VaultError(SourceSystemError):
    """Base class for source-vault failures."""


class VaultValidationError(GraphValidationError, VaultError):
    """Indicate that a vault contract failed validation."""


class VaultNotFoundError(VaultError):
    """Indicate that a vault artifact was not found."""
