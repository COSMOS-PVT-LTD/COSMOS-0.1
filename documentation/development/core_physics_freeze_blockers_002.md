# COSMOS 0.1 — Core / Physics Freeze Blockers 002

**Document ID:** `CORE-PHYS-REVIEW-002-BLOCKERS`  
**Parent:** `documentation/development/core_physics_independent_vv_report_002.md`  
**Date:** 2026-09-01  
**Repository audited:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Scope:** CORE-001..005, PHYS-001..007, CORE-PHYS-INT-001 after CORE-PHYS-REMEDIATION-001  
**Code modified:** none

Freeze rule used: no open **S0/S1**. Every **S2** requires explicit fix or formal waiver. This re-audit reproduced evidence; it did not accept the remediation report on faith.

---

## Recommendation

```text
NOT READY — BLOCKING FINDINGS
```

S1 affine arithmetic is **closed**. One **new/reopened S2** remains undispositioned: Core imports Physics. One prior S2 remains a **waiver pending human signature**.

---

## Closed since REVIEW-001 (do not re-open without new evidence)

| ID | Independent close evidence |
|----|----------------------------|
| **CORE-002-AFFINE-001** | `0 °C → 273.15 K`; `100 °C → 373.15 K`; `100 °C − 0 °C → 100 K interval`; `0 °C + 100 °C → UnitError`; `25 °C × 3600 s → 1.07334e6` SI |
| **CORE-002-DUAL-UNIT-001** | `core/units.py` deprecated; `test_dual_unit_regression.py` matches registry factors |
| **CORE-003-GAMMA-001** | `validate_gamma(1.0)` raises `InvalidInputError` |
| **PHYS-002-FAILOPEN-001** | LOX @ 300 K: `.quantity` and `.require_valid()` raise; stored 1141 is diagnostic only |
| **PHYS-002-NIST-001** | Independent bands: LOX 1141, LH2 70.85, water 997 vs IAPWS 996.56 (rel 4.4e-4) |
| **PHYS-003-DUAL-001** | `species.py` declared computational authority; `propellants.py` legacy adapter |
| **PHYS-005-BARTZ-001** | `(D/R)^0.1 = 0.776799609716` for D=0.04 m, R=0.5 m; `h` scales by that factor |
| **PHYS-005-KG-001** | `knowledge/foundation/seed_corpus.py` CORR-BARTZ matches physics SI form |
| **PHYS-INT-CHAIN-001** | Relabeled smoke; hardcoded γ=1.2 documented as non-scientific |

---

## Blocking findings (must close before freeze)

### S1 — none

### S2 — fix or formal waiver

| ID | Component | Defect | Required close |
|----|-----------|--------|----------------|
| **CORE-003-LAYER-001** | `core/validation.py` → `physics.propulsion_validation` | Deprecated `validate_mixture_ratio` / `validate_expansion_ratio` lazily import Physics. This inverts the frozen layering (`core` must not depend on `physics`) and creates a latent import cycle with `validate_positive`. REVIEW-001 CORE-003-PROPULSION-001 is therefore **not fully closed**. | **Fix:** keep deprecated one-line validators entirely inside Core (no Physics import), or delete the wrappers. **Or** sign a formal waiver that joint 0.1 freeze permits these two stubs. Do not claim Core is an independent stable dependency while this import remains. |

---

## Formal waiver (not a scientific close)

| ID | File | Status | Remaining risk |
|----|------|--------|----------------|
| **PHYS-004-NUM-001** | `physics/contracts/PHYS-004-NUM-WAIVER.md` | Documented waiver; **“Pending human sign-off.”** | Inverse Mach / Prandtl–Meyer / θ–β–M use physics-local bisection. Results may change when `numerics/` lands. Closed-form Anderson identities do **not** depend on this path. |

No freeze that includes inverse compressible-flow solves should treat the fallback as the canonical Numerics implementation.

---

## Explicitly not freeze blockers (must not be misread as certified)

| Topic | Status after re-audit |
|-------|------------------------|
| Affine Celsius arithmetic | Closed. Interval vs absolute semantics are explicit. |
| Anderson γ=1.4 M=2 | Independent identities match to 0. |
| Peng–Robinson | Still fail-closed. |
| CEA executable | Still unbound. |
| MOC marching | Still not in physics. |
| MMPDS / fatigue / creep / film cooling | Unchanged honest stubs / handbook typicals. |
| Experimental / engine validation | Not demonstrated. |
| Integrated chain as engine analysis | Must not be claimed; smoke only. |
| Bartz without `curvature_radius` | Factor 1 by default; literature term omitted until R is passed. S3, not S2, because the equation exists and was independently verified when R is supplied. |
| In-repo Bartz pytest | Still tautological vs literature `h`; this re-audit supplied the independent declared-equation check. |
| `ModelEvaluation` | Method exists on fluid `PropertyEvaluation`; unused. S3. |

---

## Environment blocker (process, not science)

| ID | Issue |
|----|-------|
| **ENV-WORKSPACE-001** | Active Cursor workspace `/Users/vaibhavkumarn/Desktop/desktop files :07:07:2026/COSMOS_0.1` is still empty except `.cursor/`. Authoritative tree: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. |

---

## Minimum close-out to re-enter freeze review

1. Disposition **CORE-003-LAYER-001**: remove Physics imports from Core **or** sign a layering waiver.
2. Human signature on **PHYS-004-NUM-WAIVER.md** (or land `numerics.root_finding` and delete the fallback).
3. Re-run this re-audit’s independent cases: affine, Anderson M=2, LOX 300 K fail-closed, NASA7 O2 polynomial, Bartz `(D/R)^{0.1}` propagation, multiprocess hashes.
4. Point Cursor at the authoritative repository.

No waiver may convert:

- simplified default Bartz (R omitted) into Bartz 1957 with curvature,
- the smoke chain into engine analysis,
- NASA7 O2 Cp into CEA validation,
- handbook material values into MMPDS allowables.

---

```text
S0: 0
S1: 0
S2 open: 1 (CORE-003-LAYER-001)
S2 waived unsigned: 1 (PHYS-004-NUM-001)

NOT READY — BLOCKING FINDINGS
```
