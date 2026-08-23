# Knowledge Folder — Per-File Audit Matrix

**Document ID:** COSMOS-DEV-KG-AUDIT-001  
**Date:** 2026-08-23  
**Scope:** Every `knowledge/**/*.py` file  
**Repository:** COSMOS-0.1  
**Regression:** 961 passed, 5 skipped (full); 575 passed, 5 skipped (knowledge)

---

## Summary

| Metric | Value |
|--------|-------|
| Total Python files | 63 |
| KG-frozen | 48 |
| Implemented (not KG-frozen) | 13 |
| Structural (empty `__init__.py`) | 2 |
| Missing tests | 0 |
| Import failures | 0 |

---

## Per-File Classification

| File | Owner | Block | Status | Freeze | Test coverage | Deferred |
|------|-------|-------|--------|--------|---------------|----------|
| `knowledge/__init__.py` | Structural | — | EMPTY | — | N/A | — |
| **graph/** | | | | | | |
| `graph/__init__.py` | KG-001→021 | BLOCK-001/003 | FROZEN | YES | `test_contracts`, exports | — |
| `graph/contracts.py` | KG-001 | BLOCK-001 | FROZEN | YES | `test_contracts.py` | — |
| `graph/exceptions.py` | KG-001/003 | BLOCK-001/003 | FROZEN | YES | `test_exceptions.py` | — |
| `graph/source_identity.py` | KG-002 | BLOCK-001 | FROZEN | YES | `test_source_identity.py` | — |
| `graph/provenance.py` | KG-002 | BLOCK-001 | FROZEN | YES | `test_provenance.py` | — |
| `graph/entity.py` | KG-003 | BLOCK-001 | FROZEN | YES | `test_entity.py` | — |
| `graph/relationship.py` | KG-003 | BLOCK-001 | FROZEN | YES | `test_relationship.py` | — |
| `graph/lifecycle.py` | KG-004 | BLOCK-001 | FROZEN | YES | `test_lifecycle.py` | — |
| `graph/repository.py` | KG-005 | BLOCK-001 | FROZEN | YES | `test_repository.py` | persistent backend |
| `graph/serialization.py` | KG-006 | BLOCK-001 | FROZEN | YES | `test_serialization.py` | — |
| `graph/snapshot.py` | KG-006 | BLOCK-001 | FROZEN | YES | `test_snapshot.py` | — |
| `graph/construction.py` | KG-014 | BLOCK-003 | FROZEN | YES | `test_construction.py` | full pipeline integration |
| `graph/memory_store.py` | KG-014/005 | BLOCK-003 | FROZEN | YES | `test_repository.py` | persistent backend |
| `graph/validation.py` | KG-015 | BLOCK-003 | FROZEN | YES | `test_validation.py` | — |
| `graph/query.py` | KG-016 | BLOCK-003 | FROZEN | YES | `test_query.py` | — |
| **repository/** | | | | | | |
| `repository/__init__.py` | Structural | — | EMPTY | — | N/A | — |
| `repository/source_registry.py` | KG-007 | BLOCK-001 | FROZEN | YES | `test_source_registry.py` | — |
| `repository/source_repository.py` | KG-007 | BLOCK-001 | FROZEN | YES | `test_source_repository.py` | — |
| `repository/repository.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_repository.py` | persistent/SQLite backend |
| **ingestion/** | | | | | | |
| `ingestion/__init__.py` | KG-008 | BLOCK-002 | FROZEN | YES | `test_ingestion.py` | — |
| `ingestion/base.py` | KG-008 | BLOCK-002 | FROZEN | YES | `test_ingestion.py` | production adapters |
| `ingestion/models.py` | KG-008 | BLOCK-002 | FROZEN | YES | `test_ingestion.py` | — |
| `ingestion/exceptions.py` | KG-008 | BLOCK-002 | FROZEN | YES | `test_ingestion.py` | — |
| **parsers/** | | | | | | |
| `parsers/__init__.py` | KG-009 | BLOCK-002 | FROZEN | YES | `test_parsers.py` | — |
| `parsers/base.py` | KG-009 | BLOCK-002 | FROZEN | YES | `test_parsers.py` | — |
| `parsers/models.py` | KG-009 | BLOCK-002 | FROZEN | YES | `test_parsers.py` | — |
| `parsers/pdf_normalizer.py` | KG-009 | BLOCK-002 | FROZEN | YES | `test_parsers.py` | binary PDF pipeline |
| `parsers/exceptions.py` | KG-009 | BLOCK-002 | FROZEN | YES | `test_parsers.py` | — |
| **extraction/** | | | | | | |
| `extraction/__init__.py` | KG-010→012 | BLOCK-002 | FROZEN | YES | `test_extraction.py` | — |
| `extraction/equation.py` | KG-010 | BLOCK-002 | FROZEN | YES | `test_extraction.py` | autonomous extraction |
| `extraction/entity.py` | KG-011 | BLOCK-002 | FROZEN | YES | `test_extraction.py` | autonomous extraction |
| `extraction/claim.py` | KG-012 | BLOCK-002 | FROZEN | YES | `test_extraction.py` | conflict resolution policy |
| `extraction/exceptions.py` | KG-010→012 | BLOCK-002 | FROZEN | YES | `test_extraction.py` | — |
| **ontology/** | | | | | | |
| `ontology/__init__.py` | KG-013 | BLOCK-002 | FROZEN | YES | `test_ontology.py` | — |
| `ontology/models.py` | KG-013 | BLOCK-002 | FROZEN | YES | `test_ontology.py` | — |
| `ontology/registry.py` | KG-013 | BLOCK-002 | FROZEN | YES | `test_ontology.py` | ontology expansion |
| `ontology/exceptions.py` | KG-013 | BLOCK-002 | FROZEN | YES | `test_ontology.py` | — |
| **indexing/** | | | | | | |
| `indexing/__init__.py` | KG-017/018 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | — |
| `indexing/models.py` | KG-017 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | — |
| `indexing/exceptions.py` | KG-017 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | — |
| `indexing/lexical.py` | KG-017 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | persistent index |
| `indexing/semantic.py` | KG-018 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | embedding backend |
| `indexing/builder.py` | KG-017 | BLOCK-004 | FROZEN | YES | `test_indexing.py` | — |
| **search/** | | | | | | |
| `search/__init__.py` | KG-018/019 | BLOCK-004 | FROZEN | YES | `test_search.py` | — |
| `search/contracts.py` | KG-018 | BLOCK-004 | FROZEN | YES | `test_search.py` | — |
| `search/engine.py` | KG-019 | BLOCK-004 | FROZEN | YES | `test_search.py`, hardening | richer structured fields |
| `search/exceptions.py` | KG-018/019 | BLOCK-004 | FROZEN | YES | `test_search.py` | — |
| **reasoning/** | | | | | | |
| `reasoning/__init__.py` | KG-020/021 | BLOCK-004 | FROZEN | YES | `test_reasoning.py` | — |
| `reasoning/exceptions.py` | KG-020 | BLOCK-004 | FROZEN | YES | `test_reasoning.py` | — |
| `reasoning/evidence.py` | KG-020 | BLOCK-004 | FROZEN | YES | `test_reasoning.py`, hardening | — |
| `reasoning/reasoner.py` | KG-020 | BLOCK-004 | FROZEN | YES | `test_reasoning.py`, hardening | cross-source conflict policy |
| `reasoning/context.py` | KG-021 | BLOCK-004 | FROZEN | YES | `test_reasoning.py` | RAG consumer |
| **models/** | | | | | | |
| `models/__init__.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | indirect | — |
| `models/quantity.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | **PROTECTED** | `test_quantity.py` | — |
| `models/unit.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | **PROTECTED** | `test_unit.py` | — |
| `models/dimension.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | **PROTECTED** | `test_dimension.py` | — |
| `models/variable.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_variable.py` | — |
| `models/constant.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_constant.py` | — |
| `models/equation.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_equation.py` | — |
| `models/document.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_document.py` | — |
| `models/reference.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | indirect | — |
| `models/material.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_material.py` | — |
| `models/subsystem.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_subsystem.py` | — |
| `models/engineering_domain.py` | Knowledge Foundation | Pre-KG | IMPLEMENTED | NO | `test_engineering_domain.py` | — |

---

## Static Analysis (KG-frozen packages)

```text
Ruff:  PASS (indexing, search, reasoning, graph scope)
Mypy:  PASS (indexing, search, reasoning, graph scope)
```

---

## Integration Status

| Pipeline stage | Integration test | Status |
|----------------|------------------|--------|
| graph construction → query | Partial (unit-level) | UNIT ONLY |
| graph → index → search | Partial (unit-level) | UNIT ONLY |
| search → evidence → context | Partial (unit-level) | UNIT ONLY |
| ingestion → parsing → extraction → construction | None | **DEFERRED** |
| end-to-end corpus pipeline | None | **DEFERRED** |

---

## Verdict

```text
INVENTORY:     COMPLETE (63/63 files)
KG BASELINE:   FROZEN through KG-021 (48 files)
UNIT TESTS:    ALL MODULES COVERED
PRODUCTION:    NOT GLOBALLY QUALIFIED (integration + production backends deferred)
```
