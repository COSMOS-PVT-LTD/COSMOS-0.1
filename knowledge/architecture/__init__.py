"""Knowledge architecture closure package."""

from __future__ import annotations

from knowledge.architecture.dispositions import ArchitectureDisposition
from knowledge.architecture.reconciliation_registry import (
    ReconciliationRegistry,
    load_reconciliation_registry,
)

__all__ = (
    "ArchitectureDisposition",
    "ReconciliationRegistry",
    "load_reconciliation_registry",
)
