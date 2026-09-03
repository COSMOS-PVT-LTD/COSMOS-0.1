# Propulsion Workflow Integration Baseline 001

**Document:** `documentation/development/propulsion_workflow_integration_001.md`  
**Date:** 2026-09-03  
**Phases covered:** 2–6 (foundation → summary/consistency/review/export)

## Architecture

```text
GUI (Rocket Engine suite)
  → api/propulsion_workflow.py + /api/propulsion/designs/*
    → systems/ (design state, graph, stages, orchestrator, export)
      → physics/ (FROZEN)
        → core/ (FROZEN)
```

## Implemented stages

| Stage | Implementation |
|-------|----------------|
| Design project / persistence | JSON `DesignStore` |
| Requirements | Capture |
| Propellants | Registry (`candidate_v1`) |
| Cycle | `NOT_IMPLEMENTED` |
| Operating point | Quantities + assumptions |
| Thermochemistry | Assumed state / CEA interface fail-closed |
| Performance | Choked + nozzle_1d + thrust |
| Injector | `NOT_IMPLEMENTED` |
| Chamber | L* geometry |
| Thermal | Bartz |
| Cooling | `NOT_IMPLEMENTED` |
| Materials | Catalog |
| Structure | Thin-wall |
| Nozzle (standalone) | Isentropic (Phase 2) |
| Performance summary | Aggregate CURRENT outputs (Phase 6) |
| Consistency | Dependency / MR / hoop checks (Phase 6) |
| Design review | Provenance package (Phase 6) |
| Export | `cosmos.propulsion_design_package` JSON |

## GUI

Module **Workflow Analysis (E2E)** runs Phase 3→6, shows the stage board, and exports the design package.

## Tests

- `tests/unit_tests/systems_layer/`
- `tests/integration_tests/systems_layer/test_phase3_chain.py`
- `tests/integration_tests/systems_layer/test_phase4_chain.py`
- `tests/integration_tests/systems_layer/test_phase6_chain.py`

## Known limitations

- No CEA execution without external engine
- Assumed γ/Tc/MW required for performance without CEA
- Injector / regen cooling / cycle / MOC contour unavailable
- `validation_status = NOT_CLAIMED` throughout
- Not flight-certified design software

## Future

Phase 7–8: per-stage shared-state pages for remaining suite modules, deeper consistency physics, and optional CAD/export bridges — without inventing missing Physics.
