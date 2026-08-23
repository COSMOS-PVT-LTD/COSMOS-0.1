# KG-BLOCK-004 ENGINEERING REVIEW & HARDENING REPORT

**Document ID:** COSMOS-KG-REV-B004  
**Date:** 2026-08-23  
**Block:** KG-BLOCK-004  
**Scope:** KG-017 → KG-021  
**Review Type:** Engineering Review + Verification + Targeted Hardening

---

## 1. Executive Status

```text
BLOCK:   KG-BLOCK-004
STATUS:  PASS WITH MINOR HARDENING
BATCHES: KG-017, KG-018, KG-019, KG-020, KG-021
PASS:    5 / 5
FAIL:    0
BLOCKED: 0
```

---

## 2. Review Coverage

| Batch | Package | Review Focus | Result |
|-------|---------|--------------|--------|
| **KG-017** | `knowledge/indexing/` | Determinism, stale detection, duplicate handling, derivative-state principle | PASS WITH HARDENING |
| **KG-018** | `knowledge/search/contracts.py` | Backend neutrality, bounded queries, explicit empty-result contracts | PASS |
| **KG-019** | `knowledge/search/engine.py` | Lexical/semantic/structured/hybrid retrieval, tie-breaking, false-positive risk | PASS WITH HARDENING |
| **KG-020** | `knowledge/reasoning/evidence.py`, `reasoner.py` | Evidence-bounded reasoning, lifecycle separation, conflict exposure | PASS WITH HARDENING |
| **KG-021** | `knowledge/reasoning/context.py` | AI boundary, bounded context, provenance retention, no-verified-result handling | PASS WITH HARDENING |

**Authoritative references reviewed:**

- `COSMOS_0.1_KG_BLOCK_004_MASTER_CURSOR_PROMPT.md`
- `documentation/development/kg_block_004_handoff_report.md`
- `documentation/development/batch_status.json` (KG-BLOCK-003 freeze record)
- All BLOCK-004 production and test files

**Frozen interfaces inspected (read-only):** KG-BLOCK-001/002/003 graph, extraction, ontology modules — no modifications required.

---

## 3. Findings

### CRITICAL — 0

None.

### HIGH — 0 (resolved by hardening)

| ID | File | Observation | Engineering Impact | Action | Verification |
|----|------|-------------|-------------------|--------|--------------|
| H-001 (resolved) | `knowledge/search/engine.py` | `_structured_results` returned **all** graph nodes with score 0.5 when query text did not match node_id | False-positive retrieval — unrelated nodes presented as search results | Rewrote structured retrieval to require property term overlap; exclude non-matching nodes | `test_structured_search_does_not_return_irrelevant_nodes` |
| H-002 (resolved) | `knowledge/search/engine.py` | Search engine did not compare live graph digest against bundle digest at query time | Stale indexes could be served after graph mutation without rebuild | Added live digest check raising `IndexStaleError` in `search()` | `test_search_rejects_stale_indexes_after_graph_mutation` |
| H-003 (resolved) | `knowledge/reasoning/evidence.py` | `has_verified_results=True` set for any non-empty retrieval, including candidate-only evidence | Overclaimed verification status — collapsed CANDIDATE into VERIFIED | `has_verified_results` now True only for `APPROVED` lifecycle; added `has_retrieval_results` property | Updated reasoning tests + `test_approved_evidence_is_classified_as_verified` |

### MEDIUM — 0 (resolved by hardening)

| ID | File | Observation | Engineering Impact | Action | Verification |
|----|------|-------------|-------------------|--------|--------------|
| M-001 (resolved) | `knowledge/indexing/lexical.py`, `semantic.py` | Duplicate `entry_id` values silently overwrote prior entries in `_entries_by_id` | Non-deterministic/conflicting index state without explicit failure | Raise `IndexValidationError` on duplicate entry_id | `test_lexical_index_rejects_duplicate_entry_ids` |
| M-002 (resolved) | `knowledge/search/engine.py`, `reasoning/evidence.py` | Broad `except Exception` in hybrid retrieval and evidence assembly | Engineering failures could be masked or misclassified | Narrowed to `GraphQueryError` with `RetrievalError`/`RankingError` chaining | Existing + hardening tests pass |
| M-003 (resolved) | `knowledge/reasoning/context.py` | Empty-evidence sentinel validation keyed on `has_verified_results` instead of retrieval emptiness | Candidate evidence could trigger incorrect `ContextAssemblyError` after H-003 fix | Validate sentinel only when `not evidence.has_retrieval_results` | Reasoning tests updated |

### LOW — 1 (accepted)

| ID | File | Observation | Engineering Impact | Action |
|----|------|-------------|-------------------|--------|
| L-001 | `knowledge/search/engine.py` | Structured retrieval uses term-overlap on node properties (not full field-schema matching) | Sufficient for BLOCK-004 contracts; richer structured queries deferred to KG-022+ | **ACCEPT** — document as deferred |

### INFORMATIONAL — 4

| ID | Observation | Action |
|----|-------------|--------|
| I-001 | Semantic index uses deterministic term-overlap scoring (documented abstraction, not embeddings) | No change — compliant with block constraints |
| I-002 | `ProvenanceAwareReasoner` conflict detection relies on `conflict_visibility=CONFIRMED_CONFLICT` graph property | Test added; cross-source value conflict resolution policy deferred to KG-022+ |
| I-003 | Per-batch spec files KG-017–021 not found in repository | Implementation validated against master prompt + batch matrix |
| I-004 | `EngineeringContextAssembler` enforces max 1000 evidence items per package | Hardening added — bounded context assembly |

---

## 4. Hardening Summary

| FILE | CHANGE | RATIONALE | TEST | RESULT |
|------|--------|-----------|------|--------|
| `knowledge/indexing/lexical.py` | Reject duplicate `entry_id` at construction | Prevent silent index corruption | `test_lexical_index_rejects_duplicate_entry_ids` | PASS |
| `knowledge/indexing/semantic.py` | Reject duplicate `entry_id` at construction | Same as lexical | Covered by lexical pattern | PASS |
| `knowledge/search/engine.py` | Live graph digest staleness check in `search()` | Prevent serving stale indexes after mutation | `test_search_rejects_stale_indexes_after_graph_mutation` | PASS |
| `knowledge/search/engine.py` | Rewrite `_structured_results` to require property term match | Eliminate false-positive node returns | `test_structured_search_does_not_return_irrelevant_nodes` | PASS |
| `knowledge/search/engine.py` | Narrow `except Exception` → `GraphQueryError` in hybrid path | Do not mask unexpected failures | Regression suite | PASS |
| `knowledge/reasoning/evidence.py` | Fix `has_verified_results` semantics; add `has_retrieval_results` | Distinguish retrieval from verification | Reasoning + hardening tests | PASS |
| `knowledge/reasoning/evidence.py` | Narrow exception handling to `GraphQueryError` | Preserve failure taxonomy | Regression suite | PASS |
| `knowledge/reasoning/reasoner.py` | Empty-evidence check uses `evidence.items` not `has_verified_results` | Correct NO_VERIFIED_RESULT for empty retrieval only | Reasoning tests | PASS |
| `knowledge/reasoning/context.py` | Sentinel validation on `has_retrieval_results`; max evidence bound (1000) | Correct AI boundary + boundedness | Reasoning tests | PASS |
| `tests/unit_tests/knowledge/reasoning/test_reasoning.py` | Updated assertions for verified vs retrieval semantics | Align tests with corrected contracts | All pass | PASS |
| `tests/unit_tests/knowledge/test_block004_hardening.py` | **NEW** — 8 hardening tests | Close review gaps | All pass | PASS |

**Frozen modules modified:** 0

---

## 5. Test Summary

```text
Baseline (pre-review):     953 passed, 5 skipped
Targeted (BLOCK-004):      21 passed
Knowledge suite (BLOCK-004): 21 passed
Full regression (final):   961 passed, 5 skipped
New tests added:           8
Skipped:                   5 (unchanged)
Failures:                  0
Regressions:               0
Delta:                     +8 tests
```

### New hardening tests

```text
test_lexical_index_rejects_duplicate_entry_ids
test_index_build_is_independent_of_construction_batch_order
test_empty_graph_produces_empty_index
test_search_rejects_stale_indexes_after_graph_mutation
test_structured_search_does_not_return_irrelevant_nodes
test_hybrid_search_tie_breaks_by_target_id
test_reasoner_preserves_conflicting_evidence
test_approved_evidence_is_classified_as_verified
```

### Requirement traceability (selected)

| Requirement / Invariant | Implementation | Test | Result |
|-------------------------|----------------|------|--------|
| Graph = source of truth | Index built from `store.snapshot()` + digest | `test_stale_bundle_detection` | PASS |
| Stale index detection | `is_stale()`, bundle check, engine live digest | `test_search_rejects_stale_indexes_after_graph_mutation` | PASS |
| No false structured matches | Property term overlap required | `test_structured_search_does_not_return_irrelevant_nodes` | PASS |
| Candidate ≠ verified | `has_verified_results` lifecycle-gated | `test_approved_evidence_is_classified_as_verified` | PASS |
| Conflict preservation | `conflict_target_ids` populated | `test_reasoner_preserves_conflicting_evidence` | PASS |
| Deterministic hybrid ranking | Score DESC → target_id ASC | `test_hybrid_search_tie_breaks_by_target_id` | PASS |
| NO_VERIFIED_RESULT sentinel | Empty retrieval + candidate-only context | `test_empty_evidence_reports_no_verified_result` | PASS |

---

## 6. Static Analysis

```text
Ruff (BLOCK-004 scope):  PASS
Mypy (indexing/search/reasoning): PASS (15 source files)
Import smoke:            PASS
```

Pre-existing repository-wide ruff issues outside BLOCK-004 scope remain unchanged (per KG-BLOCK-003 finding I-002).

---

## 7. Architectural Verification

| Check | Result |
|-------|--------|
| Graph remains source of truth | **PASS** |
| Index remains derivative | **PASS** |
| Search is deterministic | **PASS** |
| Reasoning is evidence-bounded | **PASS** |
| Context is bounded | **PASS** |
| Provenance preserved | **PASS** |
| No unauthorized AI | **PASS** |
| No external network | **PASS** |
| No graph DB | **PASS** |
| No domain duplication | **PASS** |
| Frozen interfaces preserved | **PASS** |

---

## 8. Review Checklist

- [x] Architecture alignment
- [x] Dependency integrity
- [x] Frozen interface protection
- [x] Index determinism
- [x] Index freshness
- [x] Search determinism
- [x] Search ranking correctness
- [x] Empty-result correctness
- [x] Provenance preservation
- [x] Evidence integrity
- [x] Conflict handling
- [x] Lifecycle enforcement
- [x] Candidate/verified separation
- [x] Reasoning boundedness
- [x] Context boundedness
- [x] API audit
- [x] Exception audit
- [x] Security/IP audit
- [x] Side-effect audit
- [x] Numerical integrity (no silent quantity mutation in BLOCK-004 layers)
- [x] Duplicate handling
- [x] Negative-path testing
- [x] Regression testing
- [x] Ruff
- [x] Mypy
- [x] Import smoke testing
- [x] Documentation reconciliation

---

## 9. API Audit (Public Exports)

| Symbol | Classification |
|--------|----------------|
| `KnowledgeIndexBuilder`, `KnowledgeIndexBundle` | PUBLIC — REQUIRED |
| `LexicalIndex`, `SemanticIndex`, `InMemory*` | PUBLIC — REQUIRED |
| `tokenize_text`, `build_*_index_from_store` | PUBLIC — JUSTIFIED |
| `EvidenceBundle.has_retrieval_results` | PUBLIC — REQUIRED (new property) |
| `KnowledgeSearchEngine` | PUBLIC — REQUIRED |
| `SearchQuery`, `SearchResult`, `SearchResultPage` | PUBLIC — REQUIRED |
| `ProvenanceAwareReasoner`, `EvidenceRanker` | PUBLIC — REQUIRED |
| `EngineeringContextAssembler` | PUBLIC — REQUIRED |
| Internal builder helpers | INTERNAL — not exported |

No premature APIs removed.

---

## 10. Deferred Work (KG-022+)

```text
- Embedding-based semantic retrieval backends
- Persistent index storage
- Richer structured field-schema retrieval
- Cross-source value conflict resolution policy (beyond CONFIRMED_CONFLICT flag)
- Full ingestion → search integration pipeline tests
- Human freeze authorization for KG-BLOCK-004
```

---

## 11. Self-Review A–J

| Review | Result | Evidence |
|--------|--------|----------|
| A — Dependency | PASS | Imports only from authorized frozen graph/extraction/ontology |
| B — API | PASS | Backend-neutral contracts; hardening preserved public surface |
| C — Data integrity | PASS | Validation errors on invalid queries, duplicates, stale indexes |
| D — Provenance | PASS | Evidence assembly retains document_id, lifecycle, conflict flags |
| E — Determinism | PASS | Batch-order, tie-break, repeated-query tests |
| F — Boundary | PASS | No KG-022+ code; frozen files untouched |
| G — Security | PASS | No network/API/filesystem side effects on import |
| H — Domain integrity | PASS | No duplicate engineering models |
| I — Test adequacy | PASS | 21 behavioral tests; 8 added for discovered gaps |
| J — Regression | PASS | 961 passed, 0 failed |

---

## 12. Final Engineering Recommendation

```text
OPTION B — PASS WITH MINOR HARDENING
```

Three high-severity retrieval/verification issues were identified and corrected with minimal, targeted changes. No frozen interfaces were modified. Full regression is green.

---

## 13. Freeze Gate

```text
KG-BLOCK-004 = READY FOR HUMAN FREEZE APPROVAL
```

The block is **not** marked FROZEN. Human engineering review and explicit freeze authorization are required before proceeding to KG-022+.

---

**Review completed by:** Cursor Coding Agent (COSMOS-KG-REV-B004)  
**Artifacts:** `documentation/development/kg_block_004_engineering_review.md`, `tests/unit_tests/knowledge/test_block004_hardening.py`
