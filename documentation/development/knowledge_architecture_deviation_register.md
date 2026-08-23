# Knowledge Architecture Deviation Register

**Document ID:** COSMOS-KG-DEVIATION-REG-003  
**Last updated:** 2026-08-23 (KG-BLOCK-013 Phase E certification closure)  
**Type:** GOVERNED — approved deviations explicitly recorded

---

## Purpose

Formal record of all deviations between frozen Part-3 architecture
(`documentation/COSMOS_0.1_FREEZED.md`) and current repository state.

---

## Severity Definitions

| Severity | Meaning |
|----------|---------|
| CRITICAL | Breaks architectural trust boundary or frozen contract |
| HIGH | Required frozen capability absent with no equivalent |
| MEDIUM | Relocated/consolidated without formal approval record |
| LOW | Deferred capability with documented KG plan |
| INFORMATIONAL | Intentional evolution, equivalent exists |

---

## Deviations

### DEV-001 — Repository path: `repositories/` vs `repository/`

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Frozen | `knowledge/repositories/` (16 entity-specific repos) |
| Current | `knowledge/repository/` (4 files: source registry, source repo, document repo) |
| Impact | Entity-specific persistence layer not implemented at frozen paths |
| Evidence | Freeze ledger; reconciliation registry |
| Resolution | Graph-primary architecture per ADR-001 |
| **Status** | **CLOSED** |
| **Closure date** | 2026-08-23 (KG-BLOCK-013 Phase A) |
| **Why not literal frozen tree** | Graph is authoritative relationship model; plural repos would duplicate authority |
| **Capability preserved** | Document/source persistence + graph construction/query |
| **Compatibility** | Facades only if external contract requires (ADR-011) |
| **Migration path** | Optional persistence layer in BLOCK-015 — not plural repos |

### DEV-002 — Missing `knowledge/exporters/` package

| Field | Value |
|-------|-------|
| Severity | **HIGH** |
| Frozen | 7 exporter modules |
| Current | None |
| Impact | No canonical export path for knowledge artifacts |
| Evidence | Part-3 tree; no `knowledge/exporters/` directory |
| Resolution | Defer to BLOCK-014 or supersede per ADR-004 (pending) |
| **Status** | **OPEN** |

### DEV-003 — Model consolidation vs 36-file tree

| Field | Value |
|-------|-------|
| Severity | **MEDIUM** |
| Frozen | 36 files under `knowledge/models/` |
| Current | 11 files; concepts in parser/graph/ontology layers |
| Impact | File-level non-compliance; capability partially preserved |
| Evidence | `knowledge_models_gap_analysis.md` |
| Resolution | Awaiting ADR-002 approval |
| **Status** | **OPEN — ADR-002 pending** |

### DEV-004 — W3/W4/W7/W8/W10/W11 subpackages

| Field | Value |
|-------|-------|
| Severity | **INFORMATIONAL** |
| Frozen | Flat module names per layer |
| Current | Block-scoped subpackages (`w3/`, `w4/`, etc.) |
| Impact | Positive — superior modularity and freeze boundaries |
| Evidence | BLOCK-006→011 implementation records |
| Resolution | Canonical subpackage architecture per ADR-003 |
| **Status** | **CLOSED** |
| **Closure date** | 2026-08-23 (KG-BLOCK-013 Phase A) |
| **Authority** | Human Technical Owner — Tk Nayak |
| **Basis** | ADR-003 (2026-08-23) |

### DEV-005 — `knowledge/source/` not in Part-3 tree

| Field | Value |
|-------|-------|
| Severity | **INFORMATIONAL** |
| Frozen | Not listed (integrity in utils) |
| Current | `knowledge/source/` vault + integrity (5 files) |
| Impact | W1 capability implemented outside frozen tree |
| Evidence | BLOCK-005 freeze; KG-006/008 |
| Resolution | W1 extension — documented in reconciliation |
| **Status** | **ACCEPTED** (no ADR required — informational extension) |

### DEV-006 — `knowledge/ingestion_adapters/` not in Part-3 tree

| Field | Value |
|-------|-------|
| Severity | **INFORMATIONAL** |
| Frozen | Loaders under `knowledge/ingestion/` |
| Current | Separate `ingestion_adapters/` package (11 files) |
| Impact | Cleaner W2 boundary |
| Evidence | Maps to frozen loaders via relocation |
| Resolution | Accepted relocation; facades per ADR-011 when needed |
| **Status** | **ACCEPTED** |

### DEV-007 — Static ontology domain modules missing

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Frozen | `ontology/propulsion.py`, `thermodynamics.py`, etc. (15 files) |
| Current | `ontology/registry.py` + `taxonomy.py` |
| Impact | Domain terms registered dynamically vs static modules |
| Evidence | SUPERSEDED in traceability matrix |
| Resolution | Dynamic registry per ADR-008 |
| **Status** | **CLOSED** |
| **Closure date** | 2026-08-23 (KG-BLOCK-013 Phase A) |
| **Authority** | Human Technical Owner — Tk Nayak |
| **Basis** | ADR-008 (2026-08-23) |

### DEV-008 — Semantic search without production embeddings

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Frozen | `semantic_index.py` with embedding backend implied |
| Current | Reference vectors in `indexing/w7/vector.py` |
| Impact | Not production semantic RAG |
| Evidence | BLOCK-010 engineering review |
| Resolution | Awaiting ADR-009 |
| **Status** | **OPEN — ADR-009 pending** |

### DEV-009 — Controlled RAG without LLM (intentional)

| Field | Value |
|-------|-------|
| Severity | **INFORMATIONAL** |
| Frozen | `recommendation_engine.py` in reasoning |
| Current | `interface/rag.py` — retrieval only, `provider_invoked=False` |
| Impact | Correct per KG-048 — controlled local RAG |
| Evidence | BLOCK-011/012 qualification |
| Resolution | Controlled RAG supersedes recommender per ADR-010 |
| **Status** | **CLOSED** |
| **Closure date** | 2026-08-23 (KG-BLOCK-013 Phase A) |
| **Authority** | Human Technical Owner — Tk Nayak |
| **Basis** | ADR-010 (2026-08-23) |

### DEV-010 — `parsers/pdf_normalizer.py` test coverage

| Field | Value |
|-------|-------|
| Severity | **LOW** |
| Frozen | `pdf_loader.py` |
| Current | `pdf_normalizer.py` — tested |
| Impact | PDF path lacked direct test coverage |
| Evidence | `test_parsers.py`, `test_pdf_normalizer_phase_c.py` |
| Resolution | Phase C test coverage added (GAP-C-003) |
| **Status** | **CLOSED** |
| **Closure date** | 2026-08-23 (KG-BLOCK-013 Phase E) |

---

## Summary

| Severity | Open | Closed | Accepted |
|----------|------|--------|----------|
| CRITICAL | 0 | 0 | 0 |
| HIGH | 1 | 0 | 0 |
| MEDIUM | 1 | 1 | 0 |
| LOW | 1 | 2 | 0 |
| INFORMATIONAL | 0 | 1 | 3 |

**No CRITICAL deviations.** Frozen BLOCK-001→012 interfaces remain intact.

---

## Approval Matrix

| DEV-ID | Basis | Approval Status |
|--------|-------|-----------------|
| DEV-001 | ADR-001 | **CLOSED** |
| DEV-002 | — | **OPEN** |
| DEV-003 | ADR-002 pending | **OPEN** |
| DEV-004 | ADR-003 | **CLOSED** |
| DEV-005 | Informational extension | **ACCEPTED** |
| DEV-006 | Relocation | **ACCEPTED** |
| DEV-007 | ADR-008 | **CLOSED** |
| DEV-008 | ADR-009 pending | **OPEN** |
| DEV-009 | ADR-010 | **CLOSED** |
| DEV-010 | DEV-010 | **CLOSED** |
