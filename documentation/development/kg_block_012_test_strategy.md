# KG-BLOCK-012 Test Strategy

**Document ID:** COSMOS-KG-TEST-B012  
**Date:** 2026-08-23

---

## 1. Test Pyramid

```text
Unit Tests (frozen BLOCK-001→011)     — 1171 tests (unchanged)
    ↓
Contract Tests (W1→W11 boundaries)    — 10 tests
    ↓
Integration Tests (domain suites)     — 38 tests
    ↓
End-to-End (golden fixture)           — included above
    ↓
Failure/Recovery                      — 7 tests
    ↓
Performance Characterization          — 5 tests (ceilings, not optimization)
```

**Total BLOCK-012 additions:** 48 tests

---

## 2. Golden Fixture Strategy

- Deterministic markdown engineering document
- License-safe (`COSMOS-INTERNAL-TEST`)
- Contains materials, quantities, tables, equations, references, conflict notes
- Markdown normalization aligned with ingestion adapter before hashing

---

## 3. Determinism Strategy

- `to_mapping()` equality for repeated pipeline runs
- Graph digest equality under input-order reversal
- Evidence chain stable ordering by `target_id`
- No brittle file snapshots for non-contractual outputs

---

## 4. Failure Strategy

- Domain exceptions only (`SearchValidationError`, `IndexStaleError`, etc.)
- No silent success on missing provenance
- Stale index detection via live store binding
- Empty/minimal documents handled without crash

---

## 5. Security Strategy

- `provider_invoked == False` invariant
- `content_kind == "knowledge_evidence"` invariant
- AST inspection of ControlledRAGOrchestrator for forbidden imports
- Graph digest unchanged after interface payload build

---

## 6. Regression Policy

- Zero regressions against BLOCK-011 freeze baseline
- No frozen source file modifications
- All new code under `tests/integration_tests/kg_block012/`
