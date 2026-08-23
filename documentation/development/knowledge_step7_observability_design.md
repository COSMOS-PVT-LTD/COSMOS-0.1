# Step 7 — Observability Design

## Recorder: `ObservabilityRecorder`

Append-only in-memory event log with structured entries.

## Event Schema

```python
{
    "event_name": str,      # e.g. "ingest.completed", "query.executed"
    "timestamp_utc": str,   # ISO-8601 UTC
    "payload": dict,        # Event-specific data
}
```

## Event Catalog

| Event Name | Trigger | Payload Fields |
|------------|---------|----------------|
| `ingest.started` | Pipeline ingest begins | `document_id` |
| `ingest.completed` | Pipeline ingest succeeds | `document_id`, `node_count` |
| `ingest.failed` | Pipeline ingest fails | `document_id`, `error` |
| `index.built` | Index bundle created | `bundle_id`, `entry_counts` |
| `index.loaded` | Index bundle loaded | `bundle_id` |
| `index.invalidated` | Index marked stale | `bundle_id`, `reason` |
| `query.executed` | Retrieval completed | `query_text`, `hit_count`, `top_k` |
| `recovery.executed` | Recovery procedure run | `action`, `outcome` |

## API

| Method | Behavior |
|--------|----------|
| `record(event_name, **payload)` | Append event |
| `events()` | Return all recorded events |
| `events_for(name)` | Filter by event name |
| `clear()` | Reset log (testing) |

## Integration Points

- `ProductionLocalRAGPipeline` — ingest + query lifecycle
- `IncrementalIngestionCoordinator` — per-document outcomes
- `RecoveryProcedure` — recovery actions
- `IndexLifecycleManager` — index state transitions

## Production Gaps

Current implementation is **in-memory only**. Production deployment would require:

- Structured log export (JSON lines / OpenTelemetry)
- Log rotation and retention policy
- Correlation IDs across ingest/query paths
- Metrics aggregation (latency histograms, error rates)

These are documented for human gate review (§24 Gate 5).
