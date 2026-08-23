# Step 7 — Scale and Concurrency Report

**Document ID:** `COSMOS-STEP7-SCALE-CONCURRENCY-001`  
**Date:** 2026-08-23  
**Scale data:** `knowledge_step7_final_scale_benchmark_data.json`  
**Concurrency data:** `knowledge_step7_final_concurrency_benchmark_data.json`

---

## 1. Scale Measurements (synthetic corpus)

| Docs | Ingest (total) | Ingest/doc | Query cold | Recovery | Peak memory | Storage | Classification |
|------|----------------|------------|------------|----------|-------------|---------|----------------|
| 5 | 85 ms | 17 ms | 14 ms | 6 ms | 31 MB | 27 KB | **VERIFIED** |
| 25 | 1,087 ms | 43 ms | 62 ms | 27 ms | 34 MB | 130 KB | **VERIFIED** |
| 50 | 3,783 ms | 76 ms | 121 ms | 57 ms | 36 MB | 260 KB | **PARTIALLY VERIFIED** |
| 100 | 14,474 ms | 145 ms | 241 ms | 117 ms | 41 MB | 519 KB | **PARTIALLY VERIFIED** |
| 250 | 88,408 ms | 354 ms | 628 ms | 329 ms | 64 MB | 1.3 MB | **CHARACTERIZED** |
| 500 | 369,688 ms | 739 ms | 1,348 ms | 745 ms | 90 MB | 2.5 MB | **CHARACTERIZED** |

Persistence reload at 500 docs: 113 ms.

---

## 2. Concurrency (25-doc corpus, 16 queries per level)

| Concurrency | Mean query ms | P95 query ms | Total ms | Classification |
|-------------|---------------|--------------|----------|----------------|
| 1 | 8.6 | 8.7 | 156 | **VERIFIED** |
| 2 | 16.1 | 17.3 | 154 | **VERIFIED** |
| 4 | 30.0 | 36.6 | 163 | **VERIFIED** |
| 8 | 53.5 | 71.8 | 159 | **CHARACTERIZED** |

Note: single-writer JSON persistence; concurrent queries are read-heavy characterization only.

---

## 3. Limits Observed

| Limit | Evidence |
|-------|----------|
| Practical verified corpus | ≤25 docs (full ingest + query + recovery) |
| Partially verified | 50–100 docs |
| Characterized only | 250–500 docs ingest; 8-way concurrency |
| Memory at 500 docs | ~90 MB peak RSS (macOS measurement) |

---

## 4. Qualification Boundary

Scale/concurrency results **do not** extend Envelope A qualification without human Gate-6 sign-off.
