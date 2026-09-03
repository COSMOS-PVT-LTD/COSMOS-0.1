# COSMOS_0.1 — Propulsion Workflow Phase 2

**Document:** `documentation/development/propulsion_workflow_phase2.md`  
**Directive:** `COSMOS-0.1-PROPULSION-WORKFLOW-PHASE-2-001`  
**Date:** 2026-09-03  
**Status:** Foundation complete (not a full propulsion analysis system)

---

## What Phase 2 delivered

New package **`systems/`** — orchestration and design state above frozen Physics.

```text
GUI ──HTTP──► api/propulsion_workflow.py + gui/server routes
                    │
                    ▼
                 systems/
                    │
                    ▼
                 physics/  (FROZEN)
                    │
                    ▼
                 core/     (FROZEN)
```

### Domain objects

| Object | Location |
|--------|----------|
| `PropulsionDesign` | `systems/projects/models.py` |
| `DesignRequirements` | `systems/requirements/models.py` |
| `PropellantConfiguration` | `systems/propellants/models.py` |
| `CycleConfiguration` | `systems/cycle/models.py` (all cycles `NOT_IMPLEMENTED`) |
| `OperatingPoint` | `systems/operating_point/models.py` (Core `Quantity`) |
| `CalculationResult` + Validity / Verification / Validation / Provenance | `systems/contracts/results.py` |
| `WorkflowGraph` / `WorkflowState` | `systems/workflow/` |
| `DesignStore` | `systems/persistence/design_store.py` |

### Result status (authoritative)

`NOT_CALCULATED | QUEUED | RUNNING | CURRENT | STALE | FAILED | NOT_IMPLEMENTED | OUT_OF_RANGE`

Only **`CURRENT`** may be displayed as the active answer (`is_current_displayable`).

### Workflow stages 00–16

Registered in `build_default_propulsion_graph()` with explicit dependencies and implementation status.

### Invalidation

`record_input_change` / `invalidate_from_stage` mark dependent results **STALE** without deleting them (history retained).

### Persistence

JSON files under application root `propulsion_designs/` via `DesignStore` — **not** knowledge vault / audit / localStorage.

### First Physics wire-through

`systems/calculations/isentropic.py` → `PHYS-004.isentropic.stagnation`

Path: API → Systems → Physics → Core → `CalculationResult`

HTTP (authenticated):

- `POST /api/propulsion/designs`
- `GET /api/propulsion/designs/{id}`
- `GET /api/propulsion/designs/{id}/workflow`
- `POST /api/propulsion/designs/{id}/requirements`
- `POST /api/propulsion/designs/{id}/calculate/isentropic`

---

## Implemented vs unavailable

| Capability | Status |
|------------|--------|
| Design create/save/load | Implemented |
| Requirements / propellants / OP models | Implemented (data) |
| Workflow graph + invalidation | Implemented |
| Isentropic via Systems | Implemented |
| Cycle power balance | `NOT_IMPLEMENTED` |
| CEA execution | `NOT_IMPLEMENTED` |
| Injector / chamber / cooling / MOC | `NOT_IMPLEMENTED` |
| Full GUI workflow pages on shared state | Deferred to Phase 5–6 |

---

## Tests

- `tests/unit_tests/systems_layer/` — contracts, domain, workflow, persistence, architecture
- `tests/unit_tests/api/test_propulsion_workflow.py`
- `tests/integration_tests/systems_layer/test_systems_physics_isentropic.py`

(Directory must not be named `systems` — that would shadow the package.)

Existing Core + Physics regression suites must remain green (unchanged foundation).

---

## Definition of Done

See `documentation/development/propulsion_workflow_phase2_dod.md` — all Phase 2 gate items **PASS**.

Master directive archived at:

`documentation/directives/COSMOS_0.1_PROPULSION_WORKFLOW_PHASE_2_MASTER_IMPLEMENTATION_DIRECTIVE.md`

---

## Known limitations

- Independent Physics calculator routes still exist alongside shared design-state APIs.
- CEA / cycle power balance / injector / regen-film / MOC remain unavailable (`NOT_IMPLEMENTED` or partial).
- No experimental validation claimed (`validation = NOT_CLAIMED`).
- PHYS-004 PATH A waiver unchanged.

---

## Later phases (already landed in tree)

```text
Phase 3 — Requirements → Propellants → OP → Thermochemistry → Performance
Phase 4 — Chamber / Thermal / Materials / Structure wiring
Phase 5 — GUI Workflow Analysis (E2E) vertical slice
```
