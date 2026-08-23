# Knowledge Compatibility Layer Plan

**Document ID:** COSMOS-KG-COMPAT-PLAN-001
**Date:** 2026-08-23
**Phase:** PLAN ONLY — Phase A governance gate COMPLETE; **Phase B implementation NOT authorized**

## Pattern

```text
Frozen API (import path)
    ↓
Compatibility facade (thin, tested)
    ↓
Current canonical implementation
```

## Proposed Facades (Priority Order)

| ID | Frozen Path | Facade API | Canonical Target | Behavior | Test Plan | Block |
|----|-------------|------------|------------------|----------|-----------|-------|
| COMPAT-001 | `knowledge/ingestion/pdf_loader.py` | `load_pdf(path) -> IngestionResult` | `ingestion_adapters.pdf.PdfIngestionAdapter.ingest` | Delegate + provenance | `test_compat_ingestion.py` | BLOCK-013 |
| COMPAT-002 | `knowledge/search/keyword_search.py` | `KeywordSearch` class | `search/w8/keyword.KeywordSearchEngine` | Deterministic keyword retrieval | `test_compat_search.py` | BLOCK-013 |
| COMPAT-003 | `knowledge/indexing/keyword_index.py` | `KeywordIndex` | `indexing/lexical.InMemoryLexicalIndex` | Index build/query passthrough | `test_compat_indexing.py` | BLOCK-013 |
| COMPAT-004 | `knowledge/graph/graph_manager.py` | `GraphManager` | `graph/construction.GraphConstructor` + `graph/query.GraphQueryService` | Unified graph API | `test_compat_graph.py` | BLOCK-013 |
| COMPAT-005 | `knowledge/ontology/ontology_manager.py` | `OntologyManager` | `ontology/registry.OntologyRegistry` | Term register/lookup | `test_compat_ontology.py` | BLOCK-013 |
| COMPAT-006 | `knowledge/pipelines/knowledge_pipeline.py` | `run_knowledge_pipeline` | `tests/.../pipeline.run_full_pipeline` (prod: new orchestrator) | E2E orchestration | E2E regression | BLOCK-013+ |

## Explicit Non-Facades (Do Not Create)

| Frozen Path | Reason |
|-------------|--------|
| Duplicate `models/*.py` for consolidated types | Would duplicate parser/ontology models |
| Empty `repositories/*_repository.py` stubs | No behavior; violates no-dummy-files rule |
| `recommendation_engine.py` | Superseded by controlled RAG — ADR-010 |
| Static `ontology/propulsion.py` etc. | Superseded by registry — ADR-008 |

## Facade Requirements

1. Real behavior only — delegate to canonical implementation
2. Preserve provenance and lifecycle fields
3. Deterministic where canonical is deterministic
4. Do not modify frozen BLOCK-001→012 canonical modules
5. Full unit test coverage per facade

**Status:** Phase A facade governance gate COMPLETE (`kg_block_013_phase_a_governance_report.md` §8). Implementation gated on **separate Phase B authorization**.