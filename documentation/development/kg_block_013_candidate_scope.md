# KG-BLOCK-013 Candidate Scope

**Document ID:** COSMOS-KG-BLOCK-013-SCOPE-001  
**Date:** 2026-08-23  
**Status:** PHASE A COMPLETE — Phase B READY (separate authorization required)  
**Prerequisite:** Governance plan + decision gate approval

---

## Executive Summary

KG-BLOCK-013 is **NOT** a bulk implementation of the 67 missing frozen files.

It is a **governance-first, compatibility-second, gap-selective** block focused on closing architectural contract surfaces and highest-value genuine gaps — without restarting the Knowledge Foundation.

```text
P0 Governance / ADR closure
    ↓
P1 Compatibility interfaces (13 facades)
    ↓
P2 Genuine capability gaps (selective)
    ↓
P3 Local RAG productionization prerequisites (minimal)
    ↓
P4 Verification + certification update
```

---

## What BLOCK-013 Is NOT

| Excluded | Reason | Target |
|----------|--------|--------|
| 67-file tree recreation | Violates primary engineering decision | Never |
| 11 domain model files | ADR-002; W4/graph interim sufficient | BLOCK-017 |
| 14 entity repositories | ADR-001 graph-primary | REMOVED |
| 7 exporters | No current consumer; not RAG-critical | BLOCK-014 |
| Production embeddings | ADR-009 | BLOCK-016 |
| Persistent graph/vector store | Infrastructure scope | BLOCK-015 |
| Frozen BLOCK-001→011 changes | Frozen | Defect-only |
| BLOCK-012 freeze | Separate human action | Pre-BLOCK-013 |

---

## Phase A — Architecture Decisions (P0)

**Status:** **COMPLETE** (2026-08-23) — `kg_block_013_phase_a_governance_report.md`

| Deliverable | Action |
|-------------|--------|
| Approve decision gate DG-001→199 | Human sign-off |
| Close ADR-001, 003, 004, 008, 010, 011 | Minimum for BLOCK-013 |
| Close ADR-005, 006, 007 | Required before any F-disposition work |
| Approve DEV-001→010 retentions | Deviation register |
| Approve BLOCK-012 freeze | Configuration control |

### ADR minimum closure set for Phase B start

| ADR | Decision needed |
|-----|-----------------|
| ADR-003 | Approve W3/W4/W7/W8/W10 subpackages |
| ADR-010 | Approve controlled RAG supersession |
| ADR-011 | Approve compatibility facade strategy |
| ADR-008 | Approve dynamic ontology registry |
| ADR-001 | Approve graph-primary; remove entity repos |

---

## Phase B — Compatibility Facades (P1)

**Authorized only after Phase A + ADR-011 approval.**

| ID | Frozen Module | Facade Location | Canonical Delegate | Tests |
|----|---------------|-----------------|-------------------|-------|
| COMPAT-001 | `ingestion/pdf_loader.py` (+ docx, html, markdown) | New thin modules at frozen paths | `ingestion_adapters/*.py` | `test_compat_ingestion.py` |
| COMPAT-002 | `search/keyword_search.py` (+ semantic, hybrid, graph, engine) | Frozen search paths | `search/w8/*`, `search/engine.py` | `test_compat_search.py` |
| COMPAT-003 | `indexing/keyword_index.py` (+ semantic, graph) | Frozen index paths | `indexing/lexical.py`, `semantic.py`, `w7/graph_index.py` | `test_compat_indexing.py` |
| COMPAT-004 | `graph/graph_manager.py` | Frozen path | `graph/construction.py` + `query.py` | `test_compat_graph.py` |
| COMPAT-005 | `ontology/ontology_manager.py` | Frozen path | `ontology/registry.py` | `test_compat_ontology.py` |
| COMPAT-006 | `pipelines/knowledge_pipeline.py` | Frozen path | New production orchestrator (not test helper) | E2E regression |

### Facade constraints

- Delegate only — zero duplicate business logic
- Mark as compatibility infrastructure
- Preserve provenance, lifecycle, determinism
- Do not modify frozen BLOCK-001→011 modules
- Full unit + contract tests per facade

**Estimated new files:** ~15–20 (facades + tests) — not 67

---

## Phase C — Highest-Value Genuine Capability Gaps (P2)

**Selective implementation only — evidence-based.**

### C.1 — Validation gaps (recommended for BLOCK-013)

| File | Gap Type | Justification |
|------|----------|---------------|
| `validation/citation_validator.py` | GAP-1 | Citation integrity not fully validated |
| `validation/ambiguity_detector.py` | GAP-1 | Ambiguity detection absent |

### C.2 — Text utilities (if ADR approves)

| File | Gap Type | Justification |
|------|----------|---------------|
| `utils/text_utils.py` | GAP-1 (minor) | Shared text helpers; low risk |

### C.3 — Parser gaps (optional in BLOCK-013)

| File | Gap Type | Justification |
|------|----------|---------------|
| `parsers/glossary_parser.py` | GAP-1 | Glossary extraction for engineering docs |
| `parsers/appendix_parser.py` | GAP-1 | Appendix structure |
| `extraction/glossary_extractor.py` | GAP-1 | Depends on glossary parser |
| `extraction/abbreviation_extractor.py` | GAP-1 | Abbreviation tables in specs |

### C.4 — Operational ingestion (optional in BLOCK-013)

| File | Gap Type | Justification |
|------|----------|---------------|
| `ingestion/batch_loader.py` | GAP-1 | Batch ingest operations |

### C.5 — Format loaders (defer unless prioritized)

| File | Priority |
|------|----------|
| `epub_loader.py` | LOW — defer |
| `latex_loader.py` | MEDIUM — engineering docs |
| `image_loader.py` | LOW |
| `ocr_loader.py` | LOW |
| `markitdown_loader.py` | LOW |

### Explicitly NOT in Phase C

- All 7 exporters → BLOCK-014
- All 14 entity repositories → REMOVED
- All 11 domain models → BLOCK-017
- All W4-consolidated extractors → already covered
- All specialized indexes/search → consolidate as facets
- `concept_graph.py` → ADR-007
- `sentence.py` / `sentence_parser.py` → SUPERSEDE

---

## Phase D — Verification (P4)

| Requirement | Scope |
|-------------|-------|
| Unit tests | Every new facade + capability |
| Contract tests | Frozen API → canonical delegation |
| Integration tests | Facades in E2E pipeline |
| Determinism tests | Search, indexing, RAG context |
| Provenance tests | All new touchpoints |
| Full regression | 1219+ baseline — zero regressions |
| Static analysis | Ruff + Mypy PASS |
| `pdf_normalizer.py` test | Close known coverage gap |

---

## Phase E — Certification Update (P4)

| Deliverable | Action |
|-------------|--------|
| Update reconciliation registry | New dispositions for implemented items |
| Update certification readiness report | L2/L3 progress |
| Update deviation register | Approved deviations marked |
| Update traceability matrix | Facade mappings |
| BLOCK-013 handoff report | Qualification evidence |

**Do not claim FILE-LEVEL CERTIFIED 100% or PRODUCTION READY.**

---

## Scope Summary Table

| Phase | Items | New Code | Authorized |
|-------|-------|----------|------------|
| A — Governance | ADRs + gate approval | Docs only | After human review |
| B — Facades | 13 targets | ~15–20 files | After Phase A |
| C — Gaps | 2–8 selective | ~5–15 files | After Phase A; prioritized |
| D — Verification | All new code | Tests | With implementation |
| E — Certification | Docs | Updates | After D |

**Total estimated new implementation files:** 20–35 (not 67)

---

## Default Priority (Master Prompt §27)

```text
P0 — Governance / ADR closure          [Phase A]
P1 — Compatibility interfaces          [Phase B]
P2 — Genuine capability gaps             [Phase C selective]
P3 — Local RAG productionization         [NOT in BLOCK-013 — BLOCK-015/016]
P4 — Optional architectural expansion    [BLOCK-017+]
```

---

## Entry Criteria

- [ ] Governance plan approved
- [ ] Decision gate table approved (minimum: C, D, H batch + B facade items)
- [ ] ADR-011 approved
- [ ] ADR-001, 003, 008, 010 approved
- [ ] BLOCK-012 human freeze completed
- [ ] Explicit authorization: "Implement KG-BLOCK-013 Phase B" (or broader)

## Exit Criteria

- [ ] All Phase B facades implemented and tested
- [ ] Phase C items (as authorized) implemented and tested
- [ ] Full regression PASS
- [ ] Static analysis PASS
- [ ] Certification documents updated
- [ ] Handoff report produced
- [ ] No frozen block modifications

---

## Authorization Statement (Template)

```text
HUMAN TECHNICAL OWNER AUTHORIZATION — KG-BLOCK-013

Authorized phases: [ A / B / C / D / E ]
Authorized scope:   [ list specific COMPAT-IDs and gap items ]
Excluded:           [ explicit exclusions ]
Date:               ___________
Signature:          ___________
```

**UNTIL COMPLETED: NO IMPLEMENTATION**
