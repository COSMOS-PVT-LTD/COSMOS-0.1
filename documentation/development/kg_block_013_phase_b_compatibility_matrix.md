# KG-BLOCK-013 Phase B — Compatibility Matrix

**Document ID:** COSMOS-KG-B013-PHASE-B-MATRIX-001  
**Date:** 2026-08-23  
**Block:** KG-BLOCK-013 Phase B

---

## Facade Coverage

| ID | Frozen API Surface | Facade Module | Canonical Delegation | Test Module | Status |
|----|-------------------|---------------|---------------------|-------------|--------|
| COMPAT-001 | `load_pdf`, `load_docx`, `load_html`, `load_markdown` | `knowledge/ingestion/*_loader.py` | `ingestion_adapters.*` via `compat.ingestion_loaders` | `test_compat_ingestion.py` | **PASS** |
| COMPAT-002 | `KeywordSearch`, `SemanticSearch`, `HybridSearch`, `GraphSearch`, `SearchEngine` | `knowledge/search/*_search.py`, `search_engine.py` | W8 engines + `KnowledgeSearchEngine` | `test_compat_search.py` | **PASS** |
| COMPAT-003 | `KeywordIndex`, `SemanticIndex`, `GraphIndex` | `knowledge/indexing/*_index.py` | `InMemoryLexicalIndex`, `InMemorySemanticIndex`, `InMemoryGraphIndex` | `test_compat_indexing.py` | **PASS** |
| COMPAT-004 | `GraphManager` | `knowledge/graph/graph_manager.py` | `GraphConstructor` + `GraphQueryService` | `test_compat_graph.py` | **PASS** |
| COMPAT-005 | `OntologyManager` | `knowledge/ontology/ontology_manager.py` | `OntologyRegistry` | `test_compat_ontology.py` | **PASS** |
| COMPAT-006 | `run_knowledge_pipeline` | `knowledge/pipelines/knowledge_pipeline.py` | `pipelines/orchestrator.py` | `test_compat_pipeline.py`, `test_compat_integration.py` | **PASS** |

---

## Behavioral Guarantees

| Guarantee | Verified |
|-----------|----------|
| Provenance fields preserved through ingestion facades | Yes |
| Deterministic keyword/semantic/hybrid search | Yes |
| `provider_invoked=False` for controlled RAG | Yes |
| Pipeline parity with BLOCK-012 integration helper | Yes |
| No modification of frozen canonical modules | Yes |

---

## Non-Facades (Confirmed Absent)

Per compatibility plan — no duplicate `models/`, empty repository stubs, `recommendation_engine.py`, or static ontology domain files created.

---

## Test Summary

```text
Compat tests: 27 passed
Full regression: 1246 passed, 5 skipped (+27)
```
