"""Public exports for knowledge.storage."""

from __future__ import annotations

from knowledge.storage.exceptions import (
    CorruptionError,
    SchemaMismatchError,
    StaleStateError,
    StorageError,
)
from knowledge.storage.index_lifecycle import IndexLifecycleManager, IndexLifecycleOperation
from knowledge.storage.local_store import (
    DocumentRecord,
    IngestionState,
    LocalKnowledgeStore,
    StoreManifest,
)
from knowledge.storage.schema import PRODUCTION_SCHEMA_VERSION

__all__ = (
    "CorruptionError",
    "DocumentRecord",
    "IndexLifecycleManager",
    "IndexLifecycleOperation",
    "IngestionState",
    "LocalKnowledgeStore",
    "PRODUCTION_SCHEMA_VERSION",
    "SchemaMismatchError",
    "StaleStateError",
    "StorageError",
    "StoreManifest",
)
