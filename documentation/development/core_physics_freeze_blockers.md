# COSMOS 0.1 — Core / Physics Freeze Blockers

**Document ID:** `CORE-PHYS-REVIEW-001-BLOCKERS`  
**Parent:** `documentation/development/core_physics_independent_vv_report.md`  
**Date:** 2026-09-01  
**Repository audited:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Scope:** CORE-001..005, PHYS-001..007, CORE-PHYS-INT-001  
**Code modified:** none

Freeze rule used: no open **S0/S1**. Every **S2** requires explicit fix or formal waiver.

---

## Recommendation

```text
NOT READY — BLOCKING FINDINGS
```

One S1 correctness defect is open on the Core `Quantity` type. Several S2 items remain undispositioned.

---

## Blocking findings (must close before freeze)

### S1 — mandatory fix

| ID | Component | One-line defect | Required close |
|----|-----------|-----------------|----------------|
| **CORE-002-AFFINE-001** | `core/quantity.py`, `core/unit.py` | Affine Celsius arithmetic is silently wrong. Independent run: `0 °C + 100 °C` → **646.3 K**; `100 °C − 0 °C` stored as **−173.15 °C**. Multiplication drops `si_offset`. | Forbid affine-unit `+ − × ÷` **or** implement absolute vs interval algebra. Add tests. Kelvin-only physics today does **not** excuse freezing a broken public `Quantity` API. |

### S2 — fix or formal waiver

| ID | Component | Defect | Suggested disposition |
|----|-----------|--------|------------------------|
| **CORE-002-DUAL-UNIT-001** | `core/units.py` vs `core/unit.py` | Two unit authorities. Factors currently match (`psi` = 6894.757293168361) but drift is unguarded. Physics does not import legacy helpers. | Deprecate `core/units.py`; single registry; or freeze with a written dual-system contract. |
| **CORE-003-GAMMA-001** | `core/validation.py` | `validate_gamma(1.0)` succeeds. γ = 1 is singular for isentropic/shock relations. Physics `require_gamma` rejects it. | Core: `1 < γ ≤ 3`, or rename the Core helper and keep physics as the gasdynamic gate. |
| **CORE-003-PROPULSION-001** | `core/validation.py` | `validate_mixture_ratio`, `validate_expansion_ratio`, rocket docstrings live in Core. | Move to physics or freeze as legacy-compat with deprecation. |
| **PHYS-002-FAILOPEN-001** | `physics/fluids/fluid_properties.py` | `evaluate_record` at invalid T still returns a plausible number (`LOX` at 300 K → **1141 kg/m³**, `OUT_OF_RANGE`). `require_valid()` raises; `.quantity` does not. | Fail-closed by default, or make `.quantity` inaccessible unless `VALID`. |
| **PHYS-002-NIST-001** | `physics/fluids/records.py`, tests | Cryogenic densities cite NIST; tests assert the same hardcoded constants. No independent table check. | Add sourced benchmark values (even one point each for LOX, LH2, water). |
| **PHYS-003-DUAL-001** | `species.py` vs `propellants.py` | Two thermochemistry authorities. New NASA7 registry vs legacy propellant/CEA-named DB. | Declare one API as authoritative; isolate the other as adapter/legacy. |
| **PHYS-004-NUM-001** | `physics/contracts/numerics_port.py` | Temporary bisection lives in physics (`numerics/` absent). Documented in `NUM-CONTRACT-ISSUE.md`. | Waive as temporary port **or** land `numerics.root_finding.bisection` and delete the fallback. |
| **PHYS-005-BARTZ-001** | `physics/heat_transfer/bartz.py` | Named Bartz SI form omits `(D_t/R)^{0.1}`. Independent example `D_t=0.04 m`, `R=0.5 m` → factor **0.777** (~22% h bias vs full Bartz). | Add curvature term **or** freeze only as `PHYS-005.bartz.nusselt_si` (no curvature) with a waiver. |
| **PHYS-005-CIRC-001** | `tests/benchmark_tests/test_anderson_bartz.py` | Bartz test reconstructs `h` from the same `Nu·k/D·σ` identity. | Replace with an independent worked example / published dimensionless check. |
| **PHYS-005-KG-001** | `knowledge/foundation/seed_corpus.py` vs `bartz.py` | Knowledge seed stores full Bartz `*(Dt/R)**0.1`; physics does not. Violates single computational authority. | Align knowledge citation with the frozen physics model. |
| **PHYS-INT-CHAIN-001** | `tests/validation_tests/test_physics_chain.py` | Chain uses hardcoded **γ = 1.2**, Bartz at **exit Mach** with **chamber p** and throat-scale D, yield at **300 K** vs wall **800 K**. Deterministic, not thermochemically consistent. | Relabel as smoke chain **or** derive γ/M/c* from one state. |
| **PHYS-INT-PROV-001** | `physics/model.py` | `ModelEvaluation` is defined and unused. Numeric results lack bound inputs. | Wire an evaluation envelope, or waive provenance depth for v0.1. |

---

## Explicitly not freeze blockers (must not be misread as certified)

These are in-scope limitations that are **honestly declared**. They block a *capability claim*, not this foundation freeze, provided the freeze text does not overclaim.

| Topic | Status |
|-------|--------|
| Peng–Robinson cubic EOS | Fail-closed (`InsufficientDataError`). Correct. |
| CEA executable / RocketCEA adapter | Interface only. `run_thermochemistry()` raises without an engine. |
| MOC marching | Not in physics. `generate_contour()` raises. |
| MMPDS / fatigue / creep / film cooling | Interfaces or handbook typicals; not certified allowables. |
| Experimental / engine / CEA validation | Not demonstrated. Handoff is accurate. |
| Integer Core dimensions / `K_I` as `float` | Documented scope limit. Fracture untested (S3). |
| Missing `numerics/`, `engineering/`, other 24-package dirs | Out of **this** CORE+PHYS computational freeze. Track separately. Do not treat CORE+PHYS freeze as whole-architecture freeze. |

---

## Environment blocker (process, not science)

| ID | Issue |
|----|-------|
| **ENV-WORKSPACE-001** | Active Cursor workspace `/Users/vaibhavkumarn/Desktop/desktop files :07:07:2026/COSMOS_0.1` contains only `.cursor/`. Authoritative tree is `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`. Do not maintain two sources of truth. |

---

## Minimum close-out to re-enter freeze review

1. Fix **CORE-002-AFFINE-001** and add affine arithmetic tests (including the two independent cases above).
2. Disposition every S2 row: **fix** or **signed waiver** with remaining risk.
3. Re-run this audit’s independent cases (affine, Anderson M=2, LOX fail-open, Bartz curvature, chain hashes, CEA unbound).
4. Point the Cursor workspace at the authoritative repository.

No S2 waiver may silently convert a simplified Bartz, a dual thermochemistry API, or a fail-open property lookup into a claim of full Bartz / CEA / NIST-validated fluids.
