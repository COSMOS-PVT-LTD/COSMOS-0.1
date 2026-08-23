# KG-BLOCK-013 Phase A — Decision Ledger

**Document ID:** COSMOS-KG-B013-PHASE-A-LEDGER-001  
**Date:** 2026-08-23  
**Authority:** Human Technical Owner — Tk Nayak  
**Machine-readable:** `kg_block_013_phase_a_decision_ledger.json`

---

| Decision ID | Subject | Decision | Authority | Status | Affected Block |
|-------------|---------|----------|-----------|--------|----------------|
| KG-DEC-013A-001 | ADR-001 closure | Graph-primary authoritative | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-002 | ADR-003 closure | W* subpackages canonical | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-003 | ADR-008 closure | OntologyRegistry canonical | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-004 | ADR-010 closure | Controlled RAG supersedes recommender | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-005 | ADR-011 strategy | Facades approved; impl deferred Phase B | Tk Nayak | **APPROVED — PHASE-B READY** | Phase B |
| KG-DEC-013A-006 | ADR-012 closure | BLOCK-012 freeze recorded | Tk Nayak | **CLOSED** | BLOCK-012 |
| KG-DEC-013A-007 | DEV-001 closure | Graph-primary deviation closed | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-008 | DEV-004 closure | Subpackage deviation closed | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-009 | DEV-007 closure | Ontology deviation closed | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-010 | DEV-009 closure | Controlled RAG deviation closed | Tk Nayak | **CLOSED** | Phase A |
| KG-DEC-013A-011 | DEV-002 exporters | Deferred — ADR-004 | — | **OPEN** | BLOCK-014 |
| KG-DEC-013A-012 | DEV-003 models | Deferred — ADR-002 | — | **OPEN** | BLOCK-017 |
| KG-DEC-013A-013 | DEV-008 embeddings | Deferred — ADR-009 | — | **OPEN** | BLOCK-016 |
| KG-DEC-013A-014 | DEV-010 pdf_normalizer | Test gap deferred | — | **OPEN** | Phase C |
| KG-DEC-013A-015 | DG-033 concept_graph | ADR-007 required | — | **REQUIRES HUMAN DECISION** | — |
| KG-DEC-013A-016 | DG-067 empirical_relation | ADR-006 required | — | **REQUIRES HUMAN DECISION** | — |
| KG-DEC-013A-017 | DG-154 text_utils | Phase C authorization required | — | **REQUIRES HUMAN DECISION** | Phase C |
| KG-DEC-013A-018 | Phase A prohibition | No knowledge/ implementation | Master prompt | **CLOSED** | Phase A |

---

## Decision Gate Summary (DG-001 → DG-199)

| Classification | Count |
|----------------|-------|
| CLOSED | 153 |
| DEFERRED | 43 |
| REQUIRES HUMAN DECISION | 3 |

### REQUIRES HUMAN DECISION

| DG-ID | Path | Recommended |
|-------|------|-------------|
| DG-033 | `knowledge/graph/concept_graph.py` | CONSOLIDATE — ADR-007 |
| DG-067 | `knowledge/models/empirical_relation.py` | CONSOLIDATE — ADR-006 |
| DG-154 | `knowledge/utils/text_utils.py` | IMPLEMENT — Phase C scope |

### DEFERRED (implementation authorization required)

- **13 items** — COMPATIBILITY FACADE (Phase B)
- **30 items** — IMPLEMENT (exporters, loaders, domain models, validators — Phases C/D/E)

---

## ADR Status After Phase A

| ADR | Status |
|-----|--------|
| ADR-001 | **CLOSED** |
| ADR-002 | PENDING |
| ADR-003 | **CLOSED** |
| ADR-004 | PENDING |
| ADR-005 | PENDING |
| ADR-006 | PENDING |
| ADR-007 | PENDING |
| ADR-008 | **CLOSED** |
| ADR-009 | PENDING |
| ADR-010 | **CLOSED** |
| ADR-011 | **APPROVED — PHASE-B READY** |
| ADR-012 | **CLOSED** |
