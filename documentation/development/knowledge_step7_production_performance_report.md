# Step 7 — Production Performance Report (Gate Closure)

**Date:** 2026-08-23  
**Harness:** `knowledge/production/benchmark_suite.py`

## Benchmark Envelope

| Parameter | Verified | Unverified |
|-----------|----------|------------|
| Document count | 1–5 | 100+ |
| Corpus type | Short markdown fixtures | Full engineering libraries |
| Hardware | Local developer machine | Production deployment hardware |
| Concurrency | Single-threaded | Multi-user load |

## Operations Measured

| Operation | Measured |
|-----------|----------|
| Ingestion end-to-end | ✅ |
| Persistence load | ✅ |
| Recovery | ✅ |
| Query cold-start | ✅ |
| Query warm | ✅ |
| Memory peak | ✅ (tracemalloc + RSS) |
| Storage footprint | ✅ (directory size) |

## Operations Not Separately Instrumented (Limitation)

- Parsing/extraction latency (included in ingestion end-to-end)
- Per-path retrieval (keyword/vector/graph/hybrid) — delegated to W7/W8 internals
- Index build latency (included in ingestion path via pipeline)

## Representative Results (CI Environment)

*Structural verification only — not SLA commitments.*

| Operation | Typical Range |
|-----------|---------------|
| Single-doc ingest | < 500 ms |
| Multi-doc (2 docs) ingest | < 1 s |
| Cold query | < 200 ms |
| Warm query | < 100 ms |
| Storage footprint (2-doc fixture) | < 100 KB |

## Verdict

```text
PERFORMANCE: CHARACTERIZED at verified scale
NOT CHARACTERIZED at production corpus scale
```

See `knowledge_step7_benchmark_matrix.md` for operation coverage matrix.
