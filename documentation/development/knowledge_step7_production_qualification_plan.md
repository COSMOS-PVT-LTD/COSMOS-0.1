# Step 7 — Production Qualification Plan

## Objective

Define evidence required to advance from **PRODUCTION-CAPABLE** to **PRODUCTION-QUALIFIED** and **PRODUCTION-READY**.

## Qualification Dimensions

| Dimension | Evidence Required | Step 7 Status |
|-----------|-------------------|---------------|
| Functional | Pipeline ingest/query end-to-end | ✅ Unit + integration tests |
| Integration | W4 pipeline + W7 search + persistence | ✅ Integration qualification test |
| Security | Offline guard, no provider invocation | ✅ `test_step7_offline.py` |
| Reliability | Integrity checks, schema validation | ✅ Storage tests |
| Recovery | Invalidate/rebuild path | ✅ `RecoveryProcedure` tests |
| Performance | Benchmark harness exists | ⚠️ CHARACTERIZED (fixture scale only) |
| Persistence | JSON store round-trip | ✅ Storage tests |
| Upgradeability | Schema version gate | ✅ `SchemaMismatchError` |
| Provenance | Document fingerprints, graph digest | ✅ DocumentRecord + manifest |
| Lifecycle | Index BUILD/LOAD/VALIDATE/INVALIDATE/REBUILD | ✅ Index lifecycle tests |
| Offline execution | No network, provider_invoked=False | ✅ Offline tests |

## Test Suite Mapping

| Suite | Location | Coverage |
|-------|----------|----------|
| Storage | `tests/unit_tests/knowledge/storage/test_step7_storage.py` | Persist, integrity, schema |
| Embeddings | `tests/unit_tests/knowledge/embeddings/test_step7_embeddings.py` | Deterministic, dimensions |
| Production pipeline | `tests/unit_tests/knowledge/production/test_step7_production_pipeline.py` | Full ingest/query |
| Offline | `tests/unit_tests/knowledge/production/test_step7_offline.py` | Guard, no provider |
| Integration qualification | `tests/integration_tests/step7/test_production_qualification.py` | Golden doc E2E |

## Human Gates (§24)

| Gate | Requirement | Step 7 Action |
|------|-------------|---------------|
| Gate 1 | Persistence technology selection | JSON file store (additive, no frozen change) — **documented, awaiting human review** |
| Gate 2 | Production embedding model | Deterministic v1 (placeholder) — **awaiting human selection of neural backend** |
| Gate 3 | External dependencies | None introduced — **PASS** |
| Gate 4 | Frozen interface changes | None — **PASS** |
| Gate 5 | Production qualification | **STOP — not declared** |
| Gate 6 | Production readiness | **STOP — not declared** |

## Qualification Procedure

1. Run full regression (`pytest`) — target 0 failures
2. Run static analysis (`ruff`, `mypy`) on Step 7 packages
3. Run import smoke test
4. Execute integration qualification with golden fixture
5. Verify `provider_invoked=False` across all test paths
6. Human review of Gates 1, 2, 5, 6
7. Benchmark at production corpus scale (not yet done)
8. Sign-off by Technical Owner

## Pass Criteria for PRODUCTION-QUALIFIED

All dimensions green at production scale, human gates 1–6 approved, zero regressions, frozen boundaries intact.

## Current Verdict

**Plan complete. Qualification NOT executed to production scale. Awaiting human gates.**
