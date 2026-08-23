# Step 7 — Retrieval Production Design

## Service: `ProductionRetrievalService`

Wraps W7 search primitives with production concerns:

- Index bundle hydration from `IndexLifecycleManager`
- Document-level access control (`allowed_document_ids`)
- Retrieval diagnostics via `build_retrieval_diagnostics()`
- Observability event recording

## Query Path

```
QueryRequest
  → load valid index bundle
  → lexical search (W7)
  → semantic search (W7 + local embeddings)
  → graph adjacency expansion (W7)
  → merge + rank
  → filter by allowed_document_ids
  → QueryResponse(hits, diagnostics)
```

## Request / Response Contract

### `QueryRequest`

| Field | Type | Description |
|-------|------|-------------|
| `query_text` | str | User query |
| `allowed_document_ids` | tuple[str, ...] | Access control filter |
| `top_k` | int | Max results |

### `QueryResponse`

| Field | Type | Description |
|-------|------|-------------|
| `hits` | list | Ranked retrieval results |
| `diagnostics` | dict | Path coverage, timing, filter stats |

## Access Control

Results filtered post-retrieval by `allowed_document_ids`. Empty filter tuple returns all document-scoped hits.

## Diagnostics Integration

Uses Step 6 `build_retrieval_diagnostics()` for structured diagnostic output including:

- Paths exercised (lexical, semantic, graph)
- Hit counts per path
- Filter application stats

## Failure Modes

| Condition | Behavior |
|-----------|----------|
| Stale index bundle | `StaleStateError` → caller rebuilds |
| Corrupt bundle | `CorruptionError` |
| No index loaded | Empty results with diagnostic note |

## Pipeline Integration

`ProductionLocalRAGPipeline.query()` orchestrates:

1. Offline guard check
2. Index load/validate
3. Retrieval service invocation
4. Observability recording
