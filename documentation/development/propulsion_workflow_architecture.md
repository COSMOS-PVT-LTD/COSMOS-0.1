# COSMOS_0.1 — Propulsion Workflow Architecture Map

**Document:** `documentation/development/propulsion_workflow_architecture.md`  
**Phase:** 1 — Architecture mapping only (no large implementation)  
**Repository:** `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`  
**Date:** 2026-09-03  
**Status:** READY FOR PHASE 2 APPROVAL  

**Frozen foundation (do not reopen unless stop condition):**

- Core + Physics freeze approved (PATH A waiver for PHYS-004 numerics port)
- Layer rule: `physics → core`; `core ─X→ physics`; `gui ─X→ physics` (use `api/`)

---

## 1. Mission statement (this milestone)

Build a **coherent propulsion calculation workflow** (computational graph + design state + honest stage status), not a set of isolated calculators.

**Not in scope for “full workflow”:** inventing missing physics (CEA execution, regen cooling, injector orifice theory, FEA, cycle power balance) merely to fill GUI screens.

---

## 2. Current architecture (as found)

```text
GUI (pywebview + local HTTP shell)
  ↓ fetch JSON
api/  (thin: auth, profile, physics_compressible adapters)
  ↓
physics/  (FROZEN PHYS-001..007)
  ↓
core/     (FROZEN quantities, units, validation, serialization)

knowledge/     — evidence / Maharshi workspace (not engine design store)
infrastructure/ — vault, audit
systems/       — ABSENT
engineering/   — ABSENT (documented in freeze tree only)
numerics/      — ABSENT (Area–Mach inverse uses waived physics numerics_port)
plugins/       — ABSENT (CEA adapter location referenced but missing)
```

| Package | On disk | Role today |
|---------|---------|------------|
| `core/` | Yes | Quantity/Unit/Dimension, validation, serialization |
| `physics/` | Yes | Ideal gas, fluids, NASA7/mixtures, CEA **interface**, compressible, Bartz, materials, thin-wall |
| `api/` | Yes (thin) | Auth + **only** Physics HTTP adapter module |
| `gui/` | Yes | Rocket Engine **suite** (independent calculators) |
| `knowledge/` | Yes | Knowledge graph / vault — **not** propulsion design persistence |
| `systems/` / `engineering/` | **No** | Spec-only in markdown |

### GUI framework

- Entry: `main.py` → `gui/application.py` → `gui/native_window.py` (pywebview) + `gui/server.py` (ThreadingHTTPServer)
- Navigation: workbench hub `/app/workbenches`; Propulsion/Physics **removed** from sidebar by design
- Propulsion UX: `/app/workbench/rocket-engine` (`gui/static/workbench/rocket-engine.html`, `propulsion-suite.js`)
- State today: cookie session + `localStorage` project **context** pill — **no** server-owned `PropulsionDesign` state
- Design system: `cosmos-tokens.css` / `cosmos-shell.css` / suite CSS

### Existing Physics HTTP surface

| Route | Adapter | Status |
|-------|---------|--------|
| `POST /api/physics/compressible/isentropic` | `evaluate_isentropic_stagnation` | Live |
| `POST /api/physics/compressible/area-mach` | `evaluate_area_mach` | Live (inverse = PATH A) |
| `POST /api/physics/heat-transfer/bartz` | `evaluate_bartz_htc` | Live |
| `POST /api/physics/structures/thin-wall` | `evaluate_thin_wall_stress` | Live |

All force `validation_status = NOT_CLAIMED`.

### Existing reusable Physics (not yet workflow-wired)

| Capability | Path | Notes |
|------------|------|-------|
| Ideal-gas state | `physics/thermodynamics/` | |
| Fluid props | `physics/fluids/` | LOX/RP-1/H2 records |
| NASA7 / mixtures | `physics/thermochemistry/` | |
| CEA contract | `cea_interface.py` | Raises if engine unbound |
| Choked / nozzle / thrust | `compressible_flow/` | `thrust`, `thrust_from_coefficient`, `station_from_area_ratio` |
| Bartz + recovery/flux | `heat_transfer/` | Film cooling = stub |
| Materials catalog | `physics/materials/` | Room-T handbook; creep/fatigue stubs |
| Thin-wall / Hooke / von Mises | `solid_mechanics/` | Not a chamber design system |
| Physics chain (test) | `tests/validation_tests/test_physics_chain.py` | Call-order reference only |

### Patterns to reuse (analogy)

- Knowledge `pipelines/orchestrator.py` — stage/artifact pipeline pattern (document domain, not propulsion math)
- `physics/model.py` `ModelIdentity` / evaluation metadata — result contract nucleus
- `core/serialization.py` — canonical JSON for save/load

---

## 3. Stage map (00–16) — what exists vs missing

| Stage | Intent | Repo reality | Phase target |
|-------|--------|--------------|--------------|
| **00** Design project | Project ID, revision, engineer, status | Missing models + persistence | Domain model + JSON/SQLite under systems |
| **01** Requirements | Thrust, altitude, Pc, O/F, ε, cycle | Missing; suite “engine-definition” planned | Domain + validation (no invent) |
| **02** Propellants | Ox/fuel/MR/T/P/phase | Physics registry; no workflow bind | Bind registry via systems + API |
| **03** Cycle | PF / GG / SC / expander | **Not in frozen Physics** | Interface + `NOT_IMPLEMENTED` |
| **04** Operating point | Pc, Tc, ṁ, ambient + provenance | Missing type | Domain + provenance |
| **05** Thermochemistry | Equilibrium / CEA / γ,Tc,MW,c* | NASA7/mixtures; CEA **unbound** | Internal thermo where available; CEA = honest unavailable |
| **06** Mass flow / performance | ṁ, c*, Cf, Isp, thrust | Physics primitives; no layer | Systems performance wrapping Physics |
| **07** Injector | Type, ΔP, elements, Cd | Missing calculations | Schema + `NOT_IMPLEMENTED` calcs |
| **08** Chamber | L*, Vc, Dc, contraction, At | Missing sizing layer | Implement only if derived from existing Physics + geometry defs |
| **09** Thermal | Bartz, flux, Tw | Bartz live; no full wall chain | Wire Bartz into graph; rest honest |
| **10** Cooling | Regen / film / ablative | Film stub; no regen | Boundary + `NOT_IMPLEMENTED` |
| **11** Nozzle | A/A*, Me, pe, ue, Cf | Flow live; MOC contour deferred | Wire compressible into graph |
| **12** Structure | Hoop, FoS, thermal stress | Thin-wall live | Wire + FoS only if model exists |
| **13** Materials | Part → material assignment | Catalog only | Selection object + domain checks |
| **14** Performance summary | Consolidated outputs | Missing aggregator | Aggregate calculated/assumed/unavailable |
| **15** Consistency | Continuity / validity | Local Physics checks only | Systems consistency stage |
| **16** Design review | Full provenance package | Missing | Assemble from graph artifacts |

**GUI suite today:** stages behave as **isolated calculators** (no shared design state, no invalidation). That must be replaced by workflow clients of a single design state.

---

## 4. Proposed integration boundary

```text
GUI (Rocket Engine suite — stage pages)
        ↓  HTTP only
api/workflow/  (or api/propulsion_*)   ← request validation, auth, DTO
        ↓
systems/       ← NEW orchestration + design objects + graph + invalidation
        ↓
physics/       ← FROZEN models (called only from systems/api adapters)
        ↓
core/          ← FROZEN

Optional later:
plugins/cea/   ← ThermochemistryEngine implementation (outside physics)
```

### Dependency rules (enforced by architecture tests)

| Allowed | Forbidden |
|---------|-----------|
| `systems → physics → core` | `core → physics` |
| `api → systems` / `api → physics` (thin adapters) | `gui → physics` / `gui → systems` internals |
| `gui → api` HTTP | Equations / unit conversion in JS |
| `systems → core` for Quantity | Duplicate SI conversion in GUI |

### Package naming recommendation

Prefer **`systems/`** for this milestone (mission language: propulsion systems; early architecture docs).  
Alternative **`engineering/`** matches freeze Part 6 tree — equivalent if named consistently.

**Do not** put orchestration inside `physics/` or `gui/`.

### Suggested `systems/` skeleton (Phase 2+)

```text
systems/
  projects/           # stage 00
  requirements/       # 01
  propellants/        # 02
  cycle/              # 03 — NOT_IMPLEMENTED stubs
  operating_point/    # 04
  thermochemistry/    # 05 — bind ThermochemistryEngine when present
  performance/        # 06, 14
  injector/           # 07
  chamber/            # 08
  thermal/            # 09
  cooling/            # 10
  nozzle/             # 11
  structure/          # 12
  materials/          # 13
  consistency/        # 15
  review/             # 16
  workflow/           # graph, invalidation, run orchestration
  persistence/        # design records (separate from knowledge vault)
  contracts/          # CalculationResult-like envelope
```

---

## 5. Dependency graph (target)

```text
Requirements
     ↓
Propellant Definition
     ↓
Operating Point  ←── Cycle (optional / NOT_IMPLEMENTED does not block OP)
     ↓
Thermochemistry
     ↓
Mass Flow / Performance primitives
     ↓
Injector (schema; calc if available)
     ↓
Chamber
   ↙   ↘
Thermal  Structure ←── Materials
   ↓       ↓
Cooling   (validity)
   ↘       ↙
      Nozzle
         ↓
  Performance summary
         ↓
 Consistency check
         ↓
   Design Review
```

Invalidation: change to `Pc` / O/F / propellant marks dependent nodes **STALE**; preserve prior result as historical revision; GUI must not show stale as current.

Node status enum (proposed): `NOT_CALCULATED | QUEUED | RUNNING | CURRENT | STALE | FAILED | NOT_IMPLEMENTED | OUT_OF_RANGE`.

---

## 6. Data model (conceptual — Phase 2)

Do **not** invent duplicates of Physics result types; wrap them.

| Object | Purpose |
|--------|---------|
| `PropulsionDesign` | Root: id, name, revision, engineer, software_version, status |
| `DesignRequirements` | Stage 01 fields; optional marked optional |
| `PropellantConfiguration` | Ox/fuel/MR/state refs into Physics registry IDs |
| `CycleConfiguration` | Cycle class + `implementation_status` |
| `OperatingPoint` | Pc, ambient, flows, temperatures + provenance |
| Subsystem designs | Injector / Chamber / Cooling / Nozzle / Materials |
| `StageResult` / `CalculationResult` | Envelope: model_id, version, inputs, outputs, assumptions, warnings, validity, verification, validation, provenance |
| `DesignReview` | Consolidated package for stage 16 |
| `WorkflowGraph` | Nodes + edges + dirty set |

Internal SI only; GUI display units via Core conversion **on the server/API**, not in JS.

---

## 7. GUI integration plan (preserve shell)

**Do not rewrite the GUI.** Extend Rocket Engine suite:

1. Stage nav = suite modules aligned to stages 00–16 (or grouped)
2. Single design context: `design_id` in URL or session; all stages hit workflow API
3. Each stage UI shows: INPUTS / MODEL / ASSUMPTIONS / CALCULATE / RESULTS / WARNINGS / VALIDITY / V&V
4. Drive catalog from server (`GET /api/workbenches/rocket-engine/suite` or workflow stage registry) to kill JS↔Python drift
5. Keep Maharshi FAB / shell / tokens
6. Projects: evolve Project modal → real `PropulsionDesign` persist; avoid knowledge vault overload

---

## 8. Persistence

| Existing | Use for designs? |
|----------|------------------|
| Knowledge SQLite / vault | **No** (different domain) |
| Audit SQLite | Audit only |
| `localStorage` project pill | Context label only |

**Proposed:** `systems/persistence/` → design JSON documents under app data root (e.g. `cosmos_app_data/designs/`) and/or dedicated SQLite — using `core.serialization` for canonical records. Export report formats only if existing export infrastructure supports them (architect hooks; implement minimally).

---

## 9. Stop conditions (active)

| Condition | Status | Action before proceeding |
|-----------|--------|--------------------------|
| No `systems/`/`engineering/` package | **Active** | Create new package (Phase 2) — architectural addition, not freeze reopen |
| CEA unbound | **Active** | Stage 05 must report unavailable / interface-only until plugin exists |
| Cycle physics missing | **Active** | Stage 03 = `NOT_IMPLEMENTED` |
| Injector / regen / MOC contour missing | **Active** | Schema + honest status; no fake equations |
| Design persistence missing | **Active** | New store under systems (not knowledge) |
| PHYS-004 PATH A | **Closed** | Do **not** reopen numerics / demand Numerics v2 |
| Core/Physics freeze | **Closed** | Prefer adapters + systems; do not rewrite frozen models for GUI |

---

## 10. Implementation plan (phases — unchanged directive)

| Phase | Deliverable | Gate |
|-------|-------------|------|
| **1** | This document | ✅ Complete when approved |
| **2** | Domain model + result contract + tests | Architecture tests green; no GUI equations |
| **3** | Orchestrator: Requirements → OP → Thermo → Performance | Deterministic integration tests; CEA honest |
| **4** | Subsystems: injector/chamber/thermal/cooling/nozzle/structure/materials | Only wire existing Physics |
| **5** | GUI vertical slice (one E2E path) | GUI → api → systems → physics → result |
| **6** | Remaining stage pages on shared state | Invalidation visible |
| **7** | Full test matrix | Core/Physics regression still green |
| **8** | `propulsion_workflow_integration_001.md` baseline | Document limitations |

---

## 11. Recommended first executable vertical slice (Phase 3–5)

Honest path using **existing verified Physics only**:

```text
Design + Requirements (manual SI inputs)
  → Propellant IDs from registry (no invented props)
  → Operating point (Pc, ambient, assumed/derived γ,T if thermo unavailable)
  → Thermochemistry: NASA7/mixture where possible; else NOT_IMPLEMENTED for CEA
  → Nozzle: isentropic + area–Mach + thrust_relations (Physics)
  → Thermal station: Bartz
  → Structure: thin-wall
  → Performance summary + Design Review envelope
  → Consistency: unit/model validity flags
```

Injector, cycle, regen cooling, MOC contour remain **NOT_IMPLEMENTED** nodes in the same graph.

---

## 12. Testing strategy (from Phase 2 onward)

- Unit: domain validation, graph edges, invalidation, result envelope
- Integration: systems→physics; api→systems; GUI boundary (no physics imports / no Anderson identities in JS)
- Regression: existing Core + Physics suites must remain green
- Architecture: import-graph tests for forbidden edges
- Honesty: assert CEA/cycle/injector stages emit `NOT_IMPLEMENTED` when unbound

---

## 13. Explicit non-claims

This workflow will **not** claim: certified design, flight readiness, hot-fire validation, MMPDS/ASME certification, ANSYS/NASTRAN/OpenFOAM equivalence, or CEA validation — unless independently demonstrated later.

---

## 14. Phase 1 decision needed before Phase 2

1. **Package name:** `systems/` (recommended) vs `engineering/` (freeze-doc name)?
2. **Approve Phase 1 map** → proceed to Phase 2 domain model only?

No Phase 2+ code until these are confirmed.
