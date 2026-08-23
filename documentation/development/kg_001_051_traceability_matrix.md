# KG-001 → KG-051 Traceability Matrix

**Document ID:** COSMOS-KG-TRACE-001  
**Date:** 2026-08-23  
**Status:** AUTHORITATIVE — HUMAN APPROVED (2026-08-23)  
**Parent:** `kg_architecture_reconciliation.md`

Per-batch traceability for the new architecture. **Old frozen batch IDs are shown in the Legacy column where applicable.**

Legend: **F** = frozen historical implementation exists | **P** = partial | **N** = not complete | **C** = complete at reference level

---

## W0 — Contracts / Foundation

| New ID | Capability | Legacy (frozen) | Implementation evidence | Tests | Gap | Status |
|--------|------------|-----------------|-------------------------|-------|-----|--------|
| KG-001 | Source & provenance contracts | KG-002 | `graph/provenance.py`, `graph/source_identity.py` | `test_provenance.py`, `test_source_identity.py` | Dedicated license/IP subsystem | **C/F** |
| KG-002 | Entity / relationship contracts | KG-003 | `graph/entity.py`, `graph/relationship.py` | `test_entity.py`, `test_relationship.py` | — | **C/F** |
| KG-003 | Lifecycle & version contracts | KG-004, KG-006 | `graph/lifecycle.py`, `graph/snapshot.py` | `test_lifecycle.py`, `test_snapshot.py` | — | **C/F** |
| KG-004 | KG interfaces & protocols | KG-001, KG-005 | `graph/contracts.py`, `graph/repository.py` | `test_contracts.py`, `test_repository.py` | — | **C/F** |

---

## W1 — Source System

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-005 | Source registry | KG-007 | `repository/source_registry.py`, `source_repository.py` | `test_source_registry.py` | — | **C/F** |
| KG-006 | Source hashing / integrity | KG-002 | SHA-256 in `source_identity.py`, ingestion models | `test_source_identity.py` | End-to-end integrity workflow | **P/F** |
| KG-007 | License & IP metadata | — | `license_identifier` on source records | partial | Full IP metadata subsystem | **P** |
| KG-008 | Source vault interface | — | — | — | Entire vault boundary | **N** |

---

## W2 — Ingestion

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-009 | PDF ingestion | KG-008, KG-009 | `ingestion/`, `parsers/pdf_normalizer.py` | `test_ingestion.py`, `test_parsers.py` | Binary PDF pipeline, bulk ingest | **P/F** |
| KG-010 | DOCX | KG-008 | enum in `ingestion/models.py` only | contracts | Production adapter | **N** |
| KG-011 | PPTX / XLSX | KG-008 | enum only | contracts | Production adapters | **N** |
| KG-012 | HTML / Markdown | KG-008 | enum only | contracts | Production adapters | **N** |
| KG-013 | Repository ingestion | KG-008 | `ingestion/base.py` contracts | `test_ingestion.py` | Filesystem/corpus crawling | **N** |

---

## W3 — Parsing

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-014 | Document structure | KG-009 | `parsers/models.py` (`NormalizedParsedDocument`) | `test_parsers.py` | Production structure parser | **P/F** |
| KG-015 | Tables | — | — | — | Table parser | **N** |
| KG-016 | Figures | — | — | — | Figure extraction | **N** |
| KG-017 | Equations | KG-010 | `extraction/equation.py`, parser hooks | `test_extraction.py` | Production equation parser | **P/F** |
| KG-018 | References / citations | — | — | — | Citation parser | **N** |

---

## W4 — Extraction

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-019 | Engineering entities | KG-011 | `extraction/entity.py` | `test_extraction.py` | Autonomous extraction engine | **P/F** |
| KG-020 | Quantities / units | — | `models/quantity.py`, `unit.py` (protected) | `test_quantity.py` | Extraction pipeline to graph | **P** |
| KG-021 | Equations / variables | KG-010 | `extraction/equation.py`, `models/variable.py` | `test_extraction.py` | Production extraction | **P/F** |
| KG-022 | Claims / evidence | KG-012 | `extraction/claim.py` | `test_extraction.py` | Conflict resolution policy | **P/F** |
| KG-023 | Relationships | KG-003, KG-012 | `graph/relationship.py`, claim contracts | graph + extraction tests | Production relationship extraction | **P/F** |

---

## W5 — Ontology

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-024 | Canonicalization | KG-013 | `ontology/registry.py` | `test_ontology.py` | Full COSMOS canonicalization rules | **P/F** |
| KG-025 | Aliases | KG-013 | `ontology/models.py` | `test_ontology.py` | — | **C/F** |
| KG-026 | Domain taxonomy | KG-013 | registry infrastructure | `test_ontology.py` | Complete engineering taxonomy | **P** |
| KG-027 | Relationship rules | KG-013 | relationship vocabulary | `test_ontology.py` | Formal rule system | **P** |

---

## W6 — Graph

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-028 | Graph storage | KG-005, KG-014 | `graph/repository.py`, `memory_store.py` | `test_repository.py` | Persistent graph DB | **C/F** |
| KG-029 | CRUD | KG-005 | `GraphStore` API | `test_repository.py` | — | **C/F** |
| KG-030 | Traversal | KG-016 | `graph/query.py` | `test_query.py` | — | **C/F** |
| KG-031 | Subgraphs | KG-016 | `GraphQueryService.subgraph` | `test_query.py` | — | **C/F** |
| KG-032 | Snapshots | KG-006 | `graph/serialization.py`, `snapshot.py` | `test_serialization.py` | — | **C/F** |

---

## W7 — Indexing

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-033 | Lexical index | **OLD KG-017** | `indexing/lexical.py` | `test_indexing.py` | Persistent index | **C/F** |
| KG-034 | Vector index | **OLD KG-018** | `indexing/semantic.py` (term-overlap) | `test_indexing.py` | Embedding backend | **P/F** |
| KG-035 | Graph index | KG-016 | graph query only | `test_query.py` | Dedicated graph index | **P** |

---

## W8 — Search

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-036 | Keyword search | OLD KG-017/019 | `search/engine.py` lexical mode | `test_search.py` | — | **C/F** |
| KG-037 | Semantic search | OLD KG-018/019 | semantic mode (overlap) | `test_search.py` | Real semantic backend | **P/F** |
| KG-038 | Graph search | KG-016 | structured mode, graph query | `test_search.py` | Richer field-schema search | **P/F** |
| KG-039 | Hybrid search | OLD KG-019 | hybrid mode | `test_search.py`, hardening | — | **C/F** |

---

## W9 — Validation

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-040 | Schema validation | KG-015 | `graph/validation.py` | `test_validation.py` | Expanded schema rules | **P/F** |
| KG-041 | Provenance validation | KG-015 | validation + provenance checks | `test_validation.py` | — | **P/F** |
| KG-042 | Unit / dimension validation | — | `models/quantity.py` etc. | model tests | KG-layer validation | **N** |
| KG-043 | Duplicate detection | OLD KG-017 | index duplicate rejection | hardening tests | Cross-graph dedup policy | **P/F** |
| KG-044 | Conflict detection | KG-012, KG-015 | `conflict_visibility`, reasoner | hardening tests | Cross-source value conflicts | **P/F** |

---

## W10 — Reasoning

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-045 | Provenance-aware reasoning | OLD KG-020 | `reasoning/reasoner.py` | `test_reasoning.py` | — | **C/F** |
| KG-046 | Evidence chains | OLD KG-020 | `reasoning/evidence.py` | `test_reasoning.py` | Full chain assembly | **P/F** |
| KG-047 | Engineering context builder | OLD KG-021 | `reasoning/context.py` | `test_reasoning.py` | — | **C/F** |

---

## W11 — AI / RAG / Cursor Interface

| New ID | Capability | Legacy | Implementation evidence | Tests | Gap | Status |
|--------|------------|--------|-------------------------|-------|-----|--------|
| KG-048 | Controlled RAG | — | — | — | Entire RAG consumer | **N** |
| KG-049 | Context packaging | OLD KG-021 | `EngineeringContextPackage` | `test_reasoning.py` | Production packaging | **P/F** |
| KG-050 | Cursor development context | OLD KG-021 | context assembler | `test_reasoning.py` | Cursor integration layer | **P** |
| KG-051 | Knowledge-to-engineering interface | — | — | — | Controlled engineering bridge | **N** |

---

## Summary Counts (New Matrix)

| Status | Count (of 51) |
|--------|---------------|
| Complete / frozen foundation (C/F) | 22 |
| Partial (P or P/F) | 22 |
| Not complete (N) | 7 |

---

## Numbering Conflict Register

| Conflicting new ID | New meaning | Old frozen meaning | Resolution |
|--------------------|-------------|-------------------|------------|
| KG-017 | Equation parsing | Lexical index | Preserve frozen `indexing/lexical.py`; map to **KG-033** |
| KG-018 | References/citations | Semantic index | Preserve frozen `indexing/semantic.py`; map to **KG-034** |
| KG-019 | Engineering entities | Hybrid retrieval | Preserve frozen search engine; map to **KG-039** |
| KG-020 | Quantities/units | Evidence ranking | Preserve frozen `reasoning/evidence.py`; map to **KG-046** |
| KG-021 | Equations/variables | Context package | Preserve frozen `reasoning/context.py`; map to **KG-047** |
| KG-022 | Claims/evidence | *(old program: not defined)* | Old claim contracts map here; no conflict with frozen block ID |

**Rule:** Always cite **legacy batch ID** when referring to frozen code; use **new batch ID** for forward development planning.
