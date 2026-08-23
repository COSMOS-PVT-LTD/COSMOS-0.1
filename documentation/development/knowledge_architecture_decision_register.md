# Knowledge Architecture Decision Register

**Document ID:** COSMOS-KG-ADR-REG-003  
**Last updated:** 2026-08-23 (KG-BLOCK-013 Phase A closure)  
**Authority:** Human Technical Owner — Tk Nayak

---

## Summary

| ADR | Status |
|-----|--------|
| ADR-001 | **CLOSED** |
| ADR-003 | **CLOSED** |
| ADR-008 | **CLOSED** |
| ADR-010 | **CLOSED** |
| ADR-011 | **APPROVED — PHASE-B READY** |
| ADR-012 | **CLOSED** |
| ADR-002, 004–007, 009 | **PENDING** |

---

## ADR-001 — Graph-primary vs plural repositories

| Field | Value |
|-------|-------|
| **Status** | **CLOSED** (Phase A — 2026-08-23) |
| **Authorization date** | 2026-08-23 |
| **Authority** | Human Technical Owner — Tk Nayak |
| **Decision** | Graph-oriented knowledge architecture is authoritative; do not recreate 15 legacy entity repository files |
| **Closure evidence** | `kg_block_013_phase_a_governance_report.md`; DEV-001 CLOSED |
| **Consequences** | 14 frozen `repositories/*_repository.py` files marked REMOVE FROM ARCHITECTURE; persistence remains future concern (BLOCK-015) |
| **Implementation constraints** | No entity repo implementation without separate authorization; compatibility facades only if external contract requires |
| **Affected areas** | `knowledge/repository/`, `knowledge/graph/`, deviation DEV-001 |

---

## ADR-003 — Subpackage evolution strategy (W3/W4/W7/W8/W10/W11)

| Field | Value |
|-------|-------|
| **Status** | **CLOSED** (Phase A — 2026-08-23) |
| **Rationale** | Superior modularity, provenance, testability, and block freeze boundaries vs flat Part-3 tree |
| **Consequences** | Do not flatten `parsers/w3/`, `extraction/w4/`, `indexing/w7/`, `search/w8/`, `reasoning/w10/`, `interface/` |
| **Implementation constraints** | Future compatibility via explicit facades (ADR-011) when justified; no path-symmetry renames |
| **Affected areas** | All W3–W11 packages, deviation DEV-004 |

---

## ADR-008 — Dynamic ontology registry

| Field | Value |
|-------|-------|
| **Status** | **CLOSED** (Phase A — 2026-08-23) |
| **Rationale** | Registry supports deterministic identity, aliases, taxonomy, validation without 15 static files |
| **Consequences** | Do not recreate `ontology/propulsion.py` etc.; domain packs may populate registry in future blocks |
| **Implementation constraints** | Preserve deterministic identity, canonicalization, aliases, taxonomy, relationship rules, provenance, validation |
| **Affected areas** | `knowledge/ontology/`, 14 superseded domain files, deviation DEV-007 |

---

## ADR-010 — Controlled RAG supersedes recommendation engine

| Field | Value |
|-------|-------|
| **Status** | **CLOSED** (Phase A — 2026-08-23) |
| **Rationale** | Preserves trust boundary: retrieval → validation → evidence → reasoning → controlled context; no auto-promotion |
| **Consequences** | Do not restore autonomous recommender; `provider_invoked=False` remains intentional |
| **Implementation constraints** | No mandatory LLM/cloud; no candidate-to-fact promotion; no silent conflict resolution |
| **Affected areas** | `knowledge/interface/rag.py`, `knowledge/reasoning/`, deviation DEV-009 |

---

## ADR-011 — Compatibility facade strategy

| Field | Value |
|-------|-------|
| **Status** | **APPROVED — PHASE-B READY** (implementation not authorized) |
| **Rationale** | Preserves frozen contracts without duplicate implementations (COMPAT-001→006 plan) |
| **Consequences** | Facades may be implemented in KG-BLOCK-013 **only after separate implementation authorization** |
| **Implementation constraints** | Delegate-only; tested; provenance-preserving; deterministic; no duplicate models or business logic |
| **Affected areas** | Ingestion loaders, search, indexing, graph manager, ontology manager, pipelines |

---

## ADR-012 — BLOCK-012 freeze

| Field | Value |
|-------|-------|
| **Status** | **CLOSED** (Phase A — 2026-08-23) |
| **Rationale** | 1219 passed, 5 skipped; E2E + provenance + lifecycle + determinism + security + controlled RAG verified |
| **Consequences** | BLOCK-012 integration test layer configuration-controlled; no production readiness claim |
| **Implementation constraints** | Do not modify frozen BLOCK-001→011; qualification evidence preserved |
| **Affected areas** | `tests/integration_tests/kg_block012/`, `batch_status.json`, freeze ledger |

---

## Pending ADRs (not approved by this gate)

| ADR-ID | Topic | Status |
|--------|-------|--------|
| ADR-002 | Model consolidation vs 36-file tree | **PENDING** |
| ADR-004 | Exporters package | **PENDING** |
| ADR-005 | Sentence-level parsing | **PENDING** |
| ADR-006 | Empirical relation model | **PENDING** |
| ADR-007 | Concept graph | **PENDING** |
| ADR-009 | Semantic embeddings (production) | **PENDING** |

---

**Note:** Approved ADRs recorded per human authorization. Unrelated ADRs remain pending.
