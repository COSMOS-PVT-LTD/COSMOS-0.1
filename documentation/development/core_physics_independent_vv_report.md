# COSMOS 0.1 — Independent Computational Kernel V&V Report

**Document ID:** `CORE-PHYS-REVIEW-001`  
**Date:** 2026-09-01  
**Auditor role:** Independent Computational Engineering Verification Agent  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Software version observed:** `COSMOS_VERSION = 0.1.0`, `CORE_API_VERSION = 1.0.0`, `PHYSICS_SCHEMA_VERSION = 0.1.0`  
**Code modified during this audit:** none  
**Affiliation / certification claims:** none. This is not ANSYS, SIMULIA, Siemens, OpenFOAM, NASTRAN, or NASA validation.

```text
NOT READY — BLOCKING FINDINGS
```

---

## 1. Executive summary

The CORE-001..004 kernel and PHYS-001..007 foundation are a coherent, mostly fail-closed computational stack with clean layering (`physics → core`, no `core → physics`, no `physics → knowledge/gui/engineering`). Closed-form compressible-flow identities match independent Anderson algebra at γ = 1.4, M = 2 to machine precision. NASA7 O2 Cp(300 K) matches the GRI-Mech polynomial and agrees with the NIST Cp scale to ~0.03%. Peng–Robinson is correctly refused. CEA is an unbound interface. MOC marching is not in physics. Serialization hashes are deterministic across `PYTHONHASHSEED` and separate processes.

That is **not** sufficient to freeze.

The freeze is blocked by a **silent affine-unit arithmetic defect** on Core `Quantity` (S1) and by undispositioned S2 items: dual unit systems, Core γ = 1, fail-open fluid records, dual thermochemistry APIs, a simplified Bartz missing `(D_t/R)^{0.1}`, circular Bartz tests, knowledge/physics Bartz disagreement, and an integrated chain that is deterministic but not scientifically consistent.

Handoff reports (`core_005_handoff_report.md`, `PHYSICS-FOUNDATION-HANDOFF.md`) are largely honest about CEA, MMPDS, experimental validation, and Peng–Robinson. They **understate** affine-unit severity and **overstate** freeze readiness. Passing tests (503 in the CORE+PHYS scope run here; handoff claimed 148 core / 340 physics) are evidence of activity, not of independent scientific completeness.

---

## 2. Repository / environment status

| Item | Observation |
|------|-------------|
| Authoritative path required by audit | `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1` |
| Path actually containing Core/Physics | Same. Audited this tree only. |
| Active Cursor workspace | `/Users/vaibhavkumarn/Desktop/desktop files :07:07:2026/COSMOS_0.1` — **empty** except `.cursor/`. `move_agent_to_root` failed (`InstantiationService disposed`). |
| Competing sources of truth | **Environment issue.** Implementers have already noted this in the CORE-005 handoff. |
| Frozen architecture source | `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS DOCS /COSMOS_0.1_FREEZED_ARCHITECTURE.md` |
| Batch matrix / execution plan | `/Users/vaibhavkumarn/Desktop/COSMOS/coursor prompts /` (not inside the repo) |
| `numerics/`, `engineering/` | Absent. Expected for a CORE+PHYS foundation freeze; **not** a whole-architecture freeze. |

**Finding ENV-WORKSPACE-001 (S3):** Point the workspace at the authoritative repository before any freeze sign-off so reviews cannot land in the empty tree.

---

## 3. Architecture compliance

Required computational direction:

```text
core → physics → numerics → engineering → simulation / optimization
```

Observed among implemented packages:

```text
core  (no upward imports)
  ↑
physics  (core only; numerics via documented port)
  ↑
tests

knowledge → core.exceptions only
physics ↛ knowledge, gui, api, engineering
```

| Rule | Result |
|------|--------|
| `core` contains no rocket/combustion/injector/nozzle/HT/CFD/GUI **algorithms** | **Pass** for CORE-001..004 modules. Residual: propulsion **validators** and **exception type names** (`CFDError`, `GUIError`) plus `core/config_v0_1_1.py` CFD/GUI config (legacy package, outside CORE-001..004 files but inside `core/`). |
| `physics` contains no GUI/API/DB/engineering orchestration | **Pass** (import grep clean). |
| Knowledge is not a second solver | **Pass.** `knowledge/models/quantity.py` is metadata, not arithmetic. |
| Numerics owns numerical algorithms | **Partial.** Closed-form physics is correct. Inverse Mach / Prandtl–Meyer / θ–β–M use `physics.contracts.numerics_port._fallback_bisection` because `numerics/` is missing. Documented; still a duplicate scalar solver. MOC marching is **not** duplicated. |
| Cycles | **None** found among `core` / `physics` / `knowledge`. |

This audit does **not** freeze the 24-package architecture. Missing `engineering/`, `optimization/`, `ai/`, etc. are whole-repo gaps, not CORE-PHYS computational blockers.

---

## 4. Core audit (CORE-001, CORE-005)

### CORE-001 — contracts

`core/contracts.py` is domain-independent: `ValidationResult`, `DimensionProtocol`, `UnitProtocol`, `QuantityProtocol`, `CanonicalSerializable`. Physics consumes concrete Core types rather than duplicating contracts. Protocols are untested as `isinstance` checks (S3). `core/__init__.py` does not re-export a frozen public surface (S3).

### Exceptions

`core/exceptions.py` provides a usable hierarchy (`CoreError` → `CosmosError` → typed errors). Domain names `CFDError`, `GUIError`, `DatabaseError` leak application ownership into Core (**S3**, not an algorithm). Module branding still says “Rocket Propulsion Platform.”

### CORE-005 freeze gate

CORE-005 handoff: freeze candidate, 148 tests. Independent run of the documented core scope: **153 passed**. Test count is not the issue. Affine arithmetic is untested and wrong. CORE-005 is **FAIL** while S1 remains open.

---

## 5. Unit / dimension audit (CORE-002)

### What holds

Independent checks:

| Case | Result |
|------|--------|
| length + pressure | `DimensionError` |
| pressure / density | velocity² dimension, SI 25000 for 1e5 Pa / 4 kg/m³ |
| mass / time | mass-flow dimension |
| dimensionless × length | valid |
| NaN / ±∞ Quantity | rejected |
| zero and negative magnitudes | allowed (mathematically) |
| `psi` legacy vs `SI.get("psi")` vs `PSI_TO_PASCAL` | identical 6894.757293168361 |
| `0 °C` conversion | 273.15 K, matches `celsius_to_kelvin` |

Integer SI exponent algebra (`Dimension.multiply/divide/power`) is correct. Named dimensions cover the mechanical set; physics builds transport units in `physics/si.py` from Core algebra (not a second unit *system*).

### S1 — affine arithmetic

`Unit.convert_to_si` is `magnitude * scale + offset`. `Quantity.__add__` sums `to_si()` values then converts back. Independent execution:

```text
(0 °C).to_si()                 = 273.15 K
(100 °C).to_si()               = 373.15 K
(0 °C + 100 °C).to_si()        = 646.30 K     expected: invalid, or 373.15 K if “100 °C absolute”
(100 °C − 0 °C).magnitude      = −173.15 °C   SI difference 100 K is correct; affine reconversion is not
(25 °C × 3600 s).to_si()       = 90000        expected ~1.073e6 if 25 °C is thermodynamic
```

Physics public helpers use Kelvin only (`physics` has **zero** `degC` references). The defect is still in the frozen Core type: `degC` is registered and arithmetic is public.

**ID: CORE-002-AFFINE-001**  
**Severity: S1**  
**Freeze blocker: YES**

### Fractional dimensions

`Dimension.power` rejects non-integers. `LENGTH ** 0.5` raises. PHYS-007 `mode_i_infinite_plate` returns `float` [Pa √m] with a dummy unit `PRESSURE * LENGTH**0`. If Core freeze claims “all engineering dimensions,” this is in-scope. Declared Core contract is integer SI exponents → **S2 / scope limitation**, not S1.

### Dual unit authority

Legacy `core/units.py` scalar helpers coexist with `core/unit.py`. No production `physics` import of `core.units`. Factors match today. **S2**, must be dispositioned (deprecation or dual-system contract).

---

## 6. Validation / exception audit (CORE-003)

Generic validators (`validate_finite`, `validate_positive`, `collect_validation`) raise typed errors. No bare `except:` / silent `pass` on CORE-003 compute paths.

Defects:

- `validate_gamma(1.0)` returns `1.0`. Physics `require_gamma(1.0)` raises. Core tests never hit γ = 1. **S2, freeze blocker until disposition.**
- `validate_mixture_ratio`, `validate_expansion_ratio` are propulsion-specific. **S2.**

`core/settings.py` and `core/config_v0_1_1.py` use `except Exception` then re-raise or wrap — not silent numeric fallback.

Physics legacy `thermochemistry/cache.py` has multiple `except Exception: pass` on file unlink (**S3**, not on the new compute path).

---

## 7. Metadata / serialization / hash audit (CORE-004)

`canonical_json_dumps`: sorted keys, compact separators, `allow_nan=False`, `-0.0 → 0.0` normalization in hashing tests. Independent:

- dict insertion order does not change the hash
- 50 in-process repeats of a Quantity payload: identical SHA-256
- 3 subprocesses with `PYTHONHASHSEED ∈ {0, 12345, 24690}`: identical hash `22040d2c…`, identical `p0/p(M=2)`, identical choked `ṁ`

No timestamps, object ids, or pickle in Core serialization. `eval`/`exec`/`pickle` are not used on the Core/Physics compute path.

`ObjectMetadata.assumptions` order is significant (unsorted). Document the contract (**S3**). `PhysicalConstant.from_canonical_dict` raises `ValueError` rather than `SerializationError` (**S3**).

**CORE-004: PASS** for freeze of the determinism design, with minor taxonomy/test gaps.

---

## 8. Thermodynamics audit (PHYS-001)

Implemented: calorically perfect ideal gas `p = ρ R T`, `a = √(γ R T)`, `Cp − Cv = R`, `h = Cp T` (0 K datum), first/second-law helpers, Z identity, saturation/cubic **interfaces**.

Independent:

```text
a(273.15 K, γ=1.4, M=0.0289647 kg/mol) = 331.31965118168387 m/s  (matches first principles, rel 0)
ρ(101325 Pa, 273.15 K) = 1.292261058079426 kg/m³               (matches p/RT)
peng_robinson() → InsufficientDataError                         (fail-closed; Peng–Robinson issue is NOT a silent-coeff bug)
```

`evaluate_state` marks `VALID` for any positive T, p, legal γ — no near-saturation flag (**S3**). Enthalpy datum is not formation enthalpy; mixing with NASA7 H without a shift is a documented limitation.

Physical equation, property wrappers (`enthalpy.py`, `entropy.py`), and numerical solution are separated. Several wrappers have 0% coverage because tests call `ideal_gas` directly (**S3** test organization).

**PHYS-001: PASS** within declared ideal-gas scope.

---

## 9. Fluid-property audit (PHYS-002)

Sutherland viscosity: fail-closed out of range unless `allow_extrapolation=True`; formula μ(T_ref) = μ_ref holds. Dimensionless Re/Pr are unit-safe.

Property **records** are reference-state constants, not ρ(T,p). `evaluate_record` still takes T and p. Independent:

```text
LOX NBP density record = 1141 kg/m³
evaluate_record(..., T=300 K) .quantity = 1141, validity=OUT_OF_RANGE
.require_valid() raises OutOfRangeError
allow_extrapolation=True → same 1141, validity=EXTRAPOLATED  (not a predictive model)
```

This is **not** silent extrapolation of a correlation; it is a fail-open numeric field on an invalid state. Callers that read `.quantity` get a cryogenic density at room temperature.

NIST/Incropera citations exist in `records.py`. Tests lock the same literals. No independent table comparison was present; this audit did not fetch live NIST (network not used for scientific calc, and this review does not treat a related paper as automatic validation).

RP-1 810 kg/m³ is labeled typical. LOX γ = 1.40 is an ideal-gas stand-in.

**PHYS-002: FAIL** until fail-open `.quantity` and NIST regression are dispositioned.

---

## 10. Thermochemistry audit (PHYS-003)

### NASA7

Polynomial forms match NASA TM-4513 / Chemkin:

`Cp/R = a1 + a2 T + …`, `H/RT` and `S/R` standard. Out-of-range rejected unless extrapolation is requested.

Independent O2 at 300 K using the stored GRI low-interval coefficients:

```text
Cp/R = 3.534572525267
Cp   = 29.388071132483972 J/(mol K)
NIST ~29.38 J/(mol K) at 298.15 K; relative deviation ≈ 2.7e-4
```

N2/O2 coefficient rows match the published GRI-Mech 3.0 `thermo.dat` layout (high/low split). That is transcription evidence for those two species, **not** a CEA campaign and **not** H/S/continuity coverage. Tests only check O2 Cp ± 2%.

He uses kinetic-theory Cp/R = 2.5 with unsourced H/S datum.

N2 `t_min_k = 300`; 298.15 K STP is out of range.

### Dual API

`physics.thermochemistry.species` (NASA7 registry) and `physics.thermochemistry.propellants` (“single source of truth”, CEA species names, JSON DB) both exist. New compute path does not import CEA executables. Legacy `cea_species_name` is a naming leak on the old path.

### CEA boundary

```text
CEA interface  = cea_interface.ThermochemistryEngine + CeaRequest/ThermochemicalResult
CEA executable = not present
CEA validation = not performed
```

`run_thermochemistry(engine=None)` raises `InsufficientDataError`. Adapter types do not appear on `ThermochemicalResult`. This matches the declared foundation scope. A freeze that claims “thermochemistry capability” without an adapter overclaims.

**PHYS-003: FAIL** on dual authority. CEA unbound is acceptable **only** if the freeze text says interface-only.

---

## 11. Compressible-flow audit (PHYS-004)

### Independent Anderson γ = 1.4, M = 2

| Quantity | First principles | COSMOS | |Δ| | Tolerance basis | Acceptance |
|----------|------------------|--------|-----|-----------------|------------|
| T0/T | 1.8 | 1.8 | 0 | exact identity | **Pass** |
| p0/p | 7.824449066867263 | 7.824449066867263 | 0 | Anderson table / identity | **Pass** |
| ρ0/ρ | 4.3469161482595915 | 4.3469161482595915 | 0 | identity (untested in benchmark file) | **Pass** (code) |
| A/A* | 1.6875 | 1.6875 | 0 | Anderson | **Pass** |
| NS M2 | 0.5773502691896257 | 0.5773502691896257 | 0 | Rankine–Hugoniot | **Pass** |
| NS p2/p1 | 4.5 | 4.5 | 0 | identity | **Pass** |
| NS ρ2/ρ1 | 8/3 | 8/3 | 0 | identity | **Pass** |
| NS T2/T1 | 1.6875 | 1.6875 | 0 | p/ρ consistency | **Pass** |
| ν (P–M) | 26.379760813416446° | 26.379760813416446° | 0 | Anderson formula (no table test) | **Pass** (code) |
| M → 0 T0/T | 1 | 1 | 0 | limit | **Pass** |
| M = 1 A/A* | 1 | 1 | 0 | sonic identity | **Pass** |

`require_gamma` rejects γ = 1. Area–Mach / P–M inverse / oblique β use the numerics port (fallback bisection). `moc_nozzle.generate_contour` raises `InsufficientDataError`.

Gaps: Fanno/Rayleigh/oblique lack independent table tests; `losses.py` and `pressure_profile.py` are 0% coverage in the CORE+PHYS pytest set; expansion-fan inverse coverage 53%.

**PHYS-004: PASS** for closed-form gasdynamics, conditional on NUM-CONTRACT waiver for the bisection port.

---

## 12. Heat-transfer audit (PHYS-005)

Conduction / Newton cooling / radiation / resistance / lumped Bi gate are present and mostly tested. Film cooling is an honest stub.

### Bartz

Implemented and labeled `PHYS-005.bartz.nusselt_si`:

```text
Nu_D = 0.026 Re_D^0.8 Pr^0.4
G*   = p_c / c*
h    = (Nu_D k / D) σ
```

σ(M=0, Tw=Taw) = 1 independently confirmed. Re < 1e4 → `OUT_OF_RANGE`.

Original Bartz 1957 / Huzel & Huang NASA SP-125 dimensionless form also includes **`(D_t/R)^{0.1}`**. That term is absent from the physics equations tuple and API (no radius input). Independent numerical illustration, not a claim of a published h table:

```text
D_t = 0.04 m, R = 0.5 m  →  (D_t/R)^0.1 ≈ 0.7768
```

Omitting the term biases h by ~22% for that geometry. The English-unit dimensional 0.026 package is **not** what the code implements (good). The SI Nusselt origin is documented. Calling the model “Bartz” without curvature still disagrees with the named literature correlation and with `knowledge/foundation/seed_corpus.py` (`*(Dt/R)**0.1`).

The benchmark `test_bartz_nusselt_origin_not_english_package` reconstructs `h` from the same Nu definition. That is software identity, not reference validation.

**PHYS-005: FAIL** for a freeze that includes rocket gas-side Bartz as Bartz 1957. Eligible for waiver only as simplified SI Nusselt-origin Bartz without curvature.

---

## 13. Materials audit (PHYS-006)

Catalog: OFHC copper, 304 SS, Al 6061-T6, Inconel-class, Ti-6Al-4V — room-temperature window ±10 K around 300 K. Notes: “not MMPDS certified allowables.” Interpolation is not performed. 900 K correctly rejected in tests. Copper yield is `None`. Creep/fatigue modules raise `InsufficientDataError`.

Thin wrappers `aluminum_alloys.py` etc. are re-exports (0% coverage is not a second data set).

**PHYS-006: PASS** as a room-temperature handbook property lookup. Must not be frozen as design allowables.

---

## 14. Solid-mechanics audit (PHYS-007)

Independent hoop: `p = 5e6 Pa`, `r = 0.1 m`, `t = 0.008 m` → `σ_h = 6.25e7 Pa`, matches `cylinder()`. `r/t = 12.5` (thin-wall typical); `r/t < 10` is documented but not rejected (**S3**).

`K_I = σ √(π a)`: 1e8 Pa, a = 0.001 m → 5,604,991.216 Pa√m, matches. Return type `float`. **`physics/solid_mechanics/fracture.py` coverage = 0%** in the executed suite (**S3**). Plasticity/shells/strain wrappers similarly untested.

Pressure-vessel module states it is not ASME. Yield ratio is a physical ratio, not a design code.

**PHYS-007: PASS** for Hooke / von Mises / thin-wall / Euler within physics-not-code scope.

---

## 15. Integrated-chain audit (CORE-PHYS-INT-001)

File: `tests/validation_tests/test_physics_chain.py`.

Declared chain:

```text
H2/O2 mixture → ideal-gas chamber → choked ṁ → nozzle station
  → thrust → recovery T + Bartz + flux → 304 yield vs hoop
```

Independent 10× repeat + 3-process check: identical `(ṁ, M_e, F)`:

```text
ṁ = 29.040178198413148 kg/s
M_e = 3.121903423149032
F = 77558.16725215132 N
```

Unit-safe, deterministic, no hidden CEA fallback.

Not scientifically consistent:

- γ hardcoded **1.2**, not from NASA7/CEA at 3000 K
- Bartz uses **exit Mach**, **chamber pressure**, D = 0.113 m, μ/k/Cp invented literals, c* = 1500 m/s
- yield queried at **300 K** while wall T is **800 K** (800 K is outside the material window if asked)

This is a **wiring smoke test**, not an independent engine calculation.

**INT-001: FAIL** as “integrated scientific calculation chain.” Pass only if relabeled demonstration/smoke.

---

## 16. Numerical robustness

| Topic | Observation |
|-------|-------------|
| Division by zero | Quantity division guarded; γ = 1 blocked in physics, not in Core |
| Domain (log, sqrt) | P–M requires M ≥ 1; crack length > 0; NASA7 T windows |
| Root finding | Bracketed bisection; no sign change → `SolverConvergenceError`; max_iter 80 |
| Clamps | Fanno `max(fl, 0)` after negative check — documented |
| Hidden fallback | Fluid `.quantity` on OUT_OF_RANGE; cache unlink `pass`; **not** silent Peng–Robinson |
| MOC / cubic EOS | Explicit insufficient-data |

The Core affine path is a robustness failure: wrong finite numbers, not exceptions.

---

## 17. Determinism

| Experiment | Result |
|------------|--------|
| Canonical hash, shuffled keys | identical |
| 50 in-process Quantity hashes | identical |
| 3 processes, varying `PYTHONHASHSEED` | identical hash and `p0/p`, `ṁ` |
| 10× physics chain | one unique tuple |
| Physics env/config imports | none |

**Pass** for the measured CORE+PHYS compute path.

---

## 18. Provenance

`ModelIdentity` on models records equation, assumptions, validity, source, verification_status, limitations. `PHYSICS_SCHEMA_VERSION` and `COSMOS_VERSION` exist.

Gaps: `ModelEvaluation` has **zero** call sites. Results do not bind the input `Quantity`s that produced them. Fluid/material records carry source strings; evaluation objects carry validity. That is better than a bare float, short of a full engineering envelope (input, units, model version, numerical config, verification status on every number).

---

## 19. Test-quality assessment

Independent pytest (this audit):

```text
tests/unit_tests/core/ + validation_tests/{units,dimensions}.py
+ legacy core tests + tests/unit_tests/physics/
+ test_anderson_bartz.py + test_physics_chain.py
+ test_physics_conservation.py + test_physics_foundation.py
+ test_propellants.py + test_cache.py

503 passed in 0.75–0.91 s
```

Coverage (`coverage.py` 7.6.9, same suite, omit not applied to kernel files):

| Module class | Cover | Notes |
|--------------|-------|-------|
| `core/quantity.py` | 82% | Affine arithmetic untested — the S1 hole |
| `core/dimension.py` | 93% | |
| `core/unit.py` | 85% | |
| `core/validation.py` | 90% | γ = 1 untested |
| `core/serialization.py` / `hashing.py` | 82% / 100% | |
| `core/settings.py`, `config_v0_1_1.py` | 0% | out of CORE-001..004 compute freeze |
| `physics/heat_transfer/bartz.py` | 98% | identity tests, not literature h |
| `physics/solid_mechanics/fracture.py` | **0%** | |
| `physics/compressible_flow/losses.py` | **0%** | |
| `physics/fluids/{hydrogen,methane,nitrogen,rp1,density,viscosity}.py` | 0% | thin wrappers / unused routers |
| New physics + core kernel (handoff omit cache/propellants/config) | **81%** line | line coverage ≠ scientific coverage |

Conservation tests check p/ρ identities and elemental mole counts — useful, but Rankine–Hugoniot “conservation” is the same closed form, not an independent residual.

---

## 20. Reference benchmark assessment

| Reference | Case | Inputs | Expected | COSMOS | Rel. deviation | Tolerance basis | Acceptance |
|-----------|------|--------|----------|--------|----------------|-----------------|------------|
| Anderson identities | γ=1.4, M=2 isentropic / NS | — | table/identities above | match to 0 | algebraic | **Accept** (analytical verification) |
| GRI-Mech 3.0 + NIST Cp scale | O2 NASA7, 300 K | GRI low-T a1..a5 | ~29.38 J/(mol·K) | 29.388 | 2.7×10⁻⁴ | coefficient transcription + Cp scale | **Accept** as software/reference check, **not** CEA validation |
| Bartz 1957 / SP-125 | SI Nu origin | D=0.04, μ,k,Cp,pc,c* as in test | Nu identity | identity | same equations | **Reject** as Bartz validation |
| NIST WebBook | LOX NBP density 1141 kg/m³ | cited | untested here | catalog literal | none | **Not demonstrated** |
| Incropera App. A | 304 / copper k, ρ at 300 K | catalog | untested vs book | catalog literal | none | **Not demonstrated** |
| Experimental heat flux / engines | — | — | — | — | — | **Not claimed; not done** |

Error types: Anderson deviations are numerical (zero here). Bartz curvature omission is **model-form error**. Fluid NIST literals are **unverified transcription risk**.

---

## 21. Findings by severity

### S0 — none

Peng–Robinson is fail-closed. No silent cubic EOS. No pickle RCE on the compute path. No physics↔engineering import cycle.

### S1 (1)

See freeze-blockers file: **CORE-002-AFFINE-001**.

### S2 (12)

CORE-002-DUAL-UNIT-001, CORE-003-GAMMA-001, CORE-003-PROPULSION-001, PHYS-002-FAILOPEN-001, PHYS-002-NIST-001, PHYS-003-DUAL-001, PHYS-004-NUM-001, PHYS-005-BARTZ-001, PHYS-005-CIRC-001, PHYS-005-KG-001, PHYS-INT-CHAIN-001, PHYS-INT-PROV-001.

Full templates: `documentation/development/core_physics_freeze_blockers.md`.

### S3 (selected)

| ID | Issue |
|----|--------|
| CORE-001-EXC-001 | `CFDError` / `GUIError` in Core |
| CORE-002-FRAC-001 | Integer exponents; `K_I` is `float` |
| CORE-004-ASSUME-001 | Assumption list order affects hashes |
| PHYS-001-VALID-001 | `evaluate_state` always VALID |
| PHYS-003-NASA7-DEPTH-001 | H/S/T_mid continuity untested |
| PHYS-004-TABLE-001 | ρ0/ρ, ν, Fanno, Rayleigh, oblique not in literature tests |
| PHYS-007-FRAC-TEST-001 | fracture.py 0% coverage |
| PHYS-007-THINWALL-001 | r/t < 10 not rejected |
| CACHE-EXC-001 | `except Exception: pass` in legacy cache |
| ENV-WORKSPACE-001 | Empty Cursor workspace vs authoritative repo |

### S4

Missing `__rsub__`, empty `core/__init__.py` exports, `dimensionless()` not in `__all__`, README test-count stale (out of this freeze but false-claim adjacent), several 0% re-export modules.

---

## 22. Freeze blockers

Must close: **CORE-002-AFFINE-001**.

Must fix **or** sign a waiver: the twelve S2 items. Waivers may not relabel simplified Bartz as Bartz 1957, fail-open LOX density as ρ(T), or the smoke chain as engine analysis.

---

## 23. Non-blocking backlog

- Register derived transport units in Core SI registry (`J/kg`, `Pa·s`, `W/(m·K)`).
- Fractional / rational dimension exponents if fracture becomes a typed API.
- Bind an approved CEA adapter **outside** physics; add CEA comparison tests then, not before.
- MMPDS / T-dependent allowables / fatigue / creep / film cooling — future, already stubbed honestly.
- Extend Anderson benchmarks; test `fracture.py`, `losses.py`.
- Relocate CFD/GUI exception types and `core/config_v0_1_1.py` in a later Core purity batch.
- Wire `ModelEvaluation`.
- Deprecate `core/units.py`.

---

## 24. Verification limitations

- No experimental data, engine tests, or live CEA executable were used.
- NIST WebBook was not re-downloaded; O2 Cp comparison uses the commonly cited 29.38 J/(mol·K) scale.
- Bartz curvature impact is an independent geometric factor, not a Huzel worked-example h.
- Coverage is line coverage of one pytest invocation, not branch coverage of all physics modules.
- Technical PDFs named in the audit prompt (Heister, Huzel, Anderson, Roark, SP-125, JHU/NASA MOC) were used as **equation-family checks**, not page-by-page certification that every coefficient in COSMOS was copied from a given edition.
- Affine, Anderson, NASA7 O2, hoop, K_I, hashes, and the chain were executed on this machine on 2026-09-01.

---

## 25. Freeze recommendation

```text
NOT READY — BLOCKING FINDINGS
```

Do not freeze CORE-002 / CORE-005 while `Quantity` can emit 646.3 K from `0 °C + 100 °C`. Do not freeze PHYS-002/003/005/INT as “scientifically verified” without S2 disposition.

After the S1 fix, a later review could become **FREEZE READY WITH FORMAL WAIVERS** if the remaining S2 items are either fixed or explicitly waived as:

- Kelvin-only arithmetic policy (if affine ops are forbidden),
- simplified Bartz without `(D_t/R)^{0.1}`,
- CEA interface-only,
- dual thermochemistry with a named authority,
- NUM-CONTRACT temporary bisection,
- INT-001 as smoke-only,
- fluids as reference-point records with fail-closed default.

Until then, the computational foundation is **promising and largely honest**, not **trustworthy enough to freeze**.

---

## Required summary table

| Area | Status | Critical findings | Freeze impact |
|------|--------|-------------------|---------------|
| CORE-001 | **PASS** | S3 exception-name leakage | None if Core purity is backlog |
| CORE-002 | **FAIL** | S1 affine arithmetic; S2 dual units / √L | **Blocks freeze** |
| CORE-003 | **FAIL** | S2 γ=1; propulsion validators | Disposition required |
| CORE-004 | **PASS** | S3 taxonomy / assumption order | None |
| CORE-005 | **FAIL** | S1 undetected by 153 passing tests | **Blocks freeze** |
| PHYS-001 | **PASS** | S3 validity metadata | Ideal-gas scope only |
| PHYS-002 | **FAIL** | S2 fail-open records; no NIST test | **Blocks fluids freeze** |
| PHYS-003 | **FAIL** | S2 dual API; CEA unbound (scope) | **Blocks unless interface-only waiver** |
| PHYS-004 | **PASS** | S2 numerics port; S3 table gaps | Waiver for bisection |
| PHYS-005 | **FAIL** | S2 incomplete Bartz; circular test; KG split | **Blocks Bartz freeze** |
| PHYS-006 | **PASS** | S3 no MMPDS (honest) | Property lookup only |
| PHYS-007 | **PASS** | S3 untested K_I; untyped √m | Constitutive scope only |
| INT-001 | **FAIL** | S2 inconsistent chain; unused envelope | **Blocks “scientific chain” freeze** |

```text
Total findings: 28 recorded (1 S1 + 12 S2 + 10 S3 + 5 S4; S0 = 0)
S0: 0
S1: 1
S2: 12
S3: 10
S4: 5

Freeze blockers: CORE-002-AFFINE-001 (S1); 12 S2 undispositioned
Open waivers: 0
Recommended next action: Fix affine Quantity arithmetic and add independent affine tests; then disposition S2 items (fix vs signed waiver) and re-run this audit’s independent cases. Point Cursor at /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1.
```
