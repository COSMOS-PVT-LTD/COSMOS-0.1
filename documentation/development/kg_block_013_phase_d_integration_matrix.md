# KG-BLOCK-013 Phase D — Integration Matrix

**Document ID:** COSMOS-KG-B013-PHASE-D-MATRIX-001  
**Date:** 2026-08-23

| Test Area | Test | Expected | Actual | Evidence | Result |
|-----------|------|----------|--------|----------|--------|
| E2E | W1→W11 golden pipeline | Full artifact chain | PASS | `test_pipeline_e2e.py` (48 tests) | **PASS** |
| E2E | Contract boundaries W1–W11 | All 10 boundaries | PASS | `test_contract_boundaries.py` | **PASS** |
| E2E | Phase-B compat pipeline parity | Digest alignment | PASS | `test_compat_integration.py` | **PASS** |
| Provenance | Source→artifact→document chain | Traceable IDs | PASS | `test_pipeline_provenance.py` | **PASS** |
| Provenance | Validation finding provenance | Anchors present | PASS | `test_w9_validation.py`, `test_phase_c_validation.py` | **PASS** |
| Lifecycle | No auto CANDIDATE→APPROVED | Rejection on APPROVED | PASS | `test_schema_validation_rejects_premature_approval` | **PASS** |
| Lifecycle | Lifecycle state preservation | Governed transitions | PASS | `test_pipeline_lifecycle.py` | **PASS** |
| Determinism | Pipeline repeatability | Identical digests | PASS | `test_pipeline_determinism.py`, `test_compat_pipeline.py` | **PASS** |
| Determinism | Extended validation digest | Stable report | PASS | `test_validate_context_extended_is_deterministic` | **PASS** |
| Security/IP | No provider invocation | `provider_invoked=False` | PASS | `test_pipeline_security.py`, compat tests | **PASS** |
| Security/IP | Local-only processing | No network required | PASS | Architecture audit | **PASS** |
| Compatibility | COMPAT-001 ingestion | Delegates to adapters | PASS | `test_compat_ingestion.py` (5) | **PASS** |
| Compatibility | COMPAT-002 search | Delegates to W8/engine | PASS | `test_compat_search.py` (5) | **PASS** |
| Compatibility | COMPAT-003 indexing | Alias to canonical | PASS | `test_compat_indexing.py` (6) | **PASS** |
| Compatibility | COMPAT-004 graph manager | Construct+query | PASS | `test_compat_graph.py` (4) | **PASS** |
| Compatibility | COMPAT-005 ontology manager | Registry delegate | PASS | `test_compat_ontology.py` (3) | **PASS** |
| Compatibility | COMPAT-006 pipeline | W1→W11 orchestration | PASS | `test_compat_pipeline.py` (3) | **PASS** |
| Phase-C | GAP-C-001 citation validator | Unresolved/orphan detection | PASS | `test_phase_c_validation.py` | **PASS** |
| Phase-C | GAP-C-002 ambiguity detector | Section/claim warnings | PASS | `test_phase_c_validation.py` | **PASS** |
| Phase-C | Extended W9 orchestration | Merged findings | PASS | `test_validate_context_extended_*` | **PASS** |
| Phase-C | GAP-C-003 pdf_normalizer | Edge-case coverage | PASS | `test_pdf_normalizer_phase_c.py` | **PASS** |
| Failure/Recovery | Adapter errors | Typed exceptions | PASS | `test_pipeline_failure_recovery.py` | **PASS** |
| Failure/Recovery | Invalid ingestion/search | Rejection | PASS | `test_block005_hardening.py`, W8 tests | **PASS** |
| Performance | Golden fixture ceilings | Within reference bounds | PASS | `test_pipeline_performance.py` (5) | **CHARACTERIZED** |
| Import | Package smoke (24 modules) | No import errors | PASS | Phase D import smoke | **PASS** |
| Static | Mypy knowledge | 0 errors | PASS | `mypy knowledge` | **PASS** |
| Static | Ruff knowledge | Pre-existing only | 4 D2 findings | `ruff check knowledge` | **PASS WITH FINDINGS** |
