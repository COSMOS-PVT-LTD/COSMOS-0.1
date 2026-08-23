# Step 7 — Index Persistence Design

## Lifecycle States

```
BUILD → VALID → (INVALIDATE) → REBUILD
         ↓
        LOAD (from disk)
```

Managed by `IndexLifecycleManager` with explicit state transitions.

## Bundle Format (`PersistedIndexBundle`)

| Field | Description |
|-------|-------------|
| `format_version` | Bundle schema version |
| `source_digest` | Graph digest at build time |
| `embedding_model` | `EmbeddingModelIdentity` snapshot |
| `lifecycle_state` | Current `IndexLifecycleState` |
| `lexical_entries` | W7 lexical index entries |
| `semantic_entries` | W7 semantic index entries |
| `vector_records` | Embedding vectors per chunk |
| `graph_adjacency` | Graph traversal adjacency |

## Operations

| Operation | Description |
|-----------|-------------|
| `build()` | Construct bundle from graph + embedding backend |
| `load()` | Read bundle from disk, validate digests |
| `validate()` | Check bundle integrity without loading into memory |
| `invalidate()` | Mark bundle stale (graph changed) |
| `rebuild()` | Invalidate + build fresh bundle |

## Staleness Detection

On `load()`:
1. Read `source_digest` from bundle
2. Compare against current `StoreManifest.graph_digest`
3. Mismatch → `StaleStateError` (caller may trigger rebuild)

## Storage Path

Bundles stored under `<store_root>/indexes/<bundle_id>/` as separate JSON files for inspectability and partial recovery.

## W7 Alignment

Bundle contents map directly to W7 search index structures, enabling `ProductionRetrievalService` to hydrate in-memory indexes without re-embedding on every query (when bundle is valid).
