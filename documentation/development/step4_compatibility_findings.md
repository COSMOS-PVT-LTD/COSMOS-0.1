# Step 4 — Compatibility Findings Register

**Document ID:** `COSMOS-STEP4-FINDINGS-001`  
**Phase:** Step 4 — Compatibility Audit & Hardening  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`  
**Date:** 2026-08-23

---

## Classification Legend

| Code | Meaning | Allowed Action |
|---|---|---|
| C0 | Contract satisfied | None |
| C1 | Documentation gap | Docs only |
| C2 | Test gap | Add tests |
| C3 | Genuine compatibility failure | Code fix |
| C4 | Intentional architecture evolution | Document |
| C5 | Out of scope | Do not implement |

---

## C0 — PASS (Representative)

| ID | COMPAT | Finding | Disposition |
|---|---|---|---|
| S4-C0-001 | 001 | `load_pdf` delegates to `PdfIngestionAdapter` without fabricated text | PASS |
| S4-C0-002 | 001 | All four loaders return `IngestionResult` with `NORMALIZED` stage | PASS |
| S4-C0-003 | 002 | `KeywordSearch.search` delegates to `KeywordSearchEngine` | PASS |
| S4-C0-004 | 002 | `HybridSearch.search` does not inject spurious `query_vector` | PASS |
| S4-C0-005 | 002 | `SearchEngine` subclasses `KnowledgeSearchEngine` | PASS |
| S4-C0-006 | 003 | `KeywordIndex is InMemoryLexicalIndex` (identity alias) | PASS |
| S4-C0-007 | 003 | `build_*_from_store` delegates to canonical builders | PASS |
| S4-C0-008 | 004 | `GraphManager.construct` updates internal store and query service | PASS |
| S4-C0-009 | 004 | `GraphManager.traverse` delegates to `GraphQueryService` | PASS |
| S4-C0-010 | 005 | `OntologyManager.list_terms()` maps to registry | PASS |
| S4-C0-011 | 005 | `OntologyManager.registry` exposes backing registry | PASS |
| S4-C0-012 | 006 | Pipeline output matches BLOCK-012 integration digests | PASS |
| S4-C0-013 | 006 | `provider_invoked=False` preserved | PASS |
| S4-C0-014 | ALL | No reverse import from canonical into `knowledge.compat` | PASS |
| S4-C0-015 | ALL | No second source of truth created | PASS |

---

## C1 — Documentation Gaps

| ID | COMPAT | Finding | Action | Status |
|---|---|---|---|---|
| S4-C1-001 | 006 | `run_knowledge_pipeline` uses `validate_context` (W9 baseline), not Phase-C `validate_context_extended` | Documented in contract matrix §COMPAT-006 | **CLOSED** |

**Rationale:** Phase-C extended validation is an additive surface. The compatibility pipeline intentionally mirrors the BLOCK-012 qualification helper. Not a defect.

---

## C2 — Test Gaps (Hardened)

| ID | COMPAT | Gap | Test Added | Status |
|---|---|---|---|---|
| S4-C2-001 | ALL | Import smoke for all public legacy symbols | `test_all_compat_surfaces_importable` | **CLOSED** |
| S4-C2-002 | 001 | Deterministic path-derived source/artifact IDs | `test_load_markdown_deterministic_source_ids` | **CLOSED** |
| S4-C2-003 | 001 | Directory path rejection | `test_load_markdown_rejects_directory` | **CLOSED** |
| S4-C2-004 | 002 | Stale index rejection via facade | `test_keyword_search_facade_rejects_stale_index` | **CLOSED** |
| S4-C2-005 | 002 | Wrong vector dimension error propagation | `test_semantic_search_facade_rejects_wrong_vector_dimension` | **CLOSED** |
| S4-C2-006 | 002 | Hybrid search determinism | `test_hybrid_search_facade_is_deterministic` | **CLOSED** |
| S4-C2-007 | 002 | Lifecycle filter honored (no promotion) | `test_keyword_search_facade_respects_lifecycle_filter` | **CLOSED** |
| S4-C2-008 | 003 | Deterministic index rebuild | `test_build_keyword_index_from_store_is_deterministic` | **CLOSED** |
| S4-C2-009 | 004 | `store` property guard before construct | `test_graph_manager_store_requires_construct` | **CLOSED** |
| S4-C2-010 | 005 | Duplicate term registration error | `test_ontology_manager_rejects_duplicate_term_registration` | **CLOSED** |
| S4-C2-011 | 006 | No lifecycle promotion in pipeline | `test_pipeline_does_not_promote_lifecycle_state` | **CLOSED** |
| S4-C2-012 | 006 | Provider boundary preserved | `test_pipeline_preserves_provider_invoked_false` | **CLOSED** |

---

## C3 — Genuine Compatibility Failures

```text
NONE
```

No C3 findings. No implementation changes made.

---

## C4 — Architecture Discrepancies (Intentional)

| ID | COMPAT | Discrepancy | ADR / Record | Action |
|---|---|---|---|---|
| S4-C4-001 | 002 | `SemanticSearch.search` requires explicit `query_vector` (legacy may have implied auto-embedding) | W8 canonical contract; no production embeddings | Document only |
| S4-C4-002 | 001 | Loader facades import `knowledge.compat.ingestion_loaders` | Phase-B approved shared helper within frozen facade layer | Document only |

---

## C5 — Out of Scope (Not Pursued)

| Topic | Reason |
|---|---|
| Persistence layer | C5 — not Step 4 |
| Production embeddings | C5 — not Step 4 |
| KG-BLOCK-014+ | C5 — not authorized |
| Static domain ontology modules | C5 — superseded by ADR-008 |
| File-level 100% architecture match | C5 — known deviation, not compatibility failure |

---

## Summary

| Classification | Count |
|---|---|
| C0 | 15+ (representative sample above) |
| C1 | 1 (closed) |
| C2 | 12 (closed) |
| C3 | **0** |
| C4 | 2 (documented) |
| C5 | 5 (deferred) |
