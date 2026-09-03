# COSMOS 0.1 — Independent Computational Kernel V&V Report 002

**Document ID:** `CORE-PHYS-REVIEW-002`  
**Date:** 2026-09-01  
**Auditor role:** Independent Computational Engineering Verification Agent (re-audit)  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Prior audit:** `documentation/development/core_physics_independent_vv_report.md` (`CORE-PHYS-REVIEW-001`)  
**Remediation under test:** `documentation/development/core_physics_remediation_001_report.md`  
**Software version observed:** `COSMOS_VERSION = 0.1.0`  
**Code modified during this audit:** none  
**Affiliation / certification claims:** none. This is not ANSYS, SIMULIA, Siemens, OpenFOAM, NASTRAN, NASA, CEA, or MMPDS validation.

```text
NOT READY — BLOCKING FINDINGS
```

The previous freeze recommendation was `NOT READY` with `S0 = 0`, `S1 = 1`, `S2 = 12`. This re-audit **does not trust** the remediation report. Every mandatory case was re-executed from first principles against the current tree.

---

## 1. Executive summary

Remediation **did** close the S1 affine-temperature defect. Independent execution now yields:

| Case | Result |
|------|--------|
| `0 °C → SI` | **273.15 K** |
| `100 °C → SI` | **373.15 K** |
| `100 °C − 0 °C` | **100 K interval** (not −173.15 °C) |
| `0 °C + 100 °C` | **`UnitError`** |
| `0 °C + 100 K` (absolute) | **`UnitError`** (justified: two absolute temperatures) |
| `0 °C + 100 K interval` | **373.15 K** |
| `25 °C × 3600 s` | **1.07334×10⁶** SI (offset retained) |

Anderson γ = 1.4, M = 2 closed-form identities still match independent algebra to machine precision, including ρ0/ρ and Prandtl–Meyer ν that REVIEW-001 noted as untested in the benchmark file. LOX at 300 K cannot be consumed via `.quantity` or `.require_valid()`. NASA7 O2 Cp(300 K) matches an independently evaluated GRI-Mech polynomial. Bartz `(D/R)^{0.1}` is implemented and **propagates** into `h` when `curvature_radius` is supplied. Canonical hashes are stable across processes and `PYTHONHASHSEED ∈ {0, 12345, 24690}`.

That is still **not** sufficient to freeze.

The remediation introduced a **new S2 architecture regression**: `core.validation.validate_mixture_ratio` and `validate_expansion_ratio` lazily import `physics.propulsion_validation`. Core is no longer an independent lower layer. REVIEW-001 required `core` to have **no upward imports**. This item is undispositioned. PHYS-004 numerics bisection remains only a **waiver pending human sign-off**. The integrated chain is still a deterministic smoke test (honestly relabeled). `ModelEvaluation` is still unused on the compute path.

Handoff / remediation freeze-readiness language is therefore **premature**. Passing tests (429 in this re-audit’s CORE+PHYS scope; remediation claimed 510) remain evidence of activity plus several real closures, not of a freeze-clean kernel.

---

## 2. Method

1. Read REVIEW-001, freeze blockers 001, and remediation 001.
2. Inspect current `core/` and `physics/` source.
3. Execute an independent script (`/tmp/cosmos_reaudit_002.py`, not committed, not a project test) that **derives expected values from textbook identities**, then compares COSMOS.
4. Re-run the CORE+PHYS pytest scope independently.
5. Classify findings with the same S0–S4 rules. S2 requires fix **or** a formal waiver. An unsigned waiver is recorded as waived-with-caveat, not as closed science.

Evidence levels:

| Level | Used in this re-audit |
|-------|------------------------|
| Software verification | pytest 429 passed; fail-closed APIs |
| Analytical verification | Anderson, NASA7 polynomial, Bartz declared SI equation, affine algebra |
| Reference validation | GRI-Mech coefficient transcription; NIST/IAPWS **scale** for LOX/LH2/water densities |
| Experimental validation | **Not performed** |

---

## 3. Remediation claims vs reproduced evidence

| ID | Remediation claim | This re-audit |
|----|-------------------|---------------|
| CORE-002-AFFINE-001 | FIXED | **Confirmed FIXED** (S1 closed) |
| CORE-002-DUAL-UNIT-001 | FIXED | **Confirmed** (deprecated `core/units.py` + factor regression) |
| CORE-003-GAMMA-001 | FIXED | **Confirmed** (`validate_gamma(1.0)` raises) |
| CORE-003-PROPULSION-001 | FIXED | **Not closed.** Validators moved, but Core now imports Physics. **Successor S2: CORE-003-LAYER-001** |
| PHYS-002-FAILOPEN-001 | FIXED | **Confirmed** (`.quantity` raises; `stored_quantity` diagnostic only) |
| PHYS-002-NIST-001 | FIXED | **Accepted as closed** with S3 residual: in-repo bands, not live NIST fetch |
| PHYS-003-DUAL-001 | FIXED | **Accepted as closed** via documented authority split; two modules remain |
| PHYS-004-NUM-001 | FORMALLY WAIVED | **Waiver exists; human sign-off pending** |
| PHYS-005-BARTZ-001 | FIXED | **Confirmed when `curvature_radius` is passed.** Default still omits the term (S3 API trap) |
| PHYS-005-CIRC-001 | FIXED | **Software identity only.** In-repo test still transcribes the same Nu equation. This audit independently recomputed the declared equation (pass). No published `h` table. |
| PHYS-005-KG-001 | FIXED | **Confirmed** (`seed_corpus` CORR-BARTZ matches physics SI form) |
| PHYS-INT-CHAIN-001 | FIXED | **Relabel confirmed.** Chain is smoke, not scientific consistency |
| PHYS-INT-PROV-001 | FIXED | **Not verified as wired.** `to_model_evaluation()` exists, **zero call sites** |

---

## 4. Architecture compliance

Required computational direction (REVIEW-001):

```text
core  (no upward imports)
  ↑
physics  (core only; numerics via port)
```

**Regression:** `core/validation.py` lines 370 and 424:

```text
from physics.propulsion_validation import validate_mixture_ratio as _validate
from physics.propulsion_validation import validate_expansion_ratio as _validate
```

`physics.propulsion_validation` imports `core.validation.validate_positive`. The import is lazy, so `import core.validation` still succeeds, and a call to `validate_mixture_ratio(2.5)` does not crash. That does **not** restore Core independence.

| Rule | Result |
|------|--------|
| physics → gui / ai / api / engineering / simulation | **Pass** (import grep clean) |
| physics → knowledge | **Pass** (no import; seed citation aligned) |
| physics defines PhysicsQuantity / ThermoQuantity / … | **Pass** |
| core → physics | **Fail** (two deprecated wrappers) |
| numerics/ present | **No.** Fallback bisection remains. Waiver on file. |

ENV-WORKSPACE-001 is unchanged: this Cursor workspace is still the empty folder; the authoritative tree is `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

---

## 5. Affine temperature (mandatory)

Independent results (Core `Quantity`, `SI.get("degC")` / `"K"`):

| Required case | Observation | Status |
|---------------|-------------|--------|
| 0 °C → 273.15 K | 273.15 | **Pass** |
| 100 °C → 373.15 K | 373.15 | **Pass** |
| 100 °C − 0 °C → 100 K | `Quantity(100.0 K, interval)` | **Pass** |
| 0 °C + 100 °C | `UnitError: Cannot add absolute temperatures.` | **Pass** |
| 0 °C + 100 K absolute | `UnitError` | **Pass** (explicit interval semantics) |
| 0 °C + 100 K interval | 373.15 K | **Pass** |
| 20 °C + 10 K interval | 30 °C / 303.15 K | **Pass** (from unit tests + algebra) |
| 25 °C × 3600 s | 298.15 × 3600 = 1 073 340 | **Pass** |

Scalar operations: `20 °C * 2` scales the **native reading** to `40 °C` (313.15 K), not `2 × 293.15 K`. This is documented in `test_celsius_scalar_multiplication_scales_native_magnitude` and is **not** the original S1 (which was Quantity×Quantity dropping `si_offset`). Residual **S3**: callers must not treat scalar multiply of `degC` as thermodynamic scaling.

**CORE-002-AFFINE-001: CLOSED.**

---

## 6. Anderson γ = 1.4, M = 2 (mandatory)

Expected values computed in this audit from Anderson identities, **not** copied from COSMOS tests:

| Quantity | Independent | COSMOS | \|Δ\| | Acceptance |
|----------|-------------|--------|-------|------------|
| T0/T | 1.8 | 1.8 | 0 | **Pass** |
| p0/p | 7.824449066867263 | 7.824449066867263 | 0 | **Pass** |
| ρ0/ρ | 4.3469161482595915 | 4.3469161482595915 | 0 | **Pass** |
| A/A* | 1.6875 | 1.6875 | 0 | **Pass** |
| NS M2 | 0.5773502691896257 | 0.5773502691896257 | 0 | **Pass** |
| NS p2/p1 | 4.5 | 4.5 | 0 | **Pass** |
| NS ρ2/ρ1 | 8/3 | 8/3 | 0 | **Pass** |
| NS T2/T1 | 1.6875 | 1.6875 | 0 | **Pass** |
| ν (P–M) | 26.37976081341645° | 26.37976081341645° | 0 | **Pass** |

Formulas used: `T0/T = 1+((γ−1)/2)M²`; `p0/p = (T0/T)^{γ/(γ−1)}`; `ρ0/ρ = (T0/T)^{1/(γ−1)}`; isentropic A/A*; Rankine–Hugoniot; Prandtl–Meyer ν(M).

**PHYS-004 closed-form: PASS** (same NUM-CONTRACT caveat as REVIEW-001).

---

## 7. Fluids (mandatory)

LOX NBP record evaluated at **300 K, 101325 Pa**:

```text
validity = OUT_OF_RANGE
.quantity        → OutOfRangeError
.require_valid() → OutOfRangeError
stored_quantity  = 1141 kg/m³   (diagnostic only; not consumable as valid)
```

Invalid LOX at 300 K **cannot** be consumed as a valid property through the public quantity accessors. **PHYS-002-FAILOPEN-001: CLOSED.**

Independent reference bands (this audit; not a live NIST download):

| Fluid | Independent scale | COSMOS catalog | Rel. deviation | Band |
|-------|-------------------|----------------|----------------|------|
| LOX NBP density | 1141 kg/m³ (NIST-scale NBP liquid O2) | 1141.0 | 0 | 2% **Pass** |
| LH2 NBP density | 70.85 kg/m³ (parahydrogen NBP scale) | 70.85 | 0 | 2% **Pass** |
| Water 300 K | 996.56 kg/m³ (IAPWS ~0.1 MPa) | 997.0 | 4.4×10⁻⁴ | 1% **Pass** |

These are **reference-point records**, not ρ(T,p). Extrapolation is explicit. Not a predictive EOS. Not live NIST validation.

---

## 8. NASA7 (mandatory)

Independent evaluation of GRI-Mech 3.0 O2 **low-T** NASA7 row (published Chemkin layout), T = 300 K:

```text
Cp/R = a1 + a2 T + a3 T² + a4 T³ + a5 T⁴
     = 3.534572525267
R    = k_B N_A (CODATA exact product in core.constants)
```

Stored COSMOS low-T coefficients **match** that GRI row exactly. COSMOS `evaluate_nasa7` Cp = **29.388071132484 J/(mol·K)**. Difference vs this audit’s truncated 8.314462618 R is 1.8×10⁻¹¹ relative — **R-digit truncation, not a polynomial bug**. NIST Cp scale ~29.38 J/(mol·K) at 298.15 K: relative deviation ≈ 2.7×10⁻⁴.

This is coefficient transcription + polynomial software/analytical check. **Not CEA. Not experimental.**

---

## 9. Bartz (mandatory)

Declared executable form in `physics/heat_transfer/bartz.py`:

```text
Nu_D = 0.026 Re_D^0.8 Pr^0.4
G*   = p_c / c*
h    = (Nu_D k / D) σ (D/R)^0.1   when curvature_radius supplied
```

Independent worked example (same numerical inputs as a geometry illustration, equations derived here, **not** read from the test’s `expected_h`):

```text
D = 0.04 m, R = 0.5 m, μ = 9e-5 Pa·s, k = 0.35 W/(m·K), Cp = 1800 J/(kg·K)
p_c = 7e6 Pa, c* = 1600 m/s, M = 0.2, γ = 1.2, Tw = 700 K, Taw = 2800 K

(D/R)^0.1 = 0.776799609716
h (R omitted) = 24691.87111450 W/(m²·K)
h (R supplied) = 19180.63584490 W/(m²·K)
h_with_R / h_without_R = 0.776799609716
```

COSMOS matches all three to 1e-12 relative. Curvature **propagates**. Omitting R still biases this geometry by ~22%, which is now an explicit default (`curvature_factor = 1.0`), not a missing equation.

The in-repo benchmark still transcribes `Nu = 0.026 Re^0.8 Pr^0.4` before calling the implementation. That remains a **tautological literature test**. This re-audit’s independent recomputation is the non-tautological check of the **declared** equation. There is still **no** Huzel/Bartz published heat-flux table comparison.

Knowledge `CORR-BARTZ` now cites the physics SI executable form including `(D/R)**0.1`. Single computational authority for the equation string: **restored**.

---

## 10. Integrated chain (mandatory)

`tests/validation_tests/test_physics_chain.py` is explicitly a **smoke** test. Independent inspection of the source:

- `gamma = 1.2` hardcoded (not NASA7/CEA at 3000 K)
- Bartz μ, k, Cp, c* are literals
- yield queried at **300 K**; wall temperature in the Bartz call is **800 K**
- Docstring: “Scientific consistency is not claimed here.”

The function executes and is deterministic. It is **not** a physically consistent propellant → thermochemistry → chamber → nozzle → thermal → materials → structure calculation.

**INT-001:** pass as smoke wiring; **fail** as scientific chain. Disposition by relabel is acceptable **only** if freeze text does not call this an engine analysis.

---

## 11. Determinism (mandatory)

| Experiment | Result |
|------------|--------|
| 20 in-process hashes of `Quantity(100 °C)` | one value `7e6debf2b93d7db37a7ebcad491214f69a023856b05b9e93ec5fcaafd14b07f6` |
| 20 in-process `p0/p(M=2,γ=1.4)` | one value `7.824449066867263` |
| 3 subprocesses, `PYTHONHASHSEED` = 0, 12345, 24690 | identical hash and `p0/p` |

**Pass** for the measured compute path.

---

## 12. Tests executed independently

```text
pytest tests/unit_tests/core tests/unit_tests/physics
       tests/unit_tests/test_validation.py
       tests/unit_tests/test_propellants.py tests/unit_tests/test_cache.py
       tests/validation_tests/test_physics_chain.py
       tests/validation_tests/test_physics_conservation.py
       tests/benchmark_tests/test_anderson_bartz.py
       tests/benchmark_tests/test_fluid_nist_references.py
       tests/regression_tests/test_physics_foundation.py

429 passed in 0.65 s
```

Remediation’s “510 passed” was **not reproduced** under this explicitly listed scope. The discrepancy is a counting/scope issue, not a failing test in the scope above.

---

## 13. Findings by severity

### S0 — none

Peng–Robinson still fail-closed. No pickle RCE on the compute path. Physics still does not import GUI/AI/API/engineering.

### S1 — none open

CORE-002-AFFINE-001 is closed by independent execution.

### S2 — open (1)

| ID | Defect | Freeze |
|----|--------|--------|
| **CORE-003-LAYER-001** | Core deprecated propulsion validators import Physics. Violates `core` independence and creates a latent `core.validation` ↔ `physics.propulsion_validation` cycle. | **Yes, until fix or formal waiver** |

### S2 — formally waived (1)

| ID | Status |
|----|--------|
| **PHYS-004-NUM-001** | Waiver file exists. **Approved by: Pending human sign-off.** |

### S2 from REVIEW-001 now closed (this re-audit)

AFFINE (was S1), DUAL-UNIT, GAMMA, FAILOPEN, NIST (with S3 residual), DUAL thermochemistry docs, BARTZ curvature when R given, KG Bartz string, CHAIN relabel.

### S3 (selected residuals)

| ID | Issue |
|----|--------|
| CORE-003-DEPREC-001 | Deprecation is docstring-only; no `DeprecationWarning` |
| PHYS-005-BARTZ-DEFAULT-001 | `curvature_radius=None` silently uses factor 1 |
| PHYS-005-CIRC-RESIDUAL | In-repo Bartz benchmark still transcribes the same equation |
| PHYS-INT-PROV-RESIDUAL | `to_model_evaluation()` unused |
| PHYS-002-NIST-LIVE | No live NIST retrieval; bands are authored constants |
| AFFINE-SCALAR-001 | `degC * scalar` scales the reading, not T_SI |
| ENV-WORKSPACE-001 | Empty Cursor workspace vs authoritative repo |
| PHYS-007-FRAC-TEST-001 | Fracture coverage still not part of this re-audit’s scientific cases |

### S4

Missing `__radd__`/`__rsub__` for mixed types; integer Core dimensions / `K_I` as float (unchanged scope).

---

## 14. What this re-audit does not claim

- Experimental engine or heat-flux validation
- CEA executable comparison
- MMPDS / certified allowables
- Equivalence to ANSYS, NASTRAN, OpenFOAM, or NASA production tools
- That the smoke chain is a complete rocket-engine calculation

---

## 15. Freeze recommendation

```text
NOT READY — BLOCKING FINDINGS
```

S1 is closed. Most REVIEW-001 S2 items are closed or waived. Freeze is blocked by **CORE-003-LAYER-001** (undispositioned S2).

A subsequent sign-off could become **FREEZE READY WITH FORMAL WAIVERS** after either:

1. removing Physics imports from Core (keep deprecated bodies in Core, or delete the wrappers), **or**
2. a signed waiver that Core propulsion stubs may import Physics for the 0.1 joint freeze,

**and** human signature on `PHYS-004-NUM-WAIVER.md`.

Until then, do not freeze CORE-001..005 / PHYS-001..007 as a computational foundation.

---

## Required summary table

| Area | Status | Critical findings | Freeze impact |
|------|--------|-------------------|---------------|
| CORE-001 | **PASS** | S3 exception-name leakage unchanged | None |
| CORE-002 | **PASS** | S1 affine closed; dual units deprecated | Unblocked |
| CORE-003 | **FAIL** | S2 Core→Physics import | **Blocks freeze** |
| CORE-004 | **PASS** | Hash stable across processes / HASHSEED | None |
| CORE-005 | **CONDITIONAL** | Affine tests exist; layering remains | Blocked by CORE-003 |
| PHYS-001 | **PASS** | Ideal-gas scope | None |
| PHYS-002 | **PASS** | Fail-closed LOX 300 K | None |
| PHYS-003 | **PASS** | NASA7 O2 independent poly; CEA still unbound | Interface-only |
| PHYS-004 | **PASS** | Anderson identities; NUM waiver unsigned | Waiver caveat |
| PHYS-005 | **PASS*** | Declared Bartz SI + curvature when R given | *not experimental Bartz 1957 |
| PHYS-006 | **PASS** | Room-T handbook lookup | Not MMPDS |
| PHYS-007 | **PASS** | Constitutive scope | Not a design code |
| INT-001 | **PASS as smoke** | Hardcoded γ=1.2 | Must not be overclaimed |

```text
Total open findings recorded: 1 S2 + 8 S3 + 2 S4 (S0 = 0, S1 = 0)
S0: 0
S1: 0
S2: 1 open + 1 waived (unsigned)
S3: 8 selected
S4: 2

Freeze blockers: CORE-003-LAYER-001
Open waivers: PHYS-004-NUM-001 (pending human sign-off)
Recommended next action: Eliminate core→physics imports (or sign a layering waiver and the NUM waiver); then re-run affine, Anderson, LOX, NASA7, Bartz curvature, and hash cases.
```
