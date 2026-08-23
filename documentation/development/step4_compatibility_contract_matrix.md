# Step 4 — Compatibility Contract Matrix

**Document ID:** `COSMOS-STEP4-CONTRACT-MATRIX-001`  
**Phase:** Step 4 — Compatibility Audit & Hardening  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`  
**Audit Date:** 2026-08-23

---

## Summary

| COMPAT | Legacy Surface | Facade | Canonical | Audit | Classification | Action |
|---|---|---|---|---|---|---|
| 001 | `knowledge/ingestion/*_loader.py` | Phase-B loaders + `ingest_file_from_path` | `knowledge/ingestion_adapters/*` | PASS | C0 / C2 | Tests hardened |
| 002 | `knowledge/search/*_search.py` | `KeywordSearch`, `SemanticSearch`, `HybridSearch`, `GraphSearch`, `SearchEngine` | W8 engines + `KnowledgeSearchEngine` | PASS | C0 / C2 | Tests hardened |
| 003 | `knowledge/indexing/*_index.py` | Type aliases + `build_*_from_store` | W7 / lexical / semantic builders | PASS | C0 / C2 | Tests hardened |
| 004 | `knowledge/graph/graph_manager.py` | `GraphManager` | `GraphConstructor` + `GraphQueryService` | PASS | C0 / C2 | Tests hardened |
| 005 | `knowledge/ontology/ontology_manager.py` | `OntologyManager` | `OntologyRegistry` | PASS | C0 / C2 | Tests hardened |
| 006 | `knowledge/pipelines/knowledge_pipeline.py` | `run_knowledge_pipeline` | `knowledge/pipelines/orchestrator.py` | PASS | C0 / C1 / C2 | Docs + tests |

---

## COMPAT-001 — Ingestion

| Field | Value |
|---|---|
| **Legacy surface** | `load_pdf`, `load_docx`, `load_html`, `load_markdown` |
| **Current facade** | `knowledge/ingestion/{pdf,docx,html,markdown}_loader.py` |
| **Shared helper** | `knowledge/compat/ingestion_loaders.ingest_file_from_path` |
| **Canonical implementation** | `knowledge/ingestion_adapters/{pdf,docx,html,markdown}` via `IngestionAdapter.ingest` |
| **Public symbols** | `load_pdf`, `load_docx`, `load_html`, `load_markdown` |
| **Inputs** | Local file path (`str` \| `Path`); optional `vault`, `source_id`, `artifact_id` |
| **Outputs** | `IngestionResult` with `NORMALIZED` stage, content hash, artifact ref |
| **Exceptions** | `FileNotFoundError` for missing/non-file paths; adapter errors propagate |
| **Provenance** | Vault artifact stored with `content_hash`; request carries `IngestionArtifactRef` |
| **Lifecycle** | No lifecycle promotion; ingestion only |
| **Determinism** | Path-derived default `SRC-*` / `ART-*` IDs via SHA-256 of resolved path |
| **Units/quantities** | N/A at ingestion boundary |
| **Security/IP** | Local file read only; no network; no fabricated extraction text |
| **Existing tests** | `test_compat_ingestion.py` (5) |
| **Step 4 tests** | `test_compat_adversarial.py` (+3) |
| **Audit result** | Delegation verified; no duplicate ingestion logic |
| **Failure classification** | C0 (contract satisfied); C2 (adversarial coverage added) |
| **Required action** | None (implementation unchanged) |

---

## COMPAT-002 — Search

| Field | Value |
|---|---|
| **Legacy surface** | `KeywordSearch`, `SemanticSearch`, `HybridSearch`, `GraphSearch`, `SearchEngine` |
| **Current facade** | `knowledge/search/{keyword,semantic,hybrid,graph}_search.py`, `search_engine.py` |
| **Canonical implementation** | W8: `KeywordSearchEngine`, `SemanticVectorSearchEngine`, `HybridSearchEngine`, `GraphSearchEngine`; `KnowledgeSearchEngine` |
| **Public symbols** | Five facade classes; `search(query)` (+ `query_vector` for semantic) |
| **Inputs** | `SearchQuery`; semantic requires explicit `query_vector` tuple |
| **Outputs** | `SearchResultPage` with ranked `SearchResult` entries |
| **Exceptions** | `IndexStaleError`, `IndexValidationError`, `SearchValidationError` propagate |
| **Provenance** | Results carry `document_id`, `target_id`, `lifecycle_state` |
| **Lifecycle** | Filters respected; no promotion via search |
| **Determinism** | Identical queries produce identical ordering/scores |
| **Units/quantities** | N/A |
| **Security/IP** | No provider invocation; no fabricated embeddings; caller-supplied vectors only |
| **Existing tests** | `test_compat_search.py` (5) |
| **Step 4 tests** | `test_compat_adversarial.py` (+4) |
| **Audit result** | Thin delegation; `HybridSearch.search` does not inject spurious `query_vector` |
| **Failure classification** | C0; C2 |
| **Required action** | None |

### Symbol Disposition

| Symbol | Disposition |
|---|---|
| `KeywordSearch.from_lexical_index` | PASS — delegates to `KeywordSearchEngine` |
| `SemanticSearch.from_vector_index` | PASS — explicit vector required (intentional W8 contract) |
| `HybridSearch.from_w7_bundle` | PASS — delegates to `HybridSearchEngine` |
| `GraphSearch.from_graph_index` | PASS — delegates to `GraphSearchEngine` |
| `SearchEngine` | PASS — subclasses `KnowledgeSearchEngine` |
| `*.canonical_engine` | PASS — exposes underlying engine for verification |

---

## COMPAT-003 — Indexing

| Field | Value |
|---|---|
| **Legacy surface** | `KeywordIndex`, `SemanticIndex`, `GraphIndex`, `build_*_from_store` |
| **Current facade** | `knowledge/indexing/{keyword,semantic,graph}_index.py` |
| **Canonical implementation** | `InMemoryLexicalIndex`, `InMemorySemanticIndex`, `InMemoryGraphIndex`; W7 builders |
| **Public symbols** | Type aliases + `build_keyword_index_from_store`, `build_semantic_index_from_store`, `build_graph_index_from_store` |
| **Inputs** | `GraphStore` |
| **Outputs** | Canonical index instances |
| **Exceptions** | Builder validation errors propagate |
| **Provenance** | Indexes bound to `source_digest` from graph snapshot |
| **Lifecycle** | Index records include lifecycle metadata |
| **Determinism** | Repeated builds from same store produce identical lookups |
| **Units/quantities** | N/A |
| **Security/IP** | No external vector services |
| **Existing tests** | `test_compat_indexing.py` (6) |
| **Step 4 tests** | `test_compat_adversarial.py` (+1) |
| **Audit result** | Pure aliases; no duplicate index implementation |
| **Failure classification** | C0; C2 |
| **Required action** | None |

---

## COMPAT-004 — Graph

| Field | Value |
|---|---|
| **Legacy surface** | `GraphManager` |
| **Current facade** | `knowledge/graph/graph_manager.py` |
| **Canonical implementation** | `GraphConstructor`, `GraphQueryService`, `GraphStore` |
| **Public symbols** | `construct`, `query_service`, `traverse`, `store`, `ontology_registry` |
| **Inputs** | `GraphConstructionBatch`; traversal `start_node_id`, `max_depth` |
| **Outputs** | `GraphConstructionResult`; `TraversalResult` |
| **Exceptions** | `GraphQueryError` when accessing store/query before `construct()` |
| **Provenance** | Construction preserves entity provenance from batch |
| **Lifecycle** | No promotion via manager |
| **Determinism** | Construction deterministic for identical batches |
| **Units/quantities** | N/A |
| **Security/IP** | Single graph authority (ADR-001) |
| **Existing tests** | `test_compat_graph.py` (4) |
| **Step 4 tests** | `test_compat_adversarial.py` (+1) |
| **Audit result** | No competing graph store |
| **Failure classification** | C0; C2 |
| **Required action** | None |

---

## COMPAT-005 — Ontology

| Field | Value |
|---|---|
| **Legacy surface** | `OntologyManager` |
| **Current facade** | `knowledge/ontology/ontology_manager.py` |
| **Canonical implementation** | `OntologyRegistry` (ADR-008) |
| **Public symbols** | `register_term`, `get_term`, `resolve_alias`, `register_alias`, `list_terms`, `validate_relationship`, etc. |
| **Inputs** | `OntologyTerm`, `OntologyAlias`, relationship parameters |
| **Outputs** | Registry state; `OntologyTerm`; `RelationshipValidationResult` |
| **Exceptions** | `DuplicateOntologyTermError`, `AliasConflictError`, `OntologyValidationError` propagate |
| **Provenance** | Registry metadata exposed via `metadata` property |
| **Lifecycle** | N/A at ontology layer |
| **Determinism** | Registry digest stable for identical registrations |
| **Units/quantities** | N/A |
| **Security/IP** | Dynamic registry only; no static domain modules recreated |
| **Existing tests** | `test_compat_ontology.py` (3) |
| **Step 4 tests** | `test_compat_adversarial.py` (+1) |
| **Audit result** | Full delegation; `list_terms()` correctly maps to registry |
| **Failure classification** | C0; C2 |
| **Required action** | None |

---

## COMPAT-006 — Knowledge Pipeline

| Field | Value |
|---|---|
| **Legacy surface** | `run_knowledge_pipeline()` |
| **Current facade** | `knowledge/pipelines/knowledge_pipeline.py` → `orchestrator.py` |
| **Canonical implementation** | W3→W4→ontology→graph→W7→W8→W9 (`validate_context`)→W10→controlled RAG→packaging→interface |
| **Public symbols** | `run_knowledge_pipeline`, `normalize_markdown_text`, `KnowledgePipelineArtifacts` |
| **Inputs** | Markdown `content` string; optional task, query, IDs, extra entities, registry |
| **Outputs** | `KnowledgePipelineArtifacts` (extraction through payload) |
| **Exceptions** | Canonical validation/construction errors propagate |
| **Provenance** | Full chain preserved through graph, RAG, package, payload digests |
| **Lifecycle** | Entities remain `CANDIDATE`; no promotion |
| **Determinism** | Identical inputs produce identical index/RAG digests |
| **Units/quantities** | Preserved through canonical extraction path |
| **Security/IP** | `provider_invoked=False`; no cloud dependency |
| **Existing tests** | `test_compat_pipeline.py` (3), `test_compat_integration.py` (1) |
| **Step 4 tests** | `test_compat_adversarial.py` (+2) |
| **Audit result** | Aligns with BLOCK-012 integration path; uses `validate_context` not Phase-C extended validation |
| **Failure classification** | C0; C1 (extended validation scope documented); C2 |
| **Required action** | Documentation only for C1 |

### C1 Note — Validation Scope

`run_knowledge_pipeline` invokes `validate_context` (W9 baseline), not `validate_context_extended` (Phase C). This is **intentional**: the pipeline mirrors the BLOCK-012 qualification helper, not the additive Phase-C extended validation surface. Phase-C validators remain available via direct import.

---

## Delegation Integrity

| Check | Result |
|---|---|
| Canonical W3/W4/W7/W8 imports `knowledge.compat` | **NO** (only Phase-B loader facades import `ingest_file_from_path`) |
| Facade creates second implementation | **NO** |
| Frozen KG-BLOCK-001→012 modified | **NO** |
| Frozen Phase-B/C facades modified | **NO** |

---

## Final Disposition

```text
NO GENUINE COMPATIBILITY FAILURES FOUND (C3 = 0)
NO IMPLEMENTATION CHANGES REQUIRED
TEST HARDENING APPLIED (C2)
DOCUMENTATION GAPS CLOSED (C1)
```
