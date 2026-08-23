# COSMOS Step 6 — Capability Traceability

**Document ID:** `COSMOS-STEP6-CAPABILITY-TRACEABILITY-001`  
**Date:** 2026-08-23

---

## CAP-STEP6-001 — Extended Validation Pipeline

| Layer | Trace |
|---|---|
| **Module** | `knowledge/pipelines/extended_pipeline.py` |
| **Public API** | `run_knowledge_pipeline_extended()` |
| **Canonical deps** | `validate_context_extended`, W3 `parse_document`, frozen `KnowledgePipelineArtifacts` |
| **Frozen boundary** | Does not modify `orchestrator.py` |
| **Tests** | `test_step6_extended_pipeline.py` (3), `test_step6_integration.py` (1) |
| **RAG path** | Full W1→W11 with Phase-C validation report passed to `ControlledRAGOrchestrator` |

---

## CAP-STEP6-002 — Graph Integrity Diagnostics

| Layer | Trace |
|---|---|
| **Module** | `knowledge/graph/diagnostics.py` |
| **Public API** | `analyze_graph_integrity()`, `GraphIntegrityDiagnostics` |
| **Canonical deps** | `GraphRecordValidator`, `canonical_graph_record_digest` |
| **Tests** | `test_graph_diagnostics.py` (2) |
| **RAG relevance** | Pre/post graph construction quality assurance |

---

## CAP-STEP6-003 — Retrieval Diagnostics

| Layer | Trace |
|---|---|
| **Module** | `knowledge/search/retrieval_diagnostics.py` |
| **Public API** | `build_retrieval_diagnostics()`, `RetrievalDiagnostics` |
| **Canonical deps** | `SearchQuery`, `SearchResultPage`, W8 hybrid engine |
| **Tests** | `test_retrieval_diagnostics.py` (2) |
| **RAG relevance** | Explainable retrieval for controlled local RAG |

---

## CAP-STEP6-004 — Evidence Chain Validation

| Layer | Trace |
|---|---|
| **Module** | `knowledge/validation/evidence_chain.py` |
| **Public API** | `validate_evidence_chain()` |
| **Canonical deps** | `ValidationContext`, `make_finding`, W4 extraction models |
| **Tests** | `test_evidence_chain.py` (2) |
| **RAG relevance** | Provenance completeness before validation-aware search |

---

## CAP-STEP6-005 — Evidence Summary

| Layer | Trace |
|---|---|
| **Module** | `knowledge/interface/evidence_summary.py` |
| **Public API** | `summarize_evidence()`, `EvidenceSummary` |
| **Canonical deps** | `ContextPackage`, W10 `EvidenceBundle` |
| **Tests** | `test_evidence_summary.py` (2) |
| **RAG relevance** | Cursor-ready deterministic evidence metadata |

---

## Quality Defect Traceability

| Defect | Fix | Verification |
|---|---|---|
| Q1 Pipeline/Phase-C gap | CAP-STEP6-001 | Extended pipeline tests |
| Q2 Graph topology gaps | CAP-STEP6-002 | Graph diagnostics tests |
| Q3 Retrieval explainability | CAP-STEP6-003 | Retrieval diagnostics tests |
| Q4 Evidence provenance gaps | CAP-STEP6-004 | Evidence chain tests |
| Q5 Package usability | CAP-STEP6-005 | Evidence summary tests |

---

## Frozen Integrity Matrix

| Path | Modified |
|---|---|
| `knowledge/pipelines/orchestrator.py` | **NO** |
| Phase-B compat facades | **NO** |
| Phase-C validation modules | **NO** |
| KG-BLOCK-001→012 canonical | **NO** |
| Frozen models (`quantity`, `unit`, `dimension`) | **NO** |
