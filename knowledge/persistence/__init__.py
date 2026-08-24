"""Persistence surface for the knowledge foundation."""

from __future__ import annotations

from knowledge.foundation.persistence import dump_snapshot, load_snapshot
from knowledge.persistence.sqlite_store import (
    DatabaseUnavailableError,
    DuplicateSourceError,
    KnowledgeDatabase,
)

__all__ = (
    "DatabaseUnavailableError",
    "DuplicateSourceError",
    "KnowledgeDatabase",
    "dump_snapshot",
    "load_snapshot",
)
