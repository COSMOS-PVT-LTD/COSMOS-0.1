# COSMOS_0.1 — Propulsion Workflow Phase 3

**Status:** Backend chain implemented  
**Date:** 2026-09-03

## Chain

```text
Requirements → Propellants → Operating Point → Thermochemistry → Performance
```

Orchestrator: `systems/workflow/orchestrator.py` (`run_phase3_chain`)  
API: `POST /api/propulsion/designs/{id}/run/phase3`

## Stage honesty

| Stage | Behavior |
|-------|----------|
| Requirements | Captures fields; does not invent values |
| Propellants | Resolves IDs via `propellants_master_candidate_v1.json` |
| Operating Point | Core Quantities; assumed γ/Tc/MW flagged |
| Thermochemistry | CEA only if engine bound; else assumed state or `NOT_IMPLEMENTED` |
| Performance | Choked ṁ + nozzle station + thrust (Physics) when inputs exist |

## Non-claims

- No CEA execution without external `ThermochemistryEngine`
- Performance is ideal 1D — `validation = NOT_CLAIMED`
- Not a complete rocket design system

## Phase 4 next

Injector / chamber / thermal / cooling / structure / materials wiring where Physics exists.
