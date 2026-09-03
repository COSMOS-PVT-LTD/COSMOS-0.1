# Rocket Engine Propulsion Design Suite (GUI)

**Status:** Active shell in Rocket Engine workbench (REV 0.5)  
**Reference tools (layout only):** [RPA — rocket-propulsion.com](https://www.rocket-propulsion.com/index.htm), RPL Engine Workbench  
**Authority:** Frozen COSMOS Physics via `api/` adapters — GUI does not embed equations.

## Placement

Propulsion design lives **inside** `/app/workbench/rocket-engine`, not as a top-level sidebar item.
Sidebar entries **Propulsion** and **Physics** were removed; open Rocket Engine from the workbench hub.

## Modules

| Module | Status | Live API |
|--------|--------|----------|
| Engine Definition | planned | — |
| Propellants & Combustion | planned | — |
| Chamber Sizing | planned | — |
| Nozzle Flow | **live** | `POST /api/physics/compressible/isentropic`, `.../area-mach` |
| Nozzle Contour | planned | — |
| Heat Transfer | **live** | `POST /api/physics/heat-transfer/bartz` |
| Injectors | planned | — |
| Structures (Thin Wall) | partial | `POST /api/physics/structures/thin-wall` |
| Cycle / Feed System | planned | — |

Catalog: `gui/workbenches/propulsion_suite.py`  
UI: `gui/static/workbench/rocket-engine.html`, `propulsion-suite.js`

## Claims

- Every live response includes `validation_status = NOT_CLAIMED`.
- This is **not** an RPA or RPL clone and does **not** claim hot-fire or CEA equivalence.
- Planned modules are honest placeholders until Physics adapters exist.

## Shell fixes bundled with this milestone

- Sidebar: constrained height + `overflow-y: auto` so long nav lists scroll.
- Maharshi FAB: `position: fixed`, higher z-index, `mix-blend-mode: normal` so the portrait remains visible.
