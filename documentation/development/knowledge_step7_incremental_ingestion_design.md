# Step 7 — Incremental Ingestion Design

## Coordinator: `IncrementalIngestionCoordinator`

Coordinates document-level change detection and pipeline invocation without modifying the frozen base orchestrator.

## Change Detection

| Signal | Action |
|--------|--------|
| New `document_id` | Full pipeline ingest |
| Same `document_id`, different `content_hash` | Re-ingest (version bump) |
| Same `document_id`, same `content_hash` | Skip (increment `skipped_unchanged_count`) |
| Pipeline failure | Increment `failed_count`, propagate error |

## Flow

```
IngestBatch
  → for each document:
      → store.get_document(document_id)
      → compare content_hash
      → if changed: run_knowledge_pipeline_extended()
      → store.save_graph() + register_document()
      → update IngestionState counters
```

## State Tracking (`IngestionState`)

| Counter | Meaning |
|---------|---------|
| `processed_count` | Documents successfully ingested |
| `skipped_unchanged_count` | Documents skipped (unchanged hash) |
| `failed_count` | Documents that failed pipeline |

Persisted via `LocalKnowledgeStore.save_ingestion_state()`.

## Known Limitation

Current implementation replaces the **entire graph** with single-document pipeline output on each ingest. This is acceptable for:

- Unit/integration test qualification
- Single-document demo workflows

**Not yet suitable for** multi-document production corpora without graph merge logic. Documented as a follow-up for KG-BLOCK-014+ authorization.

## Idempotency

Re-ingesting identical content is a no-op (hash match → skip). Re-ingesting changed content triggers full re-pipeline and graph replacement.
