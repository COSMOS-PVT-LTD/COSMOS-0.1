# PHYSICS SME REVIEW 002

**Document ID:** `PHYSICS-SME-REVIEW-002`  
**Date:** 2026-09-01  
**Role:** Physics Subject-Matter Reviewer  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Scope:** Physics consequences of `CORE-003-LAYER-001` and `PHYS-004-NUM-001` after Core remediation  
**Code modified during this review:** none  

This review is **not** a freeze authority decision and **not** an independent computational V&V audit. It does **not** certify PHYS-001..007 implementation completeness, experimental validation, CEA validation, MMPDS compliance, or equivalence to external engineering software.

---

## 1. Physics regression status

Mandatory Physics checks were re-executed against current source. Expected Anderson / NASA7 / Bartz values were derived independently in the review script, not taken from COSMOS test literals as the sole authority.

| Domain | Check | Result |
|--------|-------|--------|
| Thermodynamics / compressible | Anderson γ=1.4, M=2: T0/T, p0/p, ρ0/ρ, A/A*, normal shock (M2, p2/p1, ρ2/ρ1, T2/T1), Prandtl–Meyer ν | **Pass** (machine precision vs independent identities) |
| Fluids | LOX NBP record at 300 K, 101325 Pa | **Pass** — `OUT_OF_RANGE`; `.quantity` and `.require_valid()` raise |
| Thermochemistry | NASA7 O2 Cp(300 K) vs independent GRI low-T polynomial × Core `UNIVERSAL_GAS_CONSTANT` | **Pass** — 29.388071132483972 J/(mol·K) |
| Heat transfer | Bartz `(D/R)^0.1` with D=0.04 m, R=0.5 m | **Pass** — factor 0.7767996097157338; `h` scales by the same factor |
| Determinism | In-process + 3 processes with `PYTHONHASHSEED` ∈ {0, 12345, 24690} | **Pass** — hash `7e6debf2…`, `p0/p = 7.824449066867263` (regression lock) |
| Numerics inverses | Area–Mach inverse recovers M=2; no-sign-change raises `SolverConvergenceError` | **Pass** |
| Layering smoke | `physics.propulsion_validation` and Core deprecated wrappers both functional | **Pass** |

Pytest (Physics-focused + layer independence + legacy validation wrappers):

```text
125 passed in 0.18 s
```

Scope included: `tests/unit_tests/physics`, physics validation/benchmark/regression suites, `test_core_layer_independence.py`, `test_validation.py`.

### Domain integrity (no damage observed)

| Package | Observation after Core remediation |
|---------|--------------------------------------|
| Thermodynamics | Unchanged public path; still uses Core `Quantity` / `validate_positive` / `require_gamma` |
| Fluid properties | Fail-closed LOX behavior intact |
| Thermochemistry | NASA7 path intact; CEA still interface-only (unchanged limitation) |
| Compressible flow | Closed-form identities intact; inverses still via `numerics_port` |
| Heat transfer | Bartz curvature propagation intact when `curvature_radius` supplied |
| Materials / solid mechanics | Not exercised by the two findings under review; no Core→Physics change touches them |
| Physics validation contracts | `physics.propulsion_validation` remains Physics → Core only |

**Verdict:** No Physics scientific regression detected from the Core layering fix. Deterministic locked values are unchanged.

---

## 2. Numerics waiver assessment (`PHYS-004-NUM-001`)

### Inspected artifacts

- `physics/contracts/numerics_port.py`
- `physics/contracts/PHYS-004-NUM-WAIVER.md`
- `physics/contracts/NUM-CONTRACT-ISSUE.md`
- Call sites: `area_mach.py`, `expansion_fan.py`, `oblique_shock.py`

### Technical criteria

| Criterion | Assessment |
|-----------|------------|
| Isolated | **Yes.** Single module; public surface is `bracketed_root` / `ScalarRootFinder`. No Numerics framework sprawl. |
| Deterministic | **Yes** for fixed brackets / residuals. Area–Mach inverse recovers M=2 to ~1e-13. Multiprocess Physics hashes unchanged. |
| Bounded | **Yes.** Requires finite bracket, sign change, `max_iter=80`, `xtol=1e-12`; otherwise `SolverConvergenceError` / `InvalidInputError`. |
| Explicitly scoped | **Yes.** Waiver and NUM-CONTRACT-ISSUE limit use to PHYS-004 scalar inverses. MOC marching is not implemented here. |
| Free from Core dependency *as Numerics owner* | **Acceptable.** Port uses Core exceptions and `validate_finite` only — Physics → Core. It does **not** pull Numerics into Core. |
| Correctly documented | **Mostly.** Waiver, NUM-CONTRACT-ISSUE, and model `numerical_method_dependency` strings exist. Waiver still **“Pending human sign-off.”** |

### Current behavior

With `numerics/` absent, `bracketed_root is _fallback_bisection`. Preferential load of `numerics.root_finding.bisection.find_root` is present but unused.

Closed-form Anderson identities **do not** depend on this port. Inverse Mach / inverse ν / θ–β–M **do**.

### SME opinion on waiver reasonableness (0.1 freeze scope)

The temporary bisection fallback is **technically reasonable** for a COSMOS 0.1 Physics foundation freeze **provided**:

1. Capability claims state “closed-form gasdynamics + temporary scalar inverses,” not “Numerics delivered.”
2. The waiver is **human-signed** before treating PHYS-004-NUM-001 as administratively closed.
3. Fallback is deleted when canonical `numerics.root_finding` lands (removal condition already written).

This SME review does **not** convert the unsigned waiver into a signed approval. It only confirms the Physics-side technical basis for a 0.1 waiver is sound.

---

## 3. Layering impact (`CORE-003-LAYER-001`)

### Desired architecture

```text
Physics → Core
Core ─X→ Physics
```

### Current source state (Physics SME inspection)

After Remediation 002 (inspected, not trusted blindly):

- `core/validation.py` deprecated wrappers call local `validate_positive` only.
- Docstrings may *mention* `physics.propulsion_validation` as the preferred new API; that is documentation, not an import.
- AST scan of all `core/**/*.py`: **zero** `physics` imports.
- Runtime callers of Core wrappers do not load Physics modules (covered by `test_core_layer_independence.py`).
- `physics/propulsion_validation.py` imports only `core.validation.validate_positive`.

### Will removing / retaining Core wrappers hurt Physics?

| Change | Physics impact |
|--------|----------------|
| Keep self-contained Core wrappers (current) | **None.** Physics does not call them. Production Physics path uses `physics.propulsion_validation` or Physics-local gates (`require_gamma`, etc.). |
| Delete Core wrappers | **None** for Physics modules. Only tests that import Core wrappers would need update (`tests/unit_tests/test_validation.py`). |
| Reintroduce Core → Physics lazy import | **Forbidden.** Would recreate CORE-003-LAYER-001 and must not be done for compatibility. |

**Physics SME finding:** Moving or removing the deprecated Core wrappers will **not** cause Physics compute regressions under the current call graph. Physics already owns the propulsion validators. Do **not** reintroduce a Core → Physics dependency.

Independent V&V must still confirm CORE-003-LAYER-001 closure; this SME review only confirms **Physics is not harmed** by the fix direction.

---

## 4. Potential physics regressions / residual risks

| Item | Severity for Physics | Notes |
|------|----------------------|-------|
| Unsigned PHYS-004-NUM waiver | Process / S2 admin | Technical isolation OK; human signature still required |
| Inverse results may change when Numerics lands | Known | Documented in waiver; closed-form paths unaffected |
| Stale comment in `physics/quantities.require_gamma` / `CORE-CONTRACT-ISSUE.md` still saying Core permits γ=1 | Documentation drift | Core now rejects γ≤1; Physics still enforces `1 < γ ≤ 3`. Not a numerical regression |
| Bartz default without `curvature_radius` | Residual model trap | Factor = 1; not introduced by Core remediation |
| Smoke chain still hardcoded γ=1.2 | Scope honesty | Unchanged; not a Core-remediation regression |
| Dual API: Core vs Physics propulsion validators | Compatibility | Behaviorally identical (`validate_positive`); authority for new Physics code is `physics.propulsion_validation` |

No evidence that Core affine / gamma / layering remediation damaged PHYS-001..007 numerical results.

---

## 5. Required action

1. **Independent V&V** must re-confirm CORE-003-LAYER-001 closed (AST + runtime). Physics SME sees no Physics damage from the fix.
2. **Human sign-off** on `physics/contracts/PHYS-004-NUM-WAIVER.md` if the 0.1 freeze is to accept temporary bisection — or land `numerics/` and delete the fallback.
3. **Do not** restore Core → Physics imports for backward compatibility.
4. Optional cleanup (non-blocking for Physics regressions): update stale γ=1 notes in `physics/quantities.py` / `CORE-CONTRACT-ISSUE.md` so Physics docs match post-remediation Core.
5. Freeze readiness is **out of scope** for this SME review and is not declared here.

---

## 6. Summary for Integration / Freeze owners

| Topic | Physics SME conclusion |
|-------|------------------------|
| Physics regression status | **No regressions observed** on mandatory Anderson / LOX / NASA7 / Bartz / determinism suite |
| Numerics waiver assessment | **Technically reasonable** for 0.1 if scoped and human-signed; not scientifically “solved” |
| Layering impact | Core remediation direction is **safe for Physics**; wrappers removable without Physics code changes |
| Potential physics regressions | None from the two findings under review; residual docs/waiver/process items only |
| Required action | Human NUM waiver decision + independent V&V layering confirmation; no Physics code change required by this SME review |

This document does **not** declare freeze ready / not ready.

```text
PHYSICS SME REVIEW COMPLETE
```
