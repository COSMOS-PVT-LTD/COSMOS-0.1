# Knowledge Next Development Plan

**Document ID:** COSMOS-KG-NEXT-PLAN-002
**Date:** 2026-08-23
**Phase:** POST-RECONCILIATION PROPOSAL — not authorized for implementation

## Immediate (Human Actions)

1. Approve BLOCK-012 freeze
2. Review and approve ADR-001 through ADR-012
3. Approve deviation register entries

## Proposed Blocks (Post-Reconciliation Gate)

### KG-BLOCK-013 — Compatibility & Architecture Closure (Proposed)

- Implement approved compatibility facades (COMPAT-001→006)
- Resolve F-disposition files via ADRs
- No changes to frozen BLOCK-001→011 modules

### KG-BLOCK-014 — Export & Handoff (Proposed)

- `knowledge/exporters/` package (if ADR-004 approves implementation)
- Markdown/JSON/YAML export with provenance

### KG-BLOCK-015 — Persistence Layer (Proposed)

- Entity repositories OR approved graph-primary persistence
- Depends on ADR-001

### KG-BLOCK-016 — Production Embeddings (Proposed)

- Local embedding backend for semantic index
- Depends on ADR-009

### KG-BLOCK-017 — Domain Model Expansion (Proposed)

- Tier 3 missing domain models (if ADR-002 approves expansion vs consolidation)

---

## Reconciliation Metrics Baseline

| Metric | Value |
|--------|-------|
| E MISSING_REQUIRED | 67 |
| F MISSING_DECISION | 5 |
| Capability addressed | 103/175 |

**Implementation gate remains CLOSED until ADR approval.**