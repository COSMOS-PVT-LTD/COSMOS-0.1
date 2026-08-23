# Step 7 — Persistence Design

## Store Layout

```
<store_root>/
  manifest.json          # StoreManifest (schema_version, store_id, graph_digest)
  graph.json             # Canonical graph record
  documents.json         # Document registry (DocumentRecord entries)
  ingestion_state.json   # IngestionState (processed/skipped/failed counts)
  indexes/
    <bundle_id>/
      bundle.json        # PersistedIndexBundle metadata
      lexical.json
      semantic.json
      vectors.json
      graph_adjacency.json
```

## Schema Version

- `PRODUCTION_SCHEMA_VERSION = "1.0.0"` (`knowledge/storage/schema.py`)
- Mismatch on load → `SchemaMismatchError` (fail-closed)

## Core Types

| Type | Role |
|------|------|
| `StoreManifest` | Top-level store identity and graph digest |
| `DocumentRecord` | Per-document metadata + content fingerprints |
| `GraphRecord` | Serialized knowledge graph with digest |
| `IngestionState` | Incremental ingestion counters |
| `PersistedIndexBundle` | W7 index bundle with lifecycle state |

## Integrity Model

1. **Content hashing:** SHA-256 over normalized content (`content_hash`, `content_digest`)
2. **Graph digest:** Canonical serialization digest stored in manifest
3. **Bundle validation:** `source_digest` must match current graph digest on load
4. **Corruption detection:** `verify_integrity()` compares manifest vs on-disk graph

## API Surface (`LocalKnowledgeStore`)

| Method | Behavior |
|--------|----------|
| `initialize()` | Create empty store with manifest |
| `save_graph()` | Persist graph + update manifest digest |
| `register_document()` | Upsert document record |
| `get_document()` | Lookup by document_id |
| `save_ingestion_state()` | Persist ingestion counters |
| `verify_integrity()` | Validate manifest ↔ graph consistency |

## Limitations (Known)

- JSON file-backed — not suitable for high-concurrency multi-writer production
- No transactional multi-file atomicity (best-effort write ordering)
- Single-store model — no sharding or replication
