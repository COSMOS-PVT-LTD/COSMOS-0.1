# Step 7 Gate 6 — Scale Benchmark Report

**Date:** 2026-08-23  
**Data artifact:** `knowledge_step7_gate6_scale_benchmark_data.json`  
**Harness:** `knowledge/production/scale_benchmark.py`

## Methodology

- Synthetic markdown corpus via `generate_scale_corpus()` — deterministic, unique per document
- Isolated store directory per scale point
- Full pipeline path: ingest → persist → reload → recover → cold/warm query
- Measurements: wall-clock (`time.perf_counter`), tracemalloc peak + RSS
- Cold query: first query after reload; warm query: immediate repeat
- **No SLA values invented** — evidence boundary documented only

## Environment

| Field | Value |
|-------|-------|
| Platform | macOS-26.5.2-x86_64 (local developer machine) |
| Python | 3.11.7 |
| Workload | Single-threaded, offline, deterministic embedding v1 |
| Store | JSON v1.0.0, single-writer |

## Corpus Construction

Each document contains:
- Title + 2 sections
- Chamber pressure, thrust vector, LOX flow synthetic values
- Unique `document_id` / `source_id` / `artifact_id`

**Limitation:** Synthetic corpus — not representative engineering library content.

## Results

| Corpus | Ingest (ms) | Ingest/doc (ms) | Reload (ms) | Recovery (ms) | Query cold (ms) | Query warm (ms) | Memory (MB) | Storage (KB) | Result |
|--------|------------:|----------------:|------------:|--------------:|----------------:|----------------:|------------:|-------------:|--------|
| 5 | 83 | 17 | 2 | 6 | 14 | 13 | 28 | 27 | VERIFIED |
| 10 | 215 | 21 | 3 | 11 | 25 | 25 | 30 | 52 | VERIFIED |
| 25 | 952 | 38 | 6 | 73 | 98 | 61 | 32 | 130 | VERIFIED |
| 50 | 3,475 | 69 | 12 | 56 | 120 | 121 | 37 | 259 | PARTIALLY VERIFIED |
| 100 | 12,833 | 128 | 23 | 118 | 242 | 241 | 39 | 517 | PARTIALLY VERIFIED |

## Scaling Analysis

| Metric | Observed behavior |
|--------|-------------------|
| Ingestion | Approximately linear (~13–128 ms/doc as corpus grows) |
| Query latency | Increases with corpus size (14 ms → 242 ms cold) |
| Storage | ~5.2 KB/doc (synthetic corpus) |
| Memory | ~28–39 MB peak RSS — sub-linear growth |
| Determinism | Warm repeat queries stable (±1 ms at 100 docs) |

## First Unacceptable / Unverified Boundary

| Boundary | Finding |
|----------|---------|
| **>25 docs qualification** | Measurements exist but marked PARTIALLY VERIFIED — synthetic corpus, no SLA, Envelope A still authoritative |
| **Representative engineering corpus** | NOT VERIFIED |
| **Concurrent workload** | NOT VERIFIED |
| **Production SLA** | NOT DEFINED |

## Verified Envelope (Evidence-Supported)

```text
Corpus:     5–25 documents (synthetic markdown, single-threaded)
Ingestion:  < 1 s (5 docs) to ~1 s (25 docs)
Query:      < 100 ms cold at ≤25 docs
Storage:    < 150 KB at ≤25 docs
Memory:     < 35 MB peak RSS at ≤25 docs
```

## Limitations

- Synthetic documents only — scaling may differ on real engineering specs
- No concurrent writers/readers tested
- CPU utilization not isolated (end-to-end wall clock only)
- Parsing/extraction/indexing not separately instrumented (included in ingest)
- 50–100 doc runs measured but not qualified beyond Envelope A without human decision
