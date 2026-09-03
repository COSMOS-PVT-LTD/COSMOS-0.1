# COSMOS 0.1 — Core + Physics Frozen Baseline

**Document ID:** `CORE-PHYSICS-FROZEN-BASELINE-001`  
**Freeze date:** 2026-09-03  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Authority:** Human freeze approval recorded on PHYS-004-NUM waiver  

```text
COSMOS_0.1 Core + Physics Frozen Baseline
```

> Freeze the baseline, not the future.

---

## Identity

| Field | Value |
|-------|--------|
| Repository commit (at freeze record creation) | `8ec73e695820e5a8f1a62588af7f0d3db6a42f40` |
| Software version | `COSMOS_VERSION = 0.1.0` |
| Core API / schema | `1.0.0` / `1.0.0` |
| Physics schema | `0.1.0` |
| Python/environment | CPython 3.x on Darwin (developer machine) |
| Freeze tag (optional) | `COSMOS_0.1_CORE_PHYSICS_FROZEN` — create only if/when requested by project owner |

---

## Waiver

| Item | Status |
|------|--------|
| PHYS-004-NUM-001 | **FORMALLY APPROVED WAIVER (PATH A)** |
| File | `physics/contracts/PHYS-004-NUM-WAIVER.md` |
| Approver | TK NAYAK — CEO, CTO, Chief propulsion scientist |
| Approval date | 2026-09-03 |
| Decision | APPROVED for temporary bounded bisection on documented PHYS-004 inverses only |

---

## Architecture constraints (frozen)

```text
physics ───────► core
core ──X───────► physics
gui ──X───────► physics (presentation must use application/API adapters)
```

- Core remains independently importable.
- AST + runtime layer tests in `tests/unit_tests/core/test_core_layer_independence.py` protect Core independence.
- Physics owns physical models; Numerics owns numerical algorithms (canonical package deferred).
- Knowledge is not a second solver.

---

## Model / numerical baseline

| Domain | Baseline |
|--------|----------|
| Thermodynamics | Ideal-gas / first–second law foundation; real-gas interfaces fail-closed |
| Fluids | Sourced reference-point records; fail-closed out of range |
| Thermochemistry | NASA7 species registry authoritative; CEA interface-only |
| Compressible flow | Anderson closed-form; inverses via `numerics_port` PATH A |
| Heat transfer | SI Bartz with optional `(D/R)^0.1` |
| Materials | Room-temperature handbook windows; not MMPDS |
| Solid mechanics | Constitutive relations; not design codes |
| Numerics | Temporary `_fallback_bisection` for Area–Mach / P–M / θ–β–M only |

Critical regression locks include:

- Affine: `0 °C → 273.15 K`; `100 °C − 0 °C → 100 K interval`; absolute °C add rejected  
- Anderson γ=1.4, M=2: `p0/p = 7.824449066867263`, `A/A* = 1.6875`, NS identities  
- LOX @ 300 K fail-closed  
- NASA7 O2 Cp(300 K) ≈ 29.388071132483972 J/(mol·K)  
- Bartz curvature factor for D=0.04 m, R=0.5 m = 0.7767996097157338  
- Canonical hash determinism across `PYTHONHASHSEED`

---

## Known limitations

- Experimental / engine / CEA validation **not** claimed  
- MMPDS / certified allowables **not** claimed  
- Integrated physics chain is **smoke**, not scientific engine analysis  
- PATH A bisection may change when canonical `numerics/` lands  
- Peng–Robinson / film cooling / creep / fatigue remain deferred interfaces  

---

## Deferred work

1. Canonical `numerics/root_finding/bisection` → remove fallback → close waiver  
2. CEA adapter outside Physics compute authority  
3. Temperature-dependent material allowables  
4. Broader Physics → GUI domains beyond Phase-1 compressible slice  

---

## Future upgrade policy

See `documentation/development/core_physics_future_upgrade_policy_001.md`.

Significant model changes must be versioned extensions with verification, validation-where-data-exist, regression, and compatibility review. A superior model does not automatically become the default.

---

## Evidence references

- `documentation/development/core_physics_independent_vv_report_004.md`
- `documentation/development/physics_sme_final_001.md`
- `documentation/development/phys_004_num_closeout_001.md`
- `PHYSICS-FOUNDATION-HANDOFF.md`

```text
CORE + PHYSICS FOUNDATION RECORDED AS COSMOS_0.1 REFERENCE BASELINE
```
