# CORE / PHYSICS Remediation Report — CORE-PHYS-REMEDIATION-001

**Date:** 2026-09-01  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Agent:** Computational Kernel Remediation Agent

---

## 1. Findings reviewed

All S1 and S2 items from `core_physics_independent_vv_report.md` and `core_physics_freeze_blockers.md` were reviewed against the S2 disposition register.

---

## 2. Changes made

### S1 — CORE-002-AFFINE-001 (FIXED)

Implemented absolute vs interval temperature semantics in `core/quantity.py`:

| Operation | Result |
|-----------|--------|
| `0 °C → SI` | 273.15 K |
| `100 °C − 0 °C` | 100 K interval |
| `0 °C + 100 °C` | `UnitError` |
| `20 °C + 10 K interval` | 30 °C |
| `25 °C × 3600 s` | thermodynamic SI product |

Added `QuantityKind`, `temperature_interval()`, `Unit.is_affine`.

### S2 dispositions

| ID | Disposition | Evidence |
|----|-------------|----------|
| CORE-002-DUAL-UNIT-001 | **FIXED** | Deprecated `core/units.py`; regression test `test_dual_unit_regression.py` |
| CORE-003-GAMMA-001 | **FIXED** | `validate_gamma` rejects `γ ≤ 1`; test added |
| CORE-003-PROPULSION-001 | **FIXED** | `physics/propulsion_validation.py`; core wrappers deprecated |
| PHYS-002-FAILOPEN-001 | **FIXED** | `PropertyEvaluation.quantity` fail-closed; `stored_quantity` for diagnostics |
| PHYS-002-NIST-001 | **FIXED** | `test_fluid_nist_references.py` with independent reference bands |
| PHYS-003-DUAL-001 | **FIXED** | Authority documented in `species.py` / `propellants.py` |
| PHYS-004-NUM-001 | **FORMALLY WAIVED** | `physics/contracts/PHYS-004-NUM-WAIVER.md` |
| PHYS-005-BARTZ-001 | **FIXED** | Curvature factor `(D/R)^0.1` via `curvature_radius` parameter |
| PHYS-005-CIRC-001 | **FIXED** | Independent worked example in `test_anderson_bartz.py` |
| PHYS-005-KG-001 | **FIXED** | `seed_corpus.py` equation aligned with physics SI executable form |
| PHYS-INT-CHAIN-001 | **FIXED** | Renamed to smoke test; docstring declares non-scientific scope |
| PHYS-INT-PROV-001 | **FIXED** | `PropertyEvaluation.to_model_evaluation()` wired |

---

## 3. Files changed

**Core:** `core/quantity.py`, `core/unit.py`, `core/units.py`, `core/validation.py`  
**Physics:** `physics/fluids/fluid_properties.py`, `physics/heat_transfer/bartz.py`, `physics/propulsion_validation.py`, `physics/thermochemistry/species.py`, `physics/thermochemistry/propellants.py`, `physics/contracts/PHYS-004-NUM-WAIVER.md`  
**Knowledge:** `knowledge/foundation/seed_corpus.py`  
**Tests:** `test_affine_temperature.py`, `test_dual_unit_regression.py`, `test_fluid_nist_references.py`, updates to `test_validation.py`, `test_fluids.py`, `test_anderson_bartz.py`, `test_physics_chain.py`

---

## 4. Tests added

- `tests/unit_tests/core/test_affine_temperature.py` (14 cases)
- `tests/unit_tests/core/test_dual_unit_regression.py`
- `tests/benchmark_tests/test_fluid_nist_references.py`

---

## 5. Tests executed

```text
510 passed (CORE+PHYS audit scope)
```

Includes independent audit cases: affine arithmetic, Anderson γ=1.4 M=2, LOX fail-closed, Bartz curvature, chain smoke, hash/serialization regressions.

---

## 6. Benchmark results

- Anderson isentropic/shock: unchanged, passing
- Bartz independent reference: `expected_h` computed outside implementation matches COSMOS
- NASA7 O2 Cp@300K: passing
- NIST reference bands: LOX/LH2/water within documented tolerances

---

## 7. S1 closure evidence

Independent execution confirms audit regression cases no longer produce silent wrong values:

```text
(0 °C + 100 °C)  → UnitError
(100 °C − 0 °C)  → 100 K interval
(25 °C × 3600 s).to_si() → 1.07334e6
```

---

## 8. S2 dispositions

All twelve S2 items are **FIXED** or **FORMALLY WAIVED** (PHYS-004-NUM-001 only). None remain OPEN.

---

## 9. Remaining S3/S4

Not expanded in this remediation (per directive §17): CFD/GUI exception names in core, fracture.py coverage, assumption hash ordering, etc.

---

## 10. Architecture impact

No package restructuring. Additive semantics on `Quantity`; physics fail-closed behavior; Bartz API gains optional `curvature_radius`.

---

## 11. Compatibility impact

- `PropertyEvaluation.quantity` now raises when invalid (breaking for callers that read `.quantity` on OUT_OF_RANGE; use `stored_quantity`)
- `validate_gamma(1.0)` now raises (aligns with physics)
- `core/units.py` deprecated but functional
- Bartz `curvature_radius=None` preserves prior h (factor=1)

---

## 12. Scientific limitations

- Integrated chain remains a **smoke test** with hardcoded γ=1.2
- Fluid records remain reference-point data, not predictive EOS
- CEA still interface-only
- Materials remain room-temperature scoped

---

## 13. Determinism results

No regressions observed in hash/serialization tests; chain smoke test remains deterministic.

---

## 14. Freeze readiness

S1 closed. S2 dispositioned. Human independent re-audit recommended before freeze sign-off.

---

REMEDIATION COMPLETE — READY FOR INDEPENDENT RE-AUDIT
