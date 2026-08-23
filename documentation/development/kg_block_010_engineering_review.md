# KG-BLOCK-010 Engineering Review

**Document ID:** COSMOS-KG-REV-B010  
**Date:** 2026-08-23  
**Block:** KG-BLOCK-010  
**Scope:** KG-033 → KG-039 (W7 Indexing + W8 Search)  
**Review Type:** Engineering Review + Verification + Targeted Hardening

---

## STATUS

```text
PASS WITH MINOR HARDENING
READY FOR HUMAN FREEZE APPROVAL
```

## RECOMMENDATION

```text
KG-BLOCK-010 is architecturally compliant, deterministic, provenance-preserving,
stale-index safe, and contract-safe after targeted hardening. Recommend human freeze approval.
KG-BLOCK-011 remains NOT AUTHORIZED.
```

---

## 1. Executive Summary

Formal engineering review of KG-BLOCK-010 (W7 Indexing + W8 Search) was executed against
the KG-001→KG-051 architecture baseline, master implementation prompt, reconnaissance/handoff
documentation, and frozen BLOCK-001→009 interfaces.

Three medium-severity defects were identified and corrected:
negative hybrid weight acceptance, non-positive vector similarity pollution, and missing
live-graph staleness checks on standalone W8 search engines. Eighteen targeted hardening
regression tests were added. No critical or high findings remain open. Frozen upstream
contracts were verified unchanged.

```text
BLOCK:      KG-BLOCK-010
STATUS:     PASS WITH MINOR HARDENING
BATCHES:    KG-033, KG-034, KG-035, KG-036, KG-037, KG-038, KG-039
BASELINE:   1121 passed, 5 skipped
FINAL:      1139 passed, 5 skipped
REGRESSION: +18 tests, 0 regressions
```

---

## 2. Baseline

Independently verified before review:

| Suite | Baseline (implementation) | Final (after review) | Delta |
|-------|---------------------------|----------------------|-------|
| W7 targeted tests | 16 passed | 16 passed | 0 |
| W8 targeted tests | 13 passed | 13 passed | 0 |
| Hardening tests | 0 | 18 passed | +18 |
| W7+W8+hardening | 29 passed | 47 passed | +18 |
| Knowledge suite | 735 passed, 5 skipped | 753 passed, 5 skipped | +18 |
| Full regression | 1121 passed, 5 skipped | 1139 passed, 5 skipped | +18 |
| Ruff (W7/W8 scope) | — | PASS | — |
| Mypy (W7/W8 scope) | — | PASS (10 files) | — |
| Import smoke | — | PASS | — |

---

## 3. Review Scope

| Batch | Module(s) | Review Focus | Result |
|-------|-----------|--------------|--------|
| **KG-033** | Frozen lexical + `w7/bundle.py` | Composition, determinism, non-authoritative | PASS |
| **KG-034** | `w7/vector.py` | Caller vectors, cosine, dimension validation | PASS WITH HARDENING |
| **KG-035** | `w7/graph_index.py` | Adjacency, digest, dangling rejection | PASS |
| **KG-036** | `w8/keyword.py` | Deterministic keyword retrieval | PASS WITH HARDENING |
| **KG-037** | `w8/semantic.py` | Explicit query vectors, similarity ranking | PASS WITH HARDENING |
| **KG-038** | `w8/graph_search.py` | Bounded traversal, cycle termination | PASS WITH HARDENING |
| **KG-039** | `w8/hybrid.py` | Fusion, renormalization, component exclusion | PASS WITH HARDENING |
| **Cross** | `w8/validation_aware.py` | W9 read-only filtering | PASS |

---

## 4. Focus-Area Results A–Q

| # | Focus Area | Verdict | Evidence |
|---|------------|---------|----------|
| A | Dependency integrity | PASS | W7/W8 depend only on frozen graph/indexing/search/validation |
| B | KG-033 lexical index | PASS | Composed via `W7IndexBuilder`; frozen lexical unchanged |
| C | KG-034 vector index | PASS WITH HARDENING | Non-positive similarity filtered; dimension/NaN validation |
| D | KG-035 graph index | PASS | Deterministic adjacency; dangling endpoint rejection |
| E | KG-036 keyword search | PASS WITH HARDENING | Live-graph stale rejection when store bound |
| F | KG-037 semantic search | PASS WITH HARDENING | Explicit vectors; stale rejection; zero-score filter |
| G | KG-038 graph search | PASS | Bounded traversal; cycle tests; provenance preserved |
| H | KG-039 hybrid search | PASS WITH HARDENING | Negative weight rejection; component renormalization |
| I | Validation-aware search | PASS | Read-only W9 consumption; no promotion |
| J | Stale index safety | PASS WITH HARDENING | All W8 engines reject stale graph when store provided |
| K | Determinism | PASS | Stable digests, tie-breaking, repeated execution |
| L | Provenance integrity | PASS | document_id/lifecycle preserved through pipeline |
| M | Exception taxonomy | PASS | No `except Exception`; domain exceptions used |
| N | API stability | PASS | Frozen BLOCK-001→009 files unchanged; additive `store` param |
| O | Domain model integrity | PASS | No duplicate Quantity/Unit/Dimension models |
| P | Security/IP boundary | PASS | No network, exec, embeddings, or external APIs |
| Q | Performance/boundedness | PASS WITH FINDING | Graph search O(n·depth); acceptable for reference |

---

## 5. Findings by Severity

### CRITICAL — 0

None.

### HIGH — 0

None.

### MEDIUM — 0 (resolved by hardening)

| ID | File | Observation | Fix | Test |
|----|------|-------------|-----|------|
| M-001 | `hybrid.py` | `HybridComponentWeights` accepted negative weights | Reject negative individual weights | `test_hybrid_weights_reject_negative_components` |
| M-002 | `vector.py` | Vector similarity returned zero/negative matches | Filter `score > 0.0` before ranking | `test_vector_similarity_filters_non_positive_scores` |
| M-003 | `w8/*.py` | Standalone search engines could serve stale graph results | Optional `store` param with live digest check | `test_keyword_search_rejects_stale_graph_with_store_binding` |

### LOW — 2 (accepted)

| ID | Observation |
|----|-------------|
| L-001 | Vector index uses deterministic reference vectors, not production embeddings |
| L-002 | Graph search performs per-node bounded traversal (reference heuristic) |

### INFORMATIONAL — 2

| ID | Observation |
|----|-------------|
| I-001 | Frozen `KnowledgeSearchEngine` remains available alongside W8 engines |
| I-002 | W8 engines without `store` binding rely on caller-provided digest freshness |

---

## 6. Hardening Applied

| File | Defect | Root Cause | Fix | Regression Test |
|------|--------|------------|-----|-----------------|
| `search/w8/hybrid.py` | M-001 | Only total weight sum validated | Per-component non-negative validation | `test_hybrid_weights_reject_negative_components` |
| `indexing/w7/vector.py` | M-002 | All cosine scores returned including ≤0 | Filter non-positive scores | `test_vector_similarity_filters_non_positive_scores` |
| `search/w8/keyword.py` | M-003 | No live graph digest verification | Optional `store` + `IndexStaleError` | `test_keyword_search_rejects_stale_graph_with_store_binding` |
| `search/w8/semantic.py` | M-003 | Same stale gap | Optional `store` binding | `test_semantic_search_rejects_dimension_mismatch` (related) |
| `search/w8/graph_search.py` | M-003 | Same stale gap | Optional `store` binding | Graph cycle/stale tests |
| `search/w8/hybrid.py` | M-003 | Sub-engines lacked store binding | Pass `store` to sub-engines | Existing hybrid stale test |

---

## 7. Files Modified

```text
knowledge/indexing/w7/vector.py
knowledge/search/w8/hybrid.py
knowledge/search/w8/keyword.py
knowledge/search/w8/semantic.py
knowledge/search/w8/graph_search.py
tests/unit_tests/knowledge/test_block010_hardening.py (new)
documentation/development/kg_block_010_engineering_review.md (new)
documentation/development/batch_status.json
documentation/development/kg_block_freeze_ledger.md
```

---

## 8. Tests Added

```text
tests/unit_tests/knowledge/test_block010_hardening.py — 18 tests
```

Mandatory negative test coverage includes: duplicate IDs, dimension mismatch, zero vectors,
invalid numerics, stale graph rejection, cycle termination, hybrid weight edge cases,
component-only modes, validation-aware filtering, determinism, provenance, import smoke.

---

## 9. Verification

```text
Targeted W7/W8+hardening:  47 passed
Knowledge suite:           753 passed, 5 skipped
Full regression:           1139 passed, 5 skipped
Ruff (W7/W8 scope):        PASS
Mypy (W7/W8 scope):        PASS
Import smoke:              PASS
```

---

## 10. Frozen-Interface Verification

```text
KG-BLOCK-001: UNCHANGED
KG-BLOCK-002: UNCHANGED
KG-BLOCK-003: UNCHANGED
KG-BLOCK-004: UNCHANGED
KG-BLOCK-005: UNCHANGED
KG-BLOCK-006: UNCHANGED
KG-BLOCK-007: UNCHANGED
KG-BLOCK-008: UNCHANGED
KG-BLOCK-009: UNCHANGED
```

Verified via `git diff` on frozen paths — empty.

---

## 11. Security/IP Verification

- No network calls, external APIs, LLM calls, or embeddings
- No `eval`/`exec` or arbitrary deserialization
- No filesystem crawling or telemetry
- Engineering content treated as inert data throughout indexing/search

---

## 12. Determinism Verification

- Identical rebuilds produce identical `source_digest`
- Vector similarity tie-breaking by `record_id`
- Hybrid fusion tie-breaking by `target_id`
- Repeated search execution produces identical `SearchResultPage` mappings

---

## 13. Stale-Index Verification

Sequence verified:

```text
Graph → Build index → Search succeeds → Mutate graph → Search rejects (IndexStaleError)
```

Equivalent rebuilds produce identical digests. No silent stale serving when `store` is bound.

---

## 14. Deferred Work

- Production embedding backend behind `VectorIndex` protocol
- Persistent index storage
- Richer field-schema structured search
- Optional default `store` binding policy documentation for all W8 callers

---

## 15. Final Recommendation

```text
KG-BLOCK-010 ENGINEERING REVIEW COMPLETE

STATUS:
PASS WITH MINOR HARDENING

RECOMMENDATION:
READY FOR HUMAN FREEZE APPROVAL
```

**Do NOT freeze KG-BLOCK-010 without explicit human authorization.**
