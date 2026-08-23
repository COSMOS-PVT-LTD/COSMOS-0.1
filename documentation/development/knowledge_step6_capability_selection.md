# COSMOS Step 6 — Capability Selection

**Document ID:** `COSMOS-STEP6-CAPABILITY-SELECTION-001`  
**Date:** 2026-08-23

---

## Selection Methodology

Candidates ranked by: engineering/RAG value (30%), reliability/trust (20%), reusability (15%), architecture fit (15%), local/offline (10%), implementation risk (10%).

Prohibited: missing model recreation, persistence, exporters, production embeddings, cloud LLM.

---

## Selected Capabilities (Implemented)

| ID | Capability | Score | Owner | Status |
|---|---|---|---|---|
| CAP-STEP6-001 | Extended validation pipeline (`run_knowledge_pipeline_extended`) | 92 | `knowledge/pipelines/` | **IMPLEMENTED** |
| CAP-STEP6-002 | Graph integrity diagnostics (`analyze_graph_integrity`) | 85 | `knowledge/graph/` | **IMPLEMENTED** |
| CAP-STEP6-003 | Retrieval diagnostics (`build_retrieval_diagnostics`) | 82 | `knowledge/search/` | **IMPLEMENTED** |
| CAP-STEP6-004 | Evidence-chain validation (`validate_evidence_chain`) | 88 | `knowledge/validation/` | **IMPLEMENTED** |
| CAP-STEP6-005 | Evidence summary (`summarize_evidence`) | 80 | `knowledge/interface/` | **IMPLEMENTED** |

---

## Capability Records

### CAP-STEP6-001 — Extended Validation Pipeline

| Field | Value |
|---|---|
| **Problem** | Phase-C citation/ambiguity validators exist but are not wired into pipeline orchestration |
| **Current behavior** | `run_knowledge_pipeline()` calls `validate_context()` without `parsed_document` |
| **Why insufficient** | Engineering consumers must manually reconstruct parse context to use Phase-C validation |
| **Canonical owner** | `knowledge/pipelines/extended_pipeline.py` (additive; orchestrator frozen) |
| **Dependencies** | W3 parse, Phase-C `validate_context_extended` |
| **Engineering value** | One-call extended validation + RAG path with citation/ambiguity findings |
| **Risk** | Low — default pipeline unchanged; extended path opt-in |
| **Test strategy** | Unit tests + golden fixture parity |

### CAP-STEP6-002 — Graph Integrity Diagnostics

| Field | Value |
|---|---|
| **Problem** | No topology-level diagnostics (orphan nodes) beyond structural validation |
| **Current behavior** | `GraphRecordValidator` checks endpoints and properties |
| **Why insufficient** | Orphan nodes not explicitly reported for engineering review |
| **Canonical owner** | `knowledge/graph/diagnostics.py` |
| **Engineering value** | Deterministic integrity reports for graph quality review |
| **Risk** | Low — read-only analysis |

### CAP-STEP6-003 — Retrieval Diagnostics

| Field | Value |
|---|---|
| **Problem** | Search results lack structured diagnostic export |
| **Current behavior** | `ranking_reason` on results but no aggregated diagnostics |
| **Engineering value** | Explainable deterministic retrieval for engineering queries |
| **Risk** | Low — read-only |

### CAP-STEP6-004 — Evidence Chain Validation

| Field | Value |
|---|---|
| **Problem** | No dedicated provenance-anchor completeness check across extraction artifacts |
| **Engineering value** | Catches missing document anchors before RAG packaging |
| **Risk** | Low — additive validator |

### CAP-STEP6-005 — Evidence Summary

| Field | Value |
|---|---|
| **Problem** | No lightweight summary of packaged evidence for Cursor/engineering consumers |
| **Engineering value** | Deterministic evidence counts and trust boundary metadata |
| **Risk** | Low — read-only summary |

---

## Deferred Capabilities

| Candidate | Reason |
|---|---|
| New format loaders (epub, latex, OCR) | Frozen-tree recreation; no immediate authorized requirement |
| Production embeddings | Out of scope; ADR-009 pending |
| Exporters | KG-BLOCK-014 not authorized |
| Persistence | KG-BLOCK-015 not authorized |
| Missing domain models (15) | Step 5 governance — defer |
| Ruff fixes in frozen `dimension.py`/`unit.py` | Frozen boundary — requires separate authorization |

---

## Counts

| Category | Count |
|---|---|
| Identified | 5 |
| Implemented | 5 |
| Deferred | 6+ |
