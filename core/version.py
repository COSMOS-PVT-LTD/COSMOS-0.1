"""
COSMOS Core — version information.

Provides deterministic, import-safe version metadata for traceability.
"""

from __future__ import annotations

from typing import Final

__all__ = (
    "CORE_API_VERSION",
    "CORE_SCHEMA_VERSION",
    "COSMOS_VERSION",
)

COSMOS_VERSION: Final[str] = "0.1.0"
"""COSMOS release version."""

CORE_API_VERSION: Final[str] = "1.0.0"
"""Stable public Core API contract version."""

CORE_SCHEMA_VERSION: Final[str] = "1.0.0"
"""Canonical serialization schema version for Core objects."""
