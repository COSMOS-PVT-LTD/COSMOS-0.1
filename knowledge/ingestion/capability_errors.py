"""Additive ingestion capability errors — does not modify frozen exceptions."""

from __future__ import annotations

from knowledge.ingestion.exceptions import IngestionAdapterError

__all__ = ("IngestionNotProvisionedError",)


class IngestionNotProvisionedError(IngestionAdapterError):
    """Raised when a loader exists as a contract but runtime capability is not provisioned."""
