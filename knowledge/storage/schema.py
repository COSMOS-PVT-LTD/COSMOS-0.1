"""Production storage schema version constants."""

from __future__ import annotations

PRODUCTION_SCHEMA_VERSION = "1.0.0"
INDEX_BUNDLE_FORMAT_VERSION = "1.0.0"
STORE_MANIFEST_FILENAME = "manifest.json"
GRAPH_SNAPSHOT_FILENAME = "graph_snapshot.json"
INDEX_BUNDLE_FILENAME = "w7_index_bundle.json"
DOCUMENT_REGISTRY_FILENAME = "document_registry.json"
INGESTION_STATE_FILENAME = "ingestion_state.json"

__all__ = (
    "DOCUMENT_REGISTRY_FILENAME",
    "GRAPH_SNAPSHOT_FILENAME",
    "INDEX_BUNDLE_FILENAME",
    "INDEX_BUNDLE_FORMAT_VERSION",
    "INGESTION_STATE_FILENAME",
    "PRODUCTION_SCHEMA_VERSION",
    "STORE_MANIFEST_FILENAME",
)
