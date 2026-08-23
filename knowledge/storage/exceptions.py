"""Storage exceptions for production local knowledge persistence."""

from __future__ import annotations

__all__ = (
    "CorruptionError",
    "SchemaMismatchError",
    "StorageError",
    "StaleStateError",
)


class StorageError(Exception):
    """Base storage error."""


class CorruptionError(StorageError):
    """Raised when persisted data fails integrity verification."""


class SchemaMismatchError(StorageError):
    """Raised when persisted schema/version is incompatible."""


class StaleStateError(StorageError):
    """Raised when persisted state is stale relative to authoritative knowledge."""


def _coerce_int(value: object, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default
