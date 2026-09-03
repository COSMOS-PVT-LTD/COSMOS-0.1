# PHYSICS-FOUNDATION-HANDOFF

Status: PHYS-001 through PHYS-007 foundation delivered  
Layer: `physics/`  
Date: 2026-09-01  
Software version: COSMOS 0.1.0  
Physics schema: 0.1.0

This document is the Physics Foundation Agent handoff for CORE-PHYS-INT-001.
It does **not** claim ANSYS/SIMULIA/OpenFOAM/NASTRAN/NASA equivalence,
certification, official validation, or affiliation.

Evidence levels used below:

| Level | Meaning |
|-------|---------|
| Software verification | Typed APIs, units, exceptions, tests of the implementation |
| Analytical verification | Identities, limiting cases, independent algebraic checks |
| Reference validation | Comparison to published tables/coefficients (Anderson, NIST, GRI-Mech, Incropera) |
| Experimental validation | **Not demonstrated in this batch** |

---

## 1. Implemented models

Frozen architecture packages delivered (PHYS-001..007 only):

| Batch | Package | Status |
|-------|---------|--------|
| PHYS-001 | `physics/thermodynamics/` | Executable ideal-gas / first-second law / potentials; real-gas and saturation tables are interfaces |
| PHYS-002 | `physics/fluids/` | Sourced records + Sutherland + dimensionless numbers |
| PHYS-003 | `physics/thermochemistry/` | Species, NASA7, mixtures, reactions, CEA **interface**, Wilke viscosity; existing `propellants.py` / `cache.py` retained |
| PHYS-004 | `physics/compressible_flow/` | Closed-form Anderson relations; MOC physics only (no marching) |
| PHYS-005 | `physics/heat_transfer/` | Fourier/Newton/radiation/resistance/lumped/Bartz SI Nusselt form |
| PHYS-006 | `physics/materials/` | Temperature-windowed catalog; creep/fatigue not invented |
| PHYS-007 | `physics/solid_mechanics/` | Hooke, von Mises, thin-wall membrane, Euler, thermal stress |

Not in this batch (frozen tree, out of PHYS-001..007): `cryogenics/`, `combustion/`, `transport/`, `turbulence/`, `dynamics/`, `cycle/`, `cfd/`.

Shared infrastructure:

- `physics/model.py` — `ModelIdentity` / `ModelEvaluation`
- `physics/validity.py` — `VALID`, `OUT_OF_RANGE`, `EXTRAPOLATED`, `INSUFFICIENT_DATA`, `INVALID_INPUT`, `SINGULAR`, `DEFERRED`
- `physics/exceptions.py` — `CosmosError` subclasses
- `physics/si.py`, `physics/quantities.py` — Core `Quantity`/`Unit`/`Dimension` consumption
- `physics/contracts/` — CORE-CONTRACT-ISSUE, NUM-CONTRACT-ISSUE, numerics port

---

## 2. Public APIs

Dimensional public arguments are Core `Quantity`. Dimensionless arguments may be `float` or dimensionless `Quantity`.

Principal entry points:

```text
physics.thermodynamics.ideal_gas.evaluate_state
physics.thermodynamics.ideal_gas.{density,pressure,speed_of_sound,specific_enthalpy,...}
physics.fluids.evaluate_record / evaluate_sutherland / reynolds_number / prandtl_number
physics.thermochemistry.get_species / evaluate_nasa7 / from_mole_fractions / run_thermochemistry
physics.compressible_flow.{area_ratio, evaluate_normal_shock, station_from_area_ratio, thrust, ...}
physics.heat_transfer.bartz_heat_transfer_coefficient / plane_wall_heat_rate / ...
physics.materials.get_material
physics.solid_mechanics.{von_mises, cylinder, uniaxial_stress, ...}
```

Existing APIs preserved:

```text
physics.thermochemistry.propellants
physics.thermochemistry.cache
```

---

## 3. Equations / model families

| Family | Governing relations (compact) |
|--------|-------------------------------|
| Ideal gas | `p = ρ R T`, `R = R_univ/M`, `Cp−Cv=R`, `a=√(γRT)` |
| Calorically perfect | `h=Cp T` (datum 0 K unless specified), `Δs = Cp ln(T2/T1) − R ln(p2/p1)` |
| First/second law | `ΔU=Q−W`; `σ=ΔS−Q/T` |
| NASA7 | `Cp/R, H/RT, S/R` standard polynomials |
| Mixture | mole/mass conversion; reject invalid sums unless `normalize=True` (reported) |
| Isentropic | `T0/T=1+((γ−1)/2)M²`, `p0/p=(T0/T)^{γ/(γ−1)}` |
| Area–Mach | Anderson A/A* ; inverse via numerics port |
| Normal/oblique shock, P–M, Fanno, Rayleigh | Anderson closed forms |
| Thrust | `F=ṁVe+(pe−pa)Ae`; ideal `Cf` |
| Bartz | `Nu=0.026 Re^{0.8} Pr^{0.4}` (SI Nusselt origin) + σ |
| Thin-wall | `σ_h=pr/t`, `σ_l=pr/(2t)` |
| Hooke / von Mises / Euler | `σ=Eε`; VM; `Pcr=π²EI/(KL)²` |

---

## 4. Source references (design basis, not reproduced)

- CODATA 2022 via `core.constants` (`R_univ`, `σ_SB`, `g0`, standard atmosphere)
- Cengel & Boles; Moran & Shapiro — thermodynamic identities
- Anderson, *Modern Compressible Flow* — gasdynamics
- Sutton & Biblarz; Huzel & Huang, NASA SP-125 — thrust / Bartz context
- Bartz 1957; Incropera et al. — heat transfer / Nu–Re–Pr origin
- NASA TM-4513 / NASA RP-1311 — NASA polynomial form
- GRI-Mech 3.0 thermodynamic database — NASA7 coefficients for N2, O2, H2, H2O, CO2, CO, CH4, AR, OH, H, O
- NIST Chemistry WebBook — cryogenic NBP densities; molar masses
- Incropera Appendix A/A.6 — water 300 K, copper/steel thermal properties
- White, *Viscous Fluid Flow* — Sutherland constants
- Wilke, J. Chem. Phys. 18, 517 (1950) — mixture viscosity
- Shigley; Roark — elasticity, thin-wall, Euler (physics relations, not design codes)
- Johns Hopkins / NASA MOC nozzle reports — **future numerical MOC**, not executed here

---

## 5. Validity ranges (representative)

- Ideal gas / shocks / isentropic: `T>0`, `p>0`, `M` as required, `1<γ≤3`
- NASA7: per-species `Tmin..Tmax` (N2 GRI starts at 300 K)
- Sutherland air: ~170–1900 K; other gases as recorded
- Liquid NBP densities: ±1 K around NBP, ~1 atm
- Water Incropera table: 299–301 K
- Material catalog: ~290–310 K (room-temperature handbook window)
- Bartz: software flags `Re<1e4` as `OUT_OF_RANGE`
- Lumped capacitance: `Bi<0.1`
- Thin-wall: `r/t` reported; assumption typically `r/t≥10`

No silent clamp. Extrapolation is explicit (`allow_extrapolation=True` → `EXTRAPOLATED`).

---

## 6. Assumptions (global)

- Internal SI; Core `Quantity` at the public boundary
- Calorically perfect gas unless NASA7 is used
- Physics does not know “engines”, CAD, GUI, or design codes
- External CEA is the thermochemical **engine**; physics owns the normalized contract
- Empirical correlations are named (Bartz, Sutherland, Wilke), not hidden
- Typical handbook material values are **not** certified allowables

---

## 7. Tests

| Suite | Location | Role |
|-------|----------|------|
| Unit | `tests/unit_tests/physics/` | API, invalid input, limits, dimensions |
| Validation | `tests/validation_tests/` | conservation identities + PHYS chain |
| Benchmark | `tests/benchmark_tests/` | Anderson M=2 tables; NASA7 Cp; Bartz Nu origin |
| Regression | `tests/regression_tests/` | locked isentropic/shock/STP density values |
| Legacy | `tests/unit_tests/test_propellants.py`, `test_cache.py` | unchanged, still passing |

Latest run: **340 passed** (physics suites + existing propellant/cache tests).

### Benchmark results (analytical / literature)

| Case | Expected | COSMOS | Status |
|------|----------|--------|--------|
| Anderson γ=1.4 M=2, T0/T | 1.8 | 1.8 | pass (exact) |
| Anderson γ=1.4 M=2, p0/p | 7.82445 | 7.824449 | pass (rel 1e-4) |
| Anderson γ=1.4 M=2, A/A* | 1.68750 | 1.68750 | pass |
| Anderson NS M=2, M2 | 0.57735 | 0.57735 | pass |
| Anderson NS M=2, p2/p1 | 4.5 | 4.5 | pass |
| NASA7 O2 Cp(300 K) vs NIST ~29.4 J/mol-K | ±2% | within | pass (reference, not experiment) |
| Bartz h reconstructed from Nu·k/D·σ | identity | identity | pass (software/analytical) |

Bartz is **not** experimentally validated against a NASA heat-flux dataset in this batch.

---

## 8. Regression results

Locked values in `tests/regression_tests/test_physics_foundation.py`:

- `p0/p(M=2,γ=1.4) = 7.824449066867263`
- `A/A*(M=2,γ=1.4) = 1.6875`
- Normal-shock M2(M=2,γ=1.4) and p2/p1=4.5
- Dry-air density at 273.15 K, 101325 Pa ≈ 1.292 kg/m³ (1%)

Do not change these without scientific justification.

---

## 9. Known limitations

1. No cubic EOS coefficients (Peng–Robinson not executed).
2. No saturation tables except water NBP definition and sourced NBP liquid densities.
3. NASA CEA is **not** executed; `run_thermochemistry` requires an external `ThermochemistryEngine`.
4. MOC contour generation is deferred to numerics (NUM-CONTRACT-ISSUE).
5. Film cooling, Norton creep, S–N fatigue: interfaces only.
6. RP-1 density is typical, blend-dependent.
7. Material allowables are typical handbook values, not MMPDS.
8. Core `Dimension` has integer exponents only; `K_I` returns `float` [Pa √m].
9. Bartz uses the SI Nusselt origin, **not** the English-unit dimensional 0.026 package.
10. Physics does not import `PhysicsKnowledgeGateway` on the compute path; models carry source strings. Live knowledge lookup remains a controlled future wiring.

---

## 10. Unresolved scientific questions (OPEN SCIENTIFIC ISSUE)

1. Ingest NIST/NASA critical constants for cubic EOS.
2. Ortho/para hydrogen for LH2 thermophysical detail.
3. RP-1 assay-specific density and CEA surrogate formula.
4. Approved film-cooling correlation dataset (NASA injector criteria).
5. MMPDS / NASA temperature-dependent allowables and fatigue/creep constants.
6. Half-integer dimensions in Core for fracture toughness units.
7. Bind an approved CEA/RocketCEA adapter without leaking engine types through `physics`.
8. Whether `compressible_flow/` vs historical `gas_dynamics/` naming should be formally reconciled (frozen tree uses `compressible_flow/`; not silently renamed).

---

## 11. Core dependencies

Consumed, **not modified**:

- `core.quantity.Quantity`
- `core.unit.Unit`, `SI`
- `core.dimension.Dimension` and derived dimensions
- `core.constants`
- `core.validation`, `core.exceptions`
- `core.metadata.ObjectMetadata` / `ProvenanceRecord`
- `core.logger` (existing propellants module)

See `physics/contracts/CORE-CONTRACT-ISSUE.md`.

Physics did **not** create `PhysicsQuantity`, `ThermoQuantity`, `FluidUnit`, or `RocketDimension`.

---

## 12. Numerics dependencies

`numerics/` is absent. Physics inverses (area–Mach, Prandtl–Meyer, θ–β–M) call `physics.contracts.numerics_port.bracketed_root`, which will import `numerics.root_finding.bisection.find_root` when delivered.

See `physics/contracts/NUM-CONTRACT-ISSUE.md`.

MOC **marching** is not implemented in physics.

---

## 13. Performance observations

No hidden caches, GPU, multiprocessing, or JIT were added. Correctness was prioritized. The existing thermochemistry disk/memory cache (`cache.py`) is unchanged. Inverse Mach uses a small number of scalar bisection iterations; no performance benchmark was required for this foundation batch.

---

## 14. Architecture compliance

| Direction | Status |
|-----------|--------|
| physics → core | ALLOWED (consumed) |
| physics → numerics | ALLOWED via port; fallback documented |
| physics → knowledge | CONTROLLED: source citations only; no second solver |
| physics → GUI / AI / API / database SQL | FORBIDDEN — audited, none found |
| physics → engineering | none |

Acyclic. Physics remains the single computational authority for physical models in this batch.

Quality gates (this batch):

- pytest physics + legacy propellant/cache: **340 passed**
- ruff on new physics/tests: **pass** (legacy `cache.py`/`propellants.py` still have pre-existing E402/F401)
- mypy on new physics modules: **pass** (legacy cache/propellants and `core.logger` retain pre-existing issues; not patched — Core/legacy ownership)

---

## 15. CORE-PHYS-INT-001 readiness

The physics layer exposes a deterministic chain exercised in
`tests/validation_tests/test_physics_chain.py`:

```text
mixture (H2/O2)
  → ideal-gas chamber state (Tc, γ, M)
  → choked mass flow
  → isentropic nozzle station (M, p, T, V)
  → thrust
  → recovery temperature + Bartz h + heat flux
  → stainless yield vs thin-wall hoop stress
```

This is a **physical-model** chain. It is not GUI, API, project, or simulation orchestration, and it is not a complete rocket-engine design system.

---

## 16. What this batch is not

- Not experimental validation of a rocket engine
- Not a CEA replacement
- Not a structural design code (ASME/PED)
- Not a CFD or MOC contour generator
- Not certified material allowables
